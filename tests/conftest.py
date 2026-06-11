import os
import sys
from pathlib import Path
from tempfile import mkstemp

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app as app_module


@pytest.fixture
def client(monkeypatch):
    fd, raw_path = mkstemp(suffix=".db")
    os.close(fd)
    temp_db_path = Path(raw_path)

    monkeypatch.setattr(app_module, "DB_PATH", temp_db_path)
    app_module.setup_database()
    app_module.app.config.update(TESTING=True, _db_initialized=True)

    with app_module.app.test_client() as test_client:
        yield test_client

    if temp_db_path.exists():
        temp_db_path.unlink()
