import os
from fastapi import FastAPI, UploadFile, HTTPException
from pathlib import Path
import gridfs
from pydantic import BaseModel, Field
import asyncio

from pymongo import MongoClient
from redis import StrictRedis

DEBUG = os.getenv("DEBUG", False)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:rootroot@mongodb:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "files_db")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

TOTAL_STEPS = int(os.getenv("TOTAL_STEPS", 20))
DELAY = int(os.getenv("DELAY", 2))


app = FastAPI(debug=DEBUG)


# set up the connection to the MongoDB server
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
grid_fs = gridfs.GridFS(db)


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".gif"}


redis_client = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


class FileModel(BaseModel):
    """
    FileModel class represents a model for file metadata and processing progress.
    Attributes:
        file_id (str): The unique identifier of the file.
        filename (str): The path to the file.
        progress (int): The progress of the file processing out of 100. Defaults to 0.
    Methods:
        get_dict() -> dict: Returns a dictionary representation of the file metadata.
    """

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



def add_to_redis(file_id, file: FileModel):
    redis_client.hmset(file_id, file.model_dump())

def get_from_redis(file_id) -> FileModel:
    file_kwargs = redis_client.hgetall(file_id)
    if not file_kwargs:
        return None
    return FileModel(**file_kwargs)

def set_progress(file_id, progress):
    file = get_from_redis(file_id)
    file.progress = progress
    add_to_redis(file_id, file)


@app.post("/upload")
async def upload_files(files: list[UploadFile]):
    """
    Uploads a list of files to the server, processes them, and stores their metadata.
    Args:
        files (list[UploadFile]): A list of files to be uploaded.
    Returns:
        list[dict]: A list of dictionaries containing metadata of the uploaded files.
    Raises:
        HTTPException: If any file type is not allowed.
    """
    if len(files) == 1 and files[0].filename == "" and files[0].size == 0:
        raise HTTPException(status_code=400, detail="No files uploaded")
    allowed, file_extension = files_allowed(files)
    if not allowed:
        raise HTTPException(
            status_code=400, detail=f"File type {file_extension} is not allowed."
        )

    upload_files = []
    for file in files:
        print(f"Uploading file: {file.filename=}")
        file_id = str(grid_fs.put(file.file, filename=file.filename, content_type=file.content_type, size=file.size))
        print(f"File uploaded to mongosdb: {file_id=}")
        file_model = FileModel(
            file_id=file_id,
            filename=file.filename,
        )
        asyncio.create_task(process_file(file_id))
        upload_files.append(file_model.get_dict())
        add_to_redis(file_id, file_model)
    return upload_files


def files_allowed(files: list[UploadFile]) -> tuple[bool, str | None]:
    """
    Checks if the uploaded files have allowed extensions.

    Args:
        files (list[UploadFile]): A list of uploaded files to be checked.

    Returns:
        tuple[bool, str | None]: A tuple where the first element is a boolean indicating
        if all files have allowed extensions, and the second element is the extension
        of the first disallowed file found, or None if all files are allowed.
    """
    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            return False, file_extension
    return True, None


@app.get("/progress/{file_id}")
async def get_progress(file_id: str):
    """
    Asynchronously retrieves the progress of a file based on its file ID.

    Args:
        file_id (str): The unique identifier of the file.

    Returns:
        dict: A dictionary containing the file ID and its progress.

    Raises:
        HTTPException: If the file with the given ID is not found.
    """
    file = get_from_redis(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"file_id": file_id, "progress": file.progress}


@app.get("/result/{file_id}")
async def get_result(file_id: str):
    """
    Asynchronously retrieves the result of a processed file.

    Args:
        file_id (str): The unique identifier of the file.

    Returns:
        dict: A dictionary containing the file_id and the result text extracted from the file.

    Raises:
        HTTPException: If the file is not found (status code 404).
        HTTPException: If the file processing is not complete (status code 400).
    """
    file = get_from_redis(file_id)
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
    Asynchronously processes a file by simulating a series of steps and updating progress.
    Args:
        file_id (str): The unique identifier of the file to be processed.
    Returns:
        None
    This function simulates processing a file in 10 steps, with each step taking 2 seconds.
    It updates the progress of the file in the `files_db` after each step.
    """
    print(f"Processing file {file_id}")
    for step in range(1, TOTAL_STEPS + 1):
        await asyncio.sleep(DELAY)  # Simulating time-consuming work
        print(f"Step {step} done for file {file_id}")
        progress = step * 100 // TOTAL_STEPS
        set_progress(file_id, progress)
    set_progress(file_id, 100)
    print(f"Processing complete for file {file_id}")
    return
