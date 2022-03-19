# Backend

## Overview

### Main functionalities
* API endpoint for frontend
* Communication with camunda engine
* Process bandit interface/implementation
### Tech stack
* python
* Flask
* Postgres
* Docker
## Running the backend
You can run it in 2 different ways
### 1-Locally (No Docker)
#### postgres
install postgresql and make a database with the following configurations (you can change them in the .env file):
```conf
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sbe_db
```
#### camunda
have camunda running on port `8080`
#### Flask
install virtualenv
run

`virtualenv sbenv`

`source sbenv/bin/activate`

`pip install -r requirements.txt`

`python app.y`

#### After setup
Visit `localhost:5001`
### 2-Docker compose
To run it bundled with all other services please refer to readme in the `../source` folder
#### After setup
Visit `localhost:5001`

### Documentation of REST API
Please refer to the SwaggerUI for a visual documentation of the REST API provided by the backend.
It also offers the functionality to play around with the API by sending HTTP requests.
It is reachable when the backend (container) is running under `localhost:5001/swagger`
