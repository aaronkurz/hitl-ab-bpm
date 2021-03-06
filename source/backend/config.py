""" Configurations for flask app """
import os

from dotenv import load_dotenv

if inside_docker := os.getenv('INSIDE_DOCKER', 'False'):
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

(CAMUNDA_ENGINE_URI) = f"http://{camunda_host}:8080/engine-rest"




K_QUANTILES_REWARD_FUNC = 20  # set the amount of quantiles you want for the reward function
UPPER_CUTOFF_REWARD_FUNC = 0.8
LOWER_CUTOFF_REWARD_FUNC = 0.2
