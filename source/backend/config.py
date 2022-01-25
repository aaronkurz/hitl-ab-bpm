import os

from dotenv import load_dotenv

inside_docker = os.getenv('INSIDE_DOCKER', False)

if inside_docker:
    load_dotenv('docker.env')
else:
    load_dotenv()

user = os.getenv('POSTGRES_USER')
password = os.getenv('POSTGRES_PASSWORD')
hostname = os.getenv('POSTGRES_HOST')
port = os.getenv('POSTGRES_PORT')
database = os.getenv('POSTGRES_DB')
camunda_host = os.getenv('CAMUNDA_HOST')

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database}"
)

CAMUNDA_ENGINE_URI = f"http://{camunda_host}:8080/engine-rest"
