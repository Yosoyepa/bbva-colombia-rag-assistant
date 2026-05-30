import os

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_RAGAS_L2") != "1",
    reason="L2 Ragas es opt-in: ejecutar con RUN_RAGAS_L2=1 y credenciales LLM.",
)


def test_ragas_light_ground_truth_dataset_is_available():
    import ragas  # noqa: F401

    dataset = [
        {
            "question": "¿Qué entidad cubre el asistente?",
            "answer": "BBVA Colombia.",
            "contexts": ["El asistente responde sobre información pública de BBVA Colombia."],
            "ground_truth": "BBVA Colombia",
        },
        {
            "question": "¿Qué debe hacer si el contexto no contiene la respuesta?",
            "answer": "Debe decir que no tiene esa información.",
            "contexts": ["Si la respuesta no está soportada, el asistente no debe inventar."],
            "ground_truth": "Admitir que no sabe",
        },
    ]

    assert len(dataset) >= 2
    assert all(item["contexts"] for item in dataset)
