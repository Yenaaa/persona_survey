# Persona Survey
LLM에게 페르소나를 부여하고, 그 페르소나 입장에서 설문에 응답하게 하는 실험용 스켈레톤입니다.
페르소나는 [nvidia/Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea) 데이터셋에서 샘플링하고, LLM 호출은 OpenAI / Anthropic(Claude) / Google(Gemini) 중 `.env`로 고른 provider를 사용합니다.

> 연구 주제가 정해지면 `src/data/survey.py`(설문 문항/스키마), `src/model/prompts.py`(시스템 프롬프트), `src/data/persona_loader.py`(페르소나 필드/샘플링 전략)를 바꿔서 쓰는 것을 전제로 만든 뼈대입니다.

## 구조

코드는 역할 기준으로 나뉩니다:

- **config**: `.env` 기반 설정값 (API 키, 모델명, temperature, 샘플 수 등)
- **data**: 페르소나 데이터셋 로딩, 필드 스키마/선택, 설문 문항 등 "입력 데이터" 계층
- **model**: LLM 호출과 그에 필요한 프롬프트 구성 계층

이 셋은 전부 `src/` 패키지 안에서 실행 코드 없이 순수 로직만 담당하고, 오케스트레이션(전체 파이프라인을 도는 `main()` 함수)과 실행 진입점(`if __name__ == "__main__"`)은 루트의 `main.py` 하나뿐입니다.

LLM 호출 코드가 `src/model/llm_client.py` 한 파일에만 격리되어 있어서, provider(OpenAI/Anthropic/Google)를 바꾸거나 새 provider를 추가해도 다른 파일(`persona_loader.py`, `prompts.py`, `survey.py`, `main.py`)은 건드릴 필요가 없습니다. 자세한 내용은 아래 "기타 사용법 → LLM Provider 전환" 참고.

## 코드 설치

```bash
pip install -r requirements.txt
cp .env.example .env
```

`.env`에서 `LLM_PROVIDER`(기본 `openai`)와 그에 맞는 API 키, `MODEL_NAME`을 채워넣습니다. 필요하면 `N_PERSONAS`, `TEMPERATURE` 등 다른 값도 조정합니다. 자세한 건 "기타 사용법 → LLM Provider 전환" 참고.

## 코드 실행

```bash
python main.py
```

### API 키 없이 파이프라인만 먼저 테스트하기

`.env`의 `LLM_PROVIDER=mock`으로 두면 실제 LLM API를 전혀 호출하지 않고, 페르소나 로드 → 프롬프트 생성 → (더미) 응답 → 결과 저장까지 전체 파이프라인이 잘 도는지만 확인할 수 있습니다. API 키는 필요 없지만, 페르소나 데이터셋 다운로드 자체는 여전히 huggingface에 네트워크로 접근하므로 인터넷 연결은 필요합니다.

## 워크플로우

```
설정 로드 (src/config.py)
   → 페르소나 데이터셋 로드 + N개 샘플링 (src/data/persona_loader.py)
   → 페르소나마다 반복:
        페르소나 → system prompt 변환 (src/model/prompts.py)
        새 대화(stateless)로 설문 실행 (src/model/llm_client.py, 문항은 src/data/survey.py)
        구조화된 응답 파싱 → 결과 즉시 append 저장 (main.py)
   → results/<run_id>/results.jsonl 로 결과 누적, 같은 폴더에 run_config.json도 저장
```

각 페르소나는 매번 새로운 `messages` 리스트로 호출되므로, 이전 페르소나의 응답이나 대화 맥락이 다음 페르소나에 섞이지 않습니다(stateless). `REPEATS_PER_PERSONA`를 1보다 크게 주면 동일 페르소나에 반복 측정을 걸어 LLM 응답의 변동성(stochasticity)을 볼 수 있습니다.

## 디렉토리 구조

```
project_kang/
├── main.py                     # 오케스트레이션 + 실행 진입점 (여기 하나뿐)
├── requirements.txt
├── .env.example
├── README.md
├── results/                    # 실행마다 results/<run_id>/ 폴더로 나뉘어 결과가 쌓이는 곳
└── src/                        # 패키지: 순수 로직 (실행 코드 없음)
    ├── config.py                 # .env 기반 설정
    ├── data/                      # 페르소나/설문 = "데이터" 계층
    │   ├── persona_schema.py        # 데이터셋 전체 필드 스키마(정답지) + 검증 함수
    │   ├── persona_loader.py        # 필드 선택(FIELD_SETS) + Nemotron-Personas-Korea 샘플링
    │   └── survey.py                 # (예시) 설문 문항 + 응답 스키마
    └── model/                     # LLM 호출 = "모델" 계층
        ├── llm_client.py            # provider별(OpenAI/Anthropic/Google) 구조화된 출력 호출
        └── prompts.py                # 페르소나 -> system prompt 변환
```

| 파일 | 역할 |
|---|---|
| `src/config.py` | `.env` 기반 설정 (API 키, 모델명, temperature, 샘플 수 등) |
| `src/data/persona_schema.py` | Nemotron-Personas-Korea 전체 필드 스키마(`FIELD_SCHEMA`) + 검증 함수 |
| `src/data/persona_loader.py` | 필드 조합 선택(`FIELD_SETS`) + 페르소나 샘플링 |
| `src/data/survey.py` | (예시) 설문 문항 정의 + Pydantic 응답 스키마 |
| `src/model/prompts.py` | 페르소나 데이터 → LLM system prompt 문자열 변환 |
| `src/model/llm_client.py` | provider별(OpenAI/Anthropic/Google) structured output 호출 래퍼 |
| `main.py` | 전체 루프 실행(오케스트레이션) + 결과 incremental 저장 + 실행 진입점 |

## 기타 사용법

### 결과 파일 관리

실행할 때마다 `OUTPUT_DIR`(기본 `results`) 아래에 **실행 전용 폴더**가 자동 생성됩니다:

```
results/
└── 20260922_143000_openai_gpt-4o-mini_default/
    ├── run_config.json   # 이 실행의 설정 스냅샷
    └── results.jsonl     # 이 실행의 응답들 (한 줄당 하나)
```

폴더 이름(`run_id`)은 `<타임스탬프>_<provider>_<model>_<field_set>` 형식으로 자동 생성되어, provider/model/field_set을 바꿔가며 여러 번 실행해도 결과가 서로 다른 파일에 섞이지 않습니다.

**`run_config.json`**에는 이 실행에 쓰인 설정 전체(provider, model, temperature, field_set, n_personas, repeats_per_persona, random_seed, 데이터셋 이름/split, 시작 시각)가 요약돼 있어서, 나중에 폴더만 봐도 무슨 실험이었는지 알 수 있습니다.

**`results.jsonl`**은 한 줄당 하나의 응답(JSON)이 append됩니다. 레코드 형식:

```json
{
  "persona_id": "uuid",
  "repeat_idx": 0,
  "demographics": { "sex": "...", "age": 34, "occupation": "...", "...": "..." },
  "answers": [
    { "question_id": "q1", "answer": "4", "reasoning": "..." }
  ],
  "provider": "openai",
  "model": "gpt-4o-mini",
  "temperature": 1.0,
  "field_set": "default",
  "field_set_fields": { "narrative": ["persona", "..."], "demographic": ["sex", "..."] },
  "timestamp": "2026-09-20T12:00:00+00:00"
}
```

`field_set`/`field_set_fields`가 레코드마다도 남는 이유는, `results.jsonl` 한 줄만 떼어내 다른 곳에서 봐도(예: 분석 스크립트, 다른 폴더로 복사) 어떤 조건에서 나온 응답인지 알 수 있게 하기 위함입니다. 아래 "페르소나 필드 선택" 절 참고.

#### 중단된 실행 이어하기 (resume)

API 호출 중간에 에러가 나거나 프로그램이 죽으면, 이미 성공한 응답은 이미 `results.jsonl`에 저장돼 있습니다. 처음부터 다시 돌리면 그만큼 API를 또 호출하게(=비용 낭비) 되므로, `.env`의 `RESUME_RUN_ID`에 이어서 할 `run_id`를 적으면:

```
RESUME_RUN_ID=20260922_143000_openai_gpt-4o-mini_default
```

- 새 `run_id`를 만들지 않고 그 폴더를 그대로 이어서 씁니다.
- `results.jsonl`에 이미 있는 `(persona_id, repeat_idx)` 조합은 건너뛰고, 남은 것만 호출합니다.
- 이때 `N_PERSONAS`/`RANDOM_SEED`/`FIELD_SET` 등을 원래 실행과 동일하게 유지해야 같은 페르소나 목록이 재생성되어 정확히 이어집니다 (데이터셋 샘플링이 시드 기반이라 같은 설정이면 항상 같은 페르소나가 뽑힙니다).

### 데이터셋 스키마 참고 (Nemotron-Personas-Korea)

- 식별자: `uuid`
- 서술형 페르소나: `persona`, `professional_persona`, `sports_persona`, `arts_persona`, `travel_persona`, `culinary_persona`, `family_persona`
- 속성: `cultural_background`, `skills_and_expertise`(_list), `hobbies_and_interests`(_list), `career_goals_and_ambitions`
- 인구통계/지역: `sex`, `age`, `marital_status`, `military_status`, `family_type`, `housing_type`, `education_level`, `bachelors_field`, `occupation`, `district`, `province`, `country`

이 전체 26개 필드는 `src/data/persona_schema.py`의 `FIELD_SCHEMA`에 카테고리별로 그대로 정리해뒀습니다. 이건 데이터셋 자체의 "정답지"라서, 데이터셋 스키마가 바뀌지 않는 한 거의 손댈 일이 없습니다.

### 페르소나 필드 선택 (FIELD_SETS)

실제로 페르소나 프롬프트에 쓰는 필드 조합은 `src/data/persona_loader.py`의 `FIELD_SETS`에 이름을 붙여 정의합니다:

```python
FIELD_SETS = {
    "default": {"narrative": [...], "demographic": [...]},
    "custom":  {"narrative": [...], "demographic": [...]},
}
```

`FIELD_SCHEMA`(정답지, `persona_schema.py`)와 `FIELD_SETS`(이번 연구의 선택, `persona_loader.py`)를 파일로 분리해둔 이유는 성격이 다르기 때문입니다 — 전자는 데이터셋이 바뀌지 않는 한 고정이고, 후자는 연구가 진행되며 계속 늘어납니다.

어떤 프리셋을 쓸지는 `.env`의 `FIELD_SET` 값으로 고릅니다 (기본값 `default`). `FIELD_SETS`에 없는 이름을 적거나, 프리셋 안에 `FIELD_SCHEMA`에 없는 필드를 적으면(`persona_schema.py`의 `validate_field_set()`이 검증) 실행 시점에 바로 에러가 납니다.

**새 필드 조합을 실험할 때는 기존 프리셋을 고쳐쓰지 말고 이름을 새로 추가하세요.** 필드 조합이 바뀌면 페르소나에게 주는 정보 자체가 달라지므로 사실상 다른 실험 조건이 되고, 프리셋 이름을 그대로 남겨둬야 과거 결과를 재현할 수 있습니다. 각 결과 레코드에 `field_set`(이름)과 `field_set_fields`(실제 사용된 필드 목록)가 같이 저장되므로, 나중에 결과 파일만 봐도 어떤 조합으로 만들어졌는지 알 수 있습니다.

### LLM Provider 전환

`.env`에서 `LLM_PROVIDER`를 고르고(`mock` / `openai` / `anthropic` / `google`), 그 provider의 API 키와 그 provider가 지원하는 `MODEL_NAME`을 채우면 됩니다. `mock`은 API 키 없이 더미 응답으로 파이프라인만 테스트할 때 씁니다(위 "API 키 없이 파이프라인만 먼저 테스트하기" 참고):

```
LLM_PROVIDER=anthropic
MODEL_NAME=claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-...
```

`requirements.txt`에서 실제 쓰는 provider의 패키지만 주석을 풀어 설치하면 됩니다(`openai`는 기본으로 설치돼 있고, `anthropic`/`google-genai`는 주석 처리돼 있습니다). 세 provider 모두 같은 `SurveyResponse`(Pydantic) 스키마로 구조화된 응답을 강제하도록 구현했습니다 — OpenAI는 `response_format`, Anthropic(Claude)은 강제 tool 호출, Google(Gemini)은 `response_schema`를 사용합니다. `LLM_PROVIDER`에 등록되지 않은 값을 넣으면 실행 시점에 바로 에러가 납니다.

### 커스터마이징 지점

- **설문 문항/응답 스키마**: `src/data/survey.py`의 `SURVEY_QUESTIONS`, `SurveyResponse`
- **시스템 프롬프트 문구**: `src/model/prompts.py`의 `PERSONA_SYSTEM_PROMPT_TEMPLATE`
- **페르소나 선택 필드**: `src/data/persona_loader.py`의 `FIELD_SETS`에 새 프리셋 추가 후 `.env`의 `FIELD_SET`으로 선택 — 전체 후보는 `src/data/persona_schema.py`의 `FIELD_SCHEMA` 참고
- **샘플링 전략**(층화추출 등): `src/data/persona_loader.py`의 `load_personas()`
- **LLM provider**: `.env`의 `LLM_PROVIDER`/`MODEL_NAME` — 새 provider를 추가하려면 `src/model/llm_client.py`에 `_run_survey_<provider>()` 함수만 추가
- **반복 측정 횟수 / temperature**: `.env`의 `REPEATS_PER_PERSONA`, `TEMPERATURE`

### 아직 구현하지 않은 것 (필요 시 추가)

- 비동기/병렬 호출 (`asyncio` + 동시성 제한)
- API 실패 시 재시도 로직 (예: `tenacity`)
- 토큰/비용 로깅
- 층화추출 등 정교한 샘플링
