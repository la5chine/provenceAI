import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app

client = TestClient(app)

def test_upload_files_disallowed_extension():
    file_content = b"test file content"
    files = [
        ("files", ("test1.txt", file_content, "application/octet-stream")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "File type .txt is not allowed."}

def test_upload_files_allowed_extension(mocker):
    mocker.patch("app.grid_fs.put", return_value="mock_file_id")
    mocker.patch("app.add_to_redis")
    mocker.patch("app.asyncio.create_task")

    file_content = b"test file content"
    files = [
        ("files", ("test.pdf", file_content, "application/octet-stream")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert response.json() == [{"file_id": "mock_file_id", "filename": "test.pdf"}]

def test_upload_files_multiple_files(mocker):
    mocker.patch("app.grid_fs.put", return_value="mock_file_id")
    mocker.patch("app.add_to_redis")
    mocker.patch("app.asyncio.create_task")

    file_content = b"test file content"
    files = [
        ("files", ("test1.pdf", file_content, "application/octet-stream")),
        ("files", ("test2.jpg", file_content, "application/octet-stream")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert response.json() == [
        {"file_id": "mock_file_id", "filename": "test1.pdf"},
        {"file_id": "mock_file_id", "filename": "test2.jpg"},
    ]