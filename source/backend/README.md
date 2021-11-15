# Main Backend

## Main Functionalities

* API endpoint for frontend
* Communication with camunda engine
* Process bandit interface/implementation

## Tech stack

* python
* Flask
* Postgres
* Docker

## Setup

you can run it in 3 different ways, to run it isolated

## Locally

install virtualenv

run

`virtualenv sbenv`

`source sbenv/bin/activate`

`pip install -r requirements.txt`

## Docker

run

`docker build -t sbe_prototyping:latest .`

`docker run -d -p 5001:5001 sbe_prototyping`

if you want to enable hot reloading for flask run instead

`docker run -p 5001:5001 -v [ABSOLUTE PATH TO {backend} FOLDER]:/source sbe_prototyping`

## Docker compose

to run it bundled with all other services please refer to readme in the `/source` file

## After setup

visit `localhost:5001`
