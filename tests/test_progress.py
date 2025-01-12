import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, FileModel

client = TestClient(app)


def test_get_progress_success(mocker):
    file_id = "test_file_id"
    mock_file = FileModel(file_id=file_id, filename="test_file", progress=50)
    mocker.patch("app.get_from_redis", return_value=mock_file)

    response = client.get(f"/progress/{file_id}")

    assert response.json() == {"file_id": file_id, "progress": 50}
    assert response.status_code == 200

def test_get_progress_file_not_found(mocker):
    file_id = "non_existent_file_id"
    mocker.patch("app.get_from_redis", return_value=None)


    response = client.get(f"/progress/{file_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}