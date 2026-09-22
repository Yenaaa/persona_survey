"""전역 설정. 환경변수(.env)로 값을 주입한다."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # --- LLM ---
    # mock / openai / anthropic / google 중 하나. src/model/llm_client.py가 이 값으로 분기한다.
    # mock은 API를 전혀 호출하지 않고 더미 응답을 돌려준다 (API 키 없이 파이프라인만 테스트할 때).
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    model_name: str = os.getenv("MODEL_NAME", "gpt-4o-mini")
    temperature: float = float(os.getenv("TEMPERATURE", "1.0"))

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")

    # --- Persona dataset ---
    persona_dataset_name: str = os.getenv("PERSONA_DATASET_NAME", "nvidia/Nemotron-Personas-Korea")
    persona_dataset_split: str = os.getenv("PERSONA_DATASET_SPLIT", "train")

    # 페르소나 프롬프트에 어떤 필드를 쓸지 고르는 프리셋 이름.
    # 실제 프리셋 정의는 src/data/persona_loader.py의 FIELD_SETS 참고.
    field_set_name: str = os.getenv("FIELD_SET", "default")

    # --- Sampling ---
    n_personas: int = int(os.getenv("N_PERSONAS", "10"))
    repeats_per_persona: int = int(os.getenv("REPEATS_PER_PERSONA", "1"))
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))

    # --- Output ---
    # 실행마다 output_dir/<run_id>/ 폴더가 자동 생성된다 (main.py의 _make_run_id 참고).
    output_dir: str = os.getenv("OUTPUT_DIR", "results")

    # 기존 실행을 이어서 하고 싶을 때, 그 실행의 run_id(예: 20260922_143000_openai_gpt-4o-mini_default)를
    # 넣으면 새 run_id를 만들지 않고 그 폴더를 그대로 이어서 쓴다. 비워두면 매번 새 run_id로 시작한다.
    resume_run_id: str = os.getenv("RESUME_RUN_ID", "")


CONFIG = Config()

