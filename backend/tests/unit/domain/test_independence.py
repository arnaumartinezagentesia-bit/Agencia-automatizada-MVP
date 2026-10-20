import ast
from pathlib import Path

import pytest

DOMAIN = Path(__file__).resolve().parents[3] / "app" / "domain"
FORBIDDEN = (
    "fastapi", "starlette", "uvicorn", "httpx", "httpx2", "sqlalchemy", "alembic", "psycopg", "asyncpg",
    "openai", "phaser", "app.api", "app.application", "app.agents", "app.persistence", "app.providers",
    "app.realtime", "app.core", "app.main",
)


def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


@pytest.mark.parametrize("path", sorted(DOMAIN.glob("*.py")), ids=lambda p: p.name)
def test_domain_modules_import_no_framework_or_infrastructure(path):
    bad = [m for m in _imports(path) if any(m == f or m.startswith(f + ".") for f in FORBIDDEN)]
    assert bad == []


def test_domain_modules_exist():
    names = {p.name for p in DOMAIN.glob("*.py")}
    assert {"base.py", "types.py", "enums.py", "errors.py", "market.py", "analysis.py", "run.py", "events.py"} <= names
