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
    # save each file of files in UPLOAD_FOLDER and run process_file in background
    upload_files = []
    for file in files:
        file_id = str(uuid.uuid4())
        file_path = UPLOAD_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_model = FileModel(file_id=file_id, filename=file.filename)
        asyncio.create_task(process_file(file_id))
        upload_files.append(file_model.get_dict())
        files_db.append(file_model.get_dict())
    return upload_files


@app.get("/progress/{file_id}")
async def get_progress(file_id: str):
    # Implémentez le suivi de l’avancement
    pass


@app.get("/result/{file_id}")
async def get_result(file_id: str):
    # Implémentez la récupération des résultats
    pass


async def process_file(file_id: str):
    """
    Simulates file processing in chunks and updates progress.
    """
    total_steps = 10  # Simulating 10 steps
    for step in range(1, total_steps + 1):
        time.sleep(1)  # Simulating time-consuming work
        progress_db[file_id] = int((step / total_steps) * 100)
    progress_db[file_id] = 100
