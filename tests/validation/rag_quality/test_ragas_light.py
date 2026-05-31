import json
import os
from pathlib import Path

import pytest

DATASET = Path(__file__).resolve().parents[2] / "fixtures" / "ragas_dataset.jsonl"


def _load_dataset() -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_ragas_ground_truth_dataset_has_minimum_quality_shape():
    dataset = _load_dataset()

    assert len(dataset) >= 8
    assert all(item["question"] for item in dataset)
    assert all(item["answer"] for item in dataset)
    assert all(item["contexts"] for item in dataset)
    assert all(item["ground_truth"] for item in dataset)


@pytest.mark.skipif(
    os.getenv("RUN_RAGAS_L2") != "1",
    reason="Ragas real es opt-in: ejecutar con RUN_RAGAS_L2=1 y credenciales LLM.",
)
def test_ragas_package_is_available_for_opt_in_quality_run():
    import ragas  # noqa: F401

    assert _load_dataset()
