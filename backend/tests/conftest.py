from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.db import init_db
from app.main import app


@pytest.fixture()
def client():
    db_path = Path(f"data/test-{uuid4().hex}.sqlite3")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.database_path = str(db_path)
    init_db()
    with TestClient(app) as test_client:
        yield test_client
