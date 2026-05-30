import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _python_files(folder: str) -> list[Path]:
    return [path for path in (SRC / folder).rglob("*.py") if "__pycache__" not in path.parts]


def test_domain_imports_only_stdlib_or_domain_modules():
    forbidden_prefixes = ("src.application", "src.infrastructure", "src.interface", "pydantic", "psycopg")

    for path in _python_files("domain"):
        assert not any(
            name.startswith(forbidden_prefixes) for name in _imports(path)
        ), f"{path} violates domain dependency rule"


def test_application_does_not_import_interface_or_infrastructure():
    forbidden_prefixes = ("src.infrastructure", "src.interface")

    for path in _python_files("application"):
        assert not any(
            name.startswith(forbidden_prefixes) for name in _imports(path)
        ), f"{path} violates application dependency rule"


def test_infrastructure_does_not_import_interface():
    for path in _python_files("infrastructure"):
        assert not any(
            name.startswith("src.interface") for name in _imports(path)
        ), f"{path} violates infrastructure dependency rule"
