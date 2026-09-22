"""nvidia/Nemotron-Personas-Korea 데이터셋 전체 스키마(2026-09 기준, 26 fields).

여기 있는 FIELD_SCHEMA는 데이터셋 자체가 바뀌지 않는 한 거의 바뀌지 않는
"정답지"다. 반대로 이번 연구에서 실제로 어떤 필드를 쓸지 고르는 FIELD_SETS는
persona_loader.py에 있고, 연구가 진행되며 계속 늘어난다. 그래서 둘을 분리했다.
"""
FIELD_SCHEMA: dict[str, list[str]] = {
    "id": ["uuid"],
    "narrative": [  # 서술형 페르소나 (자연어 문단)
        "persona",
        "professional_persona",
        "sports_persona",
        "arts_persona",
        "travel_persona",
        "culinary_persona",
        "family_persona",
    ],
    "attribute": [  # 속성 (스킬/취미/커리어 목표)
        "cultural_background",
        "skills_and_expertise",
        "skills_and_expertise_list",
        "hobbies_and_interests",
        "hobbies_and_interests_list",
        "career_goals_and_ambitions",
    ],
    "demographic": [  # 인구통계 / 지역
        "sex",
        "age",
        "marital_status",
        "military_status",
        "family_type",
        "housing_type",
        "education_level",
        "bachelors_field",
        "occupation",
        "district",
        "province",
        "country",
    ],
}

ALL_SCHEMA_FIELDS: set[str] = {f for fields in FIELD_SCHEMA.values() for f in fields}


def validate_field_set(name: str, field_set: dict[str, list[str]]) -> None:
    """field_set(예: FIELD_SETS["default"]) 안의 모든 필드가 FIELD_SCHEMA에 실제로
    존재하는지 검증한다. 없는 필드명(오타 등)이 있으면 바로 에러를 낸다.
    """
    for block_name, fields in field_set.items():
        unknown = set(fields) - ALL_SCHEMA_FIELDS
        if unknown:
            raise ValueError(
                f"{name}['{block_name}']에 FIELD_SCHEMA에 없는 필드가 있습니다: "
                f"{sorted(unknown)}. 철자를 확인하거나 FIELD_SCHEMA를 업데이트하세요."
            )
