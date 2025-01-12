import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, FileModel

client = TestClient(app)


def test_get_result_success(mocker):
    file_id = "test-file-id"
    file = FileModel(file_id=file_id, filename="testfile.pdf", progress=100)
    mocker.patch("app.get_from_redis", return_value=file)
    response = client.get(f"/result/{file_id}")
    assert response.status_code == 200
    assert response.json() == {
        "file_id": file_id,
        "result": f"Text extracted from the file testfile.pdf",
    }


def test_get_result_file_not_found(mocker):
    mocker.patch("app.get_from_redis", return_value=None)
    response = client.get("/result/non-existent-file-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}


def test_get_result_processing_not_complete(mocker):
    file_id = "incomplete-file-id"
    file_model = FileModel(file_id=file_id, filename="incompletefile.pdf", progress=50)
    mocker.patch("app.get_from_redis", return_value=file_model)
    response = client.get(f"/result/{file_id}")
    assert response.status_code == 400
    assert response.json() == {"detail": "File processing not complete"}
