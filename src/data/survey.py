"""가상 설문지 (예시). 실제 연구 주제에 맞는 문항으로 교체해서 쓴다."""
from pydantic import BaseModel, Field

SURVEY_TITLE = "예시 설문: 제품 만족도 조사"

# 문항 정의. type은 프롬프트 문구 구성에만 쓰이는 메타데이터이며,
# 실제 응답 검증은 SurveyResponse 스키마가 담당한다.
SURVEY_QUESTIONS = [
    {
        "id": "q1",
        "text": "이 제품을 다른 사람에게 추천할 의향이 있습니까? (1=전혀 없다, 5=매우 그렇다)",
        "type": "likert5",
    },
    {
        "id": "q2",
        "text": "이 제품의 가격이 적절하다고 생각합니까? (1=전혀 그렇지 않다, 5=매우 그렇다)",
        "type": "likert5",
    },
    {
        "id": "q3",
        "text": "이 제품을 선택한 가장 큰 이유는 무엇입니까?",
        "type": "open",
    },
]


class QuestionAnswer(BaseModel):
    question_id: str
    answer: str = Field(description="Likert 문항은 1~5 숫자 문자열, 주관식은 자유 서술")
    reasoning: str = Field(description="이 응답을 고른 이유를 페르소나 관점에서 짧게 서술")


class SurveyResponse(BaseModel):
    answers: list[QuestionAnswer]


def build_survey_prompt() -> str:
    lines = [f"[{SURVEY_TITLE}]", ""]
    for q in SURVEY_QUESTIONS:
        lines.append(f"{q['id']}. {q['text']}")
    return "\n".join(lines)
