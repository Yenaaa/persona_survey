"""LLM 호출 레이어. .env의 LLM_PROVIDER(openai/anthropic/google/mock)로 실제 provider를 스위칭한다.

provider마다 SDK 호출 방식/구조화된 출력 방식이 다르지만, 어느 쪽을 쓰든
`run_survey()`는 항상 같은 SurveyResponse를 돌려주므로 이 파일 밖의 코드
(persona_loader, prompts, survey, main)는 전혀 건드릴 필요가 없다.

provider별 패키지는 실제로 그 provider를 쓸 때만 import한다(지연 import).
requirements.txt에서 쓰지 않는 provider의 패키지는 주석 처리해도 된다.

LLM_PROVIDER=mock으로 두면 API를 전혀 호출하지 않고 더미 응답을 돌려준다.
API 키 없이 파이프라인(페르소나 로드 -> 프롬프트 생성 -> 결과 저장)이
제대로 도는지만 먼저 확인하고 싶을 때 쓴다.
"""
from ..config import CONFIG
from ..data.survey import SURVEY_QUESTIONS, SurveyResponse, build_survey_prompt


def run_survey(persona_system_prompt: str) -> SurveyResponse:
    """하나의 페르소나 system prompt로 독립적인 새 대화를 만들어 설문을 실행한다.

    이전에 어떤 페르소나로 몇 번을 호출했든 이 함수는 항상 새 대화로
    시작하므로, 페르소나 간 대화 맥락이 섞이지 않는다(stateless).
    """
    provider = CONFIG.llm_provider
    if provider == "mock":
        return _run_survey_mock(persona_system_prompt)
    if provider == "openai":
        return _run_survey_openai(persona_system_prompt)
    if provider == "anthropic":
        return _run_survey_anthropic(persona_system_prompt)
    if provider == "google":
        return _run_survey_google(persona_system_prompt)
    raise ValueError(
        f"지원하지 않는 LLM_PROVIDER='{provider}'. 사용 가능: mock, openai, anthropic, google"
    )


def _run_survey_mock(persona_system_prompt: str) -> SurveyResponse:
    """API 호출 없이 SURVEY_QUESTIONS 형식에 맞는 더미 응답을 만든다."""
    del persona_system_prompt  # mock에서는 쓰지 않음
    answers = [
        {
            "question_id": q["id"],
            "answer": "3" if q["type"] == "likert5" else "(mock 답변)",
            "reasoning": "mock 응답입니다 (실제 LLM 호출 없음).",
        }
        for q in SURVEY_QUESTIONS
    ]
    return SurveyResponse(answers=answers)


def _run_survey_openai(persona_system_prompt: str) -> SurveyResponse:
    from openai import OpenAI

    client = OpenAI(api_key=CONFIG.openai_api_key)
    completion = client.beta.chat.completions.parse(
        model=CONFIG.model_name,
        temperature=CONFIG.temperature,
        messages=[
            {"role": "system", "content": persona_system_prompt},
            {"role": "user", "content": build_survey_prompt()},
        ],
        response_format=SurveyResponse,
    )
    return completion.choices[0].message.parsed


def _run_survey_anthropic(persona_system_prompt: str) -> SurveyResponse:
    from anthropic import Anthropic

    client = Anthropic(api_key=CONFIG.anthropic_api_key)
    # Claude는 OpenAI의 response_format 같은 기능이 없어서, 대신 "이 tool을
    # 반드시 호출하게" 강제해서 구조화된 출력을 흉내낸다. tool의 입력 스키마로
    # SurveyResponse의 JSON 스키마를 그대로 재사용한다.
    tool = {
        "name": "submit_survey_response",
        "description": "설문 응답을 제출한다.",
        "input_schema": SurveyResponse.model_json_schema(),
    }
    message = client.messages.create(
        model=CONFIG.model_name,
        max_tokens=2048,
        temperature=CONFIG.temperature,
        system=persona_system_prompt,
        messages=[{"role": "user", "content": build_survey_prompt()}],
        tools=[tool],
        tool_choice={"type": "tool", "name": "submit_survey_response"},
    )
    tool_use_block = next(b for b in message.content if b.type == "tool_use")
    return SurveyResponse.model_validate(tool_use_block.input)


def _run_survey_google(persona_system_prompt: str) -> SurveyResponse:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=CONFIG.google_api_key)
    response = client.models.generate_content(
        model=CONFIG.model_name,
        contents=build_survey_prompt(),
        config=types.GenerateContentConfig(
            system_instruction=persona_system_prompt,
            temperature=CONFIG.temperature,
            response_mime_type="application/json",
            response_schema=SurveyResponse,
        ),
    )
    return SurveyResponse.model_validate_json(response.text)
