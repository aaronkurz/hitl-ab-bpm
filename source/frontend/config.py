import os

from dotenv import load_dotenv

inside_docker = os.getenv('INSIDE_DOCKER', False)

if (inside_docker):
    load_dotenv('docker.env')
else:
    load_dotenv()

backend_host = os.getenv('BACKEND_URI')

BACKEND_URI = f"http://{backend_host}:5001/"
