# Backend

<!-- vscode-markdown-toc -->
* 1. [Overview](#Overview)
	* 1.1. [Main functionalities](#Mainfunctionalities)
	* 1.2. [Tech stack](#Techstack)
* 2. [Running the backend](#Runningthebackend)
	* 2.1. [1 - Locally (No Docker)](#LocallyNoDocker)
		* 2.1.1. [postgres](#postgres)
		* 2.1.2. [Camunda](#Camunda)
		* 2.1.3. [Flask](#Flask)
		* 2.1.4. [After setup](#Aftersetup)
	* 2.2. [2 - Docker compose](#Dockercompose)
		* 2.2.1. [After setup](#Aftersetup-1)
* 3. [Linting](#Linting)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

##  1. <a name='Overview'></a>Overview

###  1.1. <a name='Mainfunctionalities'></a>Main functionalities
* API endpoint for frontend
* Communication with camunda engine
* Process bandit interface/implementation
###  1.2. <a name='Techstack'></a>Tech stack
* Python
* Flask
* Postgres
* Docker
##  2. <a name='Runningthebackend'></a>Running the backend
You can run it in 2 different ways
###  2.1. <a name='LocallyNoDocker'></a>1 - Locally (No Docker)
####  2.1.1. <a name='postgres'></a>postgres
install postgresql and make a database with the following configurations (you can change them in the .env file):
```conf
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sbe_db
```
####  2.1.2. <a name='Camunda'></a>Camunda
Have camunda running on port `8080`
####  2.1.3. <a name='Flask'></a>Flask
Install virtualenv
run

`virtualenv sbenv`

`source sbenv/bin/activate`

`pip install -r requirements.txt`

`python app.py`

####  2.1.4. <a name='Aftersetup'></a>After setup
Visit `localhost:5001`

###  2.2. <a name='Dockercompose'></a>2 - Docker compose
To run it bundled with all other services please refer to readme in the `../source` folder

####  2.2.1. <a name='Aftersetup-1'></a>After setup
Visit `localhost:5001`

##  3. <a name='Linting'></a>Linting
To ensure a certain level of code quality as well as consistent docstrings for automatic documentation, we use *pylint*
as a linter. You can check you local code changes using pylint with the `../../.pylintrc` configuration file.
In the CI pipeline, pylint will check compliance of the backend code. Only if there are no issues can a PR then
be merged onto the main branch.
To run the checks locally, either use an extension for your IDE or run the following commands:

`pip install pylint`

`pylint --rcfile ./.pylintrc ./source/backend`
