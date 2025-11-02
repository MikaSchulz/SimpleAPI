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
SSH_KEY_PATH = os.getenv("SIMPLE_API_SSH_KEY_PATH")
HOST = os.getenv("SIMPLE_API_HOST")
SSH_USER = os.getenv("SIMPLE_API_SSH_USER")

if not USERNAME or not PASSWORD or not CONTAINER_NAME or not SSH_KEY_PATH or not HOST or not SSH_USER:
    raise RuntimeError("USERNAME, PASSWORD, CONTAINER_NAME, SSH_KEY_PATH, HOST, and SSH_USER environment variables must be set")

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
        ssh_command = [
            "ssh",
            "-i", SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f"{SSH_USER}@{HOST}",
            f"docker restart {CONTAINER_NAME}"
        ]

        logging.info(f"Executing SSH command: {' '.join(ssh_command)}")

        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            logging.error(f"SSH command failed: {result.stderr.strip()}")
            return JSONResponse(
                content={"status": "error", "message": result.stderr.strip()},
                status_code=500
            )

        logging.info(f"SSH command succeeded: {result.stdout.strip()}")
        return JSONResponse(content={"status": "done", "output": result.stdout.strip()})

    except subprocess.TimeoutExpired:
        logging.error("SSH command timed out")
        return JSONResponse(
            content={"status": "error", "message": "SSH command timed out"},
            status_code=500
        )
    except Exception as e:
        logging.error(f"Error when updating blog: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )
