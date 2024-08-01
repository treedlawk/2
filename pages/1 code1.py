import textwrap
import google.generativeai as genai
import streamlit as st
import toml
import pathlib

# secrets.toml 파일 경로
secrets_path = pathlib.Path(__file__).resolve().parent.parent / ".streamlit/secrets.toml"

# secrets.toml 파일 읽기
try:
    with open(secrets_path, "r") as f:
        secrets = toml.load(f)
except FileNotFoundError:
    raise ValueError(f"secrets.toml 파일을 찾을 수 없습니다: {secrets_path}")
except toml.TomlDecodeError:
    raise ValueError("secrets.toml 파일의 형식이 잘못되었습니다.")

# secrets.toml 파일에서 API 키 값 가져오기
api_key = secrets.get("general", {}).get("api_key")

# API 키가 제대로 로드되었는지 확인
if not api_key:
    raise ValueError("API 키가 secrets.toml 파일에서 로드되지 않았습니다.")

def to_markdown(text):
    text = text.replace('•', '*')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

# few-shot 프롬프트 구성 함수 수정
def check_endangered_species(api_key, animal_name):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 256,
        },
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
    )
    prompt = f"""
    다음 생물이 멸종 위기종인지 확인하고, 맞다면 멸종 위기 단계를 알려줘. 
    멸종 위기 단계는 IUCN 적색 목록 기준으로 "관심 필요(LC)", "준위협(NT)", "취약(VU)", "멸종 위기(EN)", "심각한 위기(CR)", "야생 절멸(EW)", "절멸(EX)" 중 하나를 사용해줘.
    만약 해당 생물에 대한 정보를 찾을 수 없다면, "멸종 위기 아님"이라고 표시해줘.

    생물: {animal_name}

    답변:
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"API 호출 실패: {e}")
        return None

# 스트림릿 앱 인터페이스 구성
st.title("멸종 위기 생물 확인")

# 사용자 입력 받기
animal_name = st.text_input("생물 이름을 입력하세요:")

if st.button("확인"):
    # API 키로 멸종 위기 여부 확인
    result = check_endangered_species(api_key, animal_name)

    # 결과 출력
    if result is not None:
        st.markdown(to_markdown(result))
    else:
        st.error("API 호출에 실패했습니다. 나중에 다시 시도해주세요.")
