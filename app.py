import time
from fastapi import FastAPI, File, UploadFile, HTTPException
import shutil
from pathlib import Path
from pydantic import BaseModel
import uuid
import asyncio

app = FastAPI(debug=True)

UPLOAD_FOLDER = Path("uploaded_files")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

files_db = []
progress_db = {}


@app.post("/upload")
async def upload_files(files: list[UploadFile]):
    # save each file of files in the files_db forlder
    for file in files:
        file_id = uuid.uuid4()
        file_path = UPLOAD_FOLDER / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        files_db.append({"file_id": file_id, "filename": file.filename})
        progress_db[file_id] = 0
        asyncio.create_task(process_file(file_id))
    return files_db


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
