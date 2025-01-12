# FastAPI File Upload and Processing

This project is a FastAPI application for uploading and processing files. It includes endpoints for uploading files, checking their processing progress, and retrieving the results.

## Requirements

- Python 3.8+
- `pip` (Python package installer)

## Setup

1. **Clone the repository:**

   ```sh
   git clone https://github.com/la5chine/provenceAI.git
   cd provenceAI
   ´´´

2. **Clone the repository:**
    ```
    python -m venv .venv
    ´´´


3. **Activate the virtual environment:**
    ```
    .venv\Scripts\activate
    ´´´


4. **Install the dependencies:**
    ```
    pip install -r requirements.txt
    ´´´


5. **Set up environment variables:**#
Create a .env file in the root directory and add the following variables:
    ```
    DEBUG=True
    UPLOAD_FOLDER=uploaded_files
    TOTAL_STEPS=10
    DELAY=2
    ´´´


6. **Run the application:**
    ```
    uvicorn app:app --reload
    ´´´

**Running Tests**
    ```
    pytest
    ´´´

**Endpoints**
- POST /upload: Upload files
- GET /progress/{file_id}: Get the processing progress of a file
- GET /result/{file_id}: Get the result of a processed file