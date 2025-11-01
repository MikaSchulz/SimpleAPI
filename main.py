from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
import os
import subprocess
import secrets
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("updateblog.log"), logging.StreamHandler()]
)

app = FastAPI(title="EyeTealer API", version="1.0")

security = HTTPBasic()

USERNAME = os.getenv("SIMPLE_API_USERNAME")
PASSWORD = os.getenv("SIMPLE_API_PASSWORD")
CONTAINER_NAME = os.getenv("SIMPLE_API_CONTAINER_NAME")

if not USERNAME or not PASSWORD or not CONTAINER_NAME:
    raise RuntimeError("USERNAME, PASSWORD or CONTAINER_NAME not set!")


@app.get("/")
def root():
    return {"message": "API is running"}


@app.get("/updateblog")
def secure_endpoint(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        # Restart the specified Docker container

        logging.info("Blog update successful")
        return JSONResponse(content={"status": "done"})

    except Exception as e:
        logging.error(f"Error when updating blog: {e}")

    return JSONResponse(
        content={"status": "error", "message": "Error when updating blog"},
        status_code=500
    )