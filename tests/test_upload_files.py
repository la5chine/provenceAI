import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app, files_db, UPLOAD_FOLDER
from pathlib import Path
import shutil

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Create the upload folder if it doesn't exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    yield
    # Teardown: Clear the upload folder and reset the files_db
    shutil.rmtree(UPLOAD_FOLDER)
    files_db.items.clear()


def test_upload_files_success():
    file_content = b"test file content"
    files = [
        ("files", ("test1.pdf", file_content, "application/pdf")),
        ("files", ("test2.jpg", file_content, "image/jpeg")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for file_data in data:
        assert "file_id" in file_data
        assert "filename" in file_data
        assert file_data["filename"] in ["test1.pdf", "test2.jpg"]
        assert Path(UPLOAD_FOLDER / file_data["filename"]).exists()


def test_upload_files_disallowed_extension():
    file_content = b"test file content"
    files = [
        ("files", ("test1.exe", file_content, "application/octet-stream")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "File type .exe is not allowed."}


def test_upload_files_partial_disallowed_extension():
    file_content = b"test file content"
    files = [
        ("files", ("test1.pdf", file_content, "application/pdf")),
        ("files", ("test2.exe", file_content, "application/octet-stream")),
    ]
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "File type .exe is not allowed."}
