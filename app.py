from typing import Dict
from fastapi import FastAPI, UploadFile, HTTPException
import shutil
from pathlib import Path
from pydantic import BaseModel, Field
import uuid
import asyncio

app = FastAPI()

UPLOAD_FOLDER = Path("uploaded_files")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


class FileModel(BaseModel):
    file_id: str = Field(
        title="file identifier",
        description="The unique identifier of the file",
    )
    filename: str = Field(
        "file path",
        description="The path to the file",
    )
    size: int = Field(
        title="file size",
        description="The size of the file in bytes",
        default=0,
    )
    progress: int = Field(
        title="processing progress",
        description="The progress of the file processing out of 100",
        default=0,
    )

    def get_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filename": self.filename,
        }


class FileDB(BaseModel):
    items: Dict[str, FileModel] = {}

    def append(self, file: dict):
        self.items[file["file_id"]] = FileModel(**file)

    def get_file(self, file_id: str) -> FileModel | None:
        return self.items.get(file_id, None)


files_db = FileDB()


@app.post("/upload")
async def upload_files(files: list[UploadFile]):
    allowed, file_extension = files_allowed(files)
    if not allowed:
        raise HTTPException(
            status_code=400, detail=f"File type {file_extension} is not allowed."
        )

    upload_files = []
    for file in files:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_model = FileModel(
            file_id=file_id,
            filename=file.filename,
            size=file.size,
        )
        asyncio.create_task(process_file(file_id))
        upload_files.append(file_model.get_dict())
        files_db.append(file_model.get_dict())
    return upload_files


def files_allowed(files: list[UploadFile]) -> tuple[bool, str | None]:
    allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".gif"}
    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            return False, file_extension
    return True, None


@app.get("/progress/{file_id}")
async def get_progress(file_id: str):
    file = files_db.get_file(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"file_id": file_id, "progress": file.progress}


@app.get("/result/{file_id}")
async def get_result(file_id: str):
    file = files_db.get_file(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    if file.progress < 100:
        raise HTTPException(status_code=400, detail="File processing not complete")
    return {
        "file_id": file_id,
        "result": f"Text extracted from the file {file.filename}",
    }


async def process_file(file_id: str):
    """
    Simulates file processing in chunks and updates progress.
    """
    print(f"Processing file {file_id}")
    total_steps = 10  # Simulating 10 steps
    for step in range(1, total_steps + 1):
        await asyncio.sleep(2)  # Simulating time-consuming work
        print(f"Step {step} done for file {file_id}")
        progress = step * 100 // total_steps
        # Update progress in files_db
        files_db.get_file(file_id).progress = progress
    files_db.get_file(file_id).progress = 100

    return
