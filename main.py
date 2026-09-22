"""페르소나를 하나씩 새로 부여해 가며 설문을 반복 수행하는 메인 루프.

핵심 아이디어: N개의 페르소나를 샘플링한 뒤, 각 페르소나마다
"새 시스템 프롬프트 생성 -> 새 대화로 설문 실행 -> 결과 저장"을
독립적으로 반복한다. 페르소나 간에 대화 히스토리를 공유하지 않기 때문에
이전 응답이 다음 페르소나의 답변에 영향을 주지 않는다.

결과는 실행마다 results/<run_id>/ 폴더에 따로 쌓인다(run_id는 타임스탬프
+provider+model+field_set로 자동 생성). 같은 폴더에 이번 실행의 설정을
정리한 run_config.json도 같이 저장해서, 나중에 폴더만 봐도 무슨 실험이었는지
알 수 있게 한다. .env의 RESUME_RUN_ID에 기존 run_id를 넣으면 그 폴더를 이어서
쓰고, 이미 끝난 (persona_id, repeat_idx)는 건너뛴다.
"""
import json
import os
from datetime import datetime, timezone

from src.config import CONFIG
from src.data.persona_loader import Persona, get_active_field_set, load_personas
from src.model.llm_client import run_survey
from src.model.prompts import build_persona_system_prompt


def _make_run_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model_name = CONFIG.model_name.replace("/", "-")
    return f"{timestamp}_{CONFIG.llm_provider}_{safe_model_name}_{CONFIG.field_set_name}"


def _write_manifest(run_dir: str) -> None:
    manifest = {
        "run_id": os.path.basename(run_dir),
        "provider": CONFIG.llm_provider,
        "model": CONFIG.model_name,
        "temperature": CONFIG.temperature,
        "field_set": CONFIG.field_set_name,
        "field_set_fields": get_active_field_set(),
        "n_personas": CONFIG.n_personas,
        "repeats_per_persona": CONFIG.repeats_per_persona,
        "random_seed": CONFIG.random_seed,
        "persona_dataset_name": CONFIG.persona_dataset_name,
        "persona_dataset_split": CONFIG.persona_dataset_split,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(run_dir, "run_config.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _load_done_keys(results_path: str) -> set[tuple[str, int]]:
    """results_path에 이미 있는 (persona_id, repeat_idx) 조합을 읽어온다.

    resume 시 이 조합들은 다시 호출하지 않고 건너뛴다(API 비용 낭비 방지).
    """
    done: set[tuple[str, int]] = set()
    if not os.path.exists(results_path):
        return done
    with open(results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            done.add((record["persona_id"], record["repeat_idx"]))
    return done


def _append_result(path: str, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_one(persona: Persona, repeat_idx: int) -> dict:
    system_prompt = build_persona_system_prompt(persona)
    response = run_survey(system_prompt)
    return {
        "persona_id": persona.persona_id,
        "repeat_idx": repeat_idx,
        "demographics": persona.demographics,
        "answers": [a.model_dump() for a in response.answers],
        "provider": CONFIG.llm_provider,
        "model": CONFIG.model_name,
        "temperature": CONFIG.temperature,
        # 이 결과가 어떤 필드 조합("실험 조건")으로 만들어졌는지 추적할 수 있도록
        # 프리셋 이름과 실제 필드 목록을 함께 남긴다. (run_config.json에도 같은
        # 정보가 있지만, 레코드 단위로도 남겨야 결과 파일 하나만 떼서 봐도 알 수 있다.)
        "field_set": CONFIG.field_set_name,
        "field_set_fields": get_active_field_set(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    run_id = CONFIG.resume_run_id or _make_run_id()
    run_dir = os.path.join(CONFIG.output_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    results_path = os.path.join(run_dir, "results.jsonl")

    manifest_path = os.path.join(run_dir, "run_config.json")
    if not os.path.exists(manifest_path):
        _write_manifest(run_dir)

    done_keys = _load_done_keys(results_path)
    if done_keys:
        print(f"이어서 실행합니다: 이미 완료된 {len(done_keys)}건은 건너뜁니다.")

    personas = load_personas(n=CONFIG.n_personas, seed=CONFIG.random_seed)
    print(f"{len(personas)}명의 페르소나 로드 완료. 설문 시작... (run_dir={run_dir})")

    for i, persona in enumerate(personas, start=1):
        # 동일 페르소나에 대해 반복 측정 (LLM의 stochasticity를 보기 위함).
        # 재현성이 중요하면 REPEATS_PER_PERSONA=1, TEMPERATURE=0으로 설정.
        for repeat_idx in range(CONFIG.repeats_per_persona):
            if (persona.persona_id, repeat_idx) in done_keys:
                continue
            try:
                record = run_one(persona, repeat_idx)
                _append_result(results_path, record)
            except Exception as e:
                print(f"[에러] persona={persona.persona_id} repeat={repeat_idx}: {e}")

        print(f"[{i}/{len(personas)}] persona={persona.persona_id} 완료")

    print(f"완료. 결과 저장 위치: {run_dir}")


if __name__ == "__main__":
    main()
