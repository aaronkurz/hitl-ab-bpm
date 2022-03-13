# SBE prototyping

SBE protoyping project

components:

* Backend (Flask)
* postgres database
* camunda process engine
* Frontend (React)

## Setup

Run these commands in the source folder to build and run all containers.

`docker compose build`

`docker compose up`

## Access

* Backend `localhost:5001`
* Frontend `localhost:8501`
* postgres `localhost:5432`
* camunda engine `localhost:8080`

## Linting
To ensure a certain level of code quality as well as consistent docstrings for automatic documentation, we use *pylint*
as a linter. You can check you local code changes using pylint with the `../../.pylintrc` configuration file.
In the CI pipeline, pylint will check compliance of the backend and frontend code. Only if there are no issues can a PR then
be merged onto the main branch.
To run the checks locally, either use an extension for your IDE or run the following commands (while being in the root 
directory of the repo):

`pip install pylint`

`pylint --rcfile ./.pylintrc ./source/backend`

`pylint --rcfile ./.pylintrc ./source/frontend`

Note that the rules regarding docstrings and type annotations are probably a bit too strong for 
flask endpoint functions, you can disable the too strict rules there by pasting this comment above those 
functions:

`# pylint: disable=missing-return-doc, missing-return-type-doc`

  