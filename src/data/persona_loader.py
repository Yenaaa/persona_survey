"""nvidia/Nemotron-Personas-Korea 데이터셋에서 페르소나를 샘플링해 로드한다."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from datasets import load_dataset

from ..config import CONFIG
from .persona_schema import validate_field_set

# 필드 조합 "프리셋". 페르소나 프롬프트에 어떤 필드를 쓸지는 여기서 이름을 붙여 정의하고,
# 실제로 어떤 프리셋을 쓸지는 .env의 FIELD_SET으로 고른다(기본값 "default").
# 새 조합을 실험하고 싶으면 기존 프리셋을 덮어쓰지 말고 이름을 새로 추가할 것 —
# 그래야 예전 프리셋과 그걸로 만든 결과가 그대로 남아 재현 가능하다.
# 필드는 persona_schema.py의 FIELD_SCHEMA에 나열된 것 중에서만 고르면 되고
# (narrative/attribute 어느 카테고리든 자유롭게 섞어서 골라도 된다), 목록에 없는
# 이름을 적으면 로드 시점에 바로 에러가 난다.
FIELD_SETS: dict[str, dict[str, list[str]]] = {
    "default": {
        "narrative": ["persona", "professional_persona", "family_persona", "hobbies_and_interests"],
        "demographic": ["sex", "age", "marital_status", "education_level", "occupation", "province", "district"],
    },
    "custom": {
        "narrative": ["persona"],
        "demographic": ["age"],
    },
}

for _name, _field_set in FIELD_SETS.items():
    validate_field_set(f"FIELD_SETS['{_name}']", _field_set)


def get_active_field_set() -> dict[str, list[str]]:
    """CONFIG.field_set_name(.env의 FIELD_SET)이 가리키는 프리셋을 반환한다."""
    try:
        return FIELD_SETS[CONFIG.field_set_name]
    except KeyError:
        raise ValueError(
            f"FIELD_SET='{CONFIG.field_set_name}'은(는) FIELD_SETS에 없는 프리셋입니다. "
            f"사용 가능한 프리셋: {sorted(FIELD_SETS)}"
        ) from None


@dataclass
class Persona:
    persona_id: str
    narrative: dict[str, Any] = field(default_factory=dict)
    demographics: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


def load_personas(n: int = CONFIG.n_personas, seed: int = CONFIG.random_seed) -> list[Persona]:
    """데이터셋에서 n개의 페르소나를 비복원 랜덤 샘플링한다.

    특정 성별/연령대/지역 비율을 맞춘 층화추출이 필요하면 이 함수를
    `ds.filter(...)`를 먼저 적용하는 식으로 바꿔 쓴다.
    """
    field_set = get_active_field_set()
    narrative_fields = field_set.get("narrative", [])
    demographic_fields = field_set.get("demographic", [])

    ds = load_dataset(CONFIG.persona_dataset_name, split=CONFIG.persona_dataset_split)
    ds = ds.shuffle(seed=seed).select(range(n))

    personas = []
    for row in ds:
        personas.append(
            Persona(
                persona_id=row["uuid"],
                narrative={k: row.get(k) for k in narrative_fields},
                demographics={k: row.get(k) for k in demographic_fields},
                raw=row,
            )
        )
    return personas
