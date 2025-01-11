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
    file_model.progress = 100
    yield file_id
    # Teardown: Clear the database
    files_db.items.clear()


def test_get_result_success(setup_files_db):
    file_id = setup_files_db
    response = client.get(f"/result/{file_id}")
    assert response.status_code == 200
    assert response.json() == {
        "file_id": file_id,
        "result": f"Text extracted from the file testfile.pdf",
    }


def test_get_result_file_not_found():
    response = client.get("/result/non-existent-file-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_get_result_processing_not_complete():
    file_id = "incomplete-file-id"
    file_model = FileModel(file_id=file_id, filename="incompletefile.pdf", progress=50)
    files_db.append(file_model.get_dict())
    response = client.get(f"/result/{file_id}")
    assert response.status_code == 400
    assert response.json() == {"detail": "File processing not complete"}
