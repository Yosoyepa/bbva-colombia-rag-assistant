from src.infrastructure.llm.factory import LLMFactory


def test_llm_factory_rejects_unknown_provider():
    try:
        LLMFactory.create("desconocido", "modelo")
    except ValueError as exc:
        assert "MODEL_PROVIDER desconocido" in str(exc)
    else:
        raise AssertionError("LLMFactory debió rechazar proveedores desconocidos")
