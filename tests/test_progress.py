import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, files_db, FileModel

client = TestClient(app)


@pytest.fixture
def setup_files_db():
    # Setup: Add a file to the database
    file_id = "test-file-id"
    file_model = FileModel(file_id=file_id, filename="testfile.pdf")
    files_db.append(file_model.get_dict())
    file_model = files_db.get_file(file_id)
    file_model.progress = 50
    yield file_id
    # Teardown: Clear the database
    files_db.items.clear()


def test_get_progress_success(setup_files_db):
    file_id = setup_files_db
    response = client.get(f"/progress/{file_id}")
    assert response.status_code == 200
    assert response.json() == {"file_id": file_id, "progress": 50}


def test_get_progress_file_not_found():
    response = client.get("/progress/nonexistent-file-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}
