

user = "admin"
password = "admin"
hostname = "database"
port = "5432"
database = "sbe_db" 

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{user}:{password}@{hostname}:{port}/{database}"
)

CAMUNDA_ENGINE_URI = "http://camunda:8080/engine-rest"