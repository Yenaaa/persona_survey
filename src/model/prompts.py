"""페르소나 데이터를 LLM system prompt 문자열로 변환한다."""
from ..data.persona_loader import Persona

PERSONA_SYSTEM_PROMPT_TEMPLATE = """\
당신은 아래 프로필을 가진 실제 한국인이라고 가정하고 답변합니다.
자신이 AI, 언어 모델이라는 사실을 밝히지 말고, 이 사람의 관점과 말투로 응답하세요.

[인구통계 정보]
{demographics_block}

[페르소나 서술]
{narrative_block}

이어지는 설문 문항에 이 사람의 입장에서 솔직하게 답하세요.
"""


def build_persona_system_prompt(persona: Persona) -> str:
    demographics_block = "\n".join(
        f"- {k}: {v}" for k, v in persona.demographics.items() if v is not None
    ) or "(정보 없음)"

    narrative_block = "\n".join(
        f"- {k}: {v}" for k, v in persona.narrative.items() if v
    ) or "(정보 없음)"

    return PERSONA_SYSTEM_PROMPT_TEMPLATE.format(
        demographics_block=demographics_block,
        narrative_block=narrative_block,
    )
