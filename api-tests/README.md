# API-Tests

## Running the tests

You can run the API-Tests both locally and "on the pipeline" via Github Actions.

### Locally

To run the pipeline locally, make sure that you build and run the docker containers of the backend, frontend, camunda
engine and the postgres database. After that you can eiter run the API tests via the "play button" of your IDE or via
the command line:

```
cd api-tests
pip install -r requirements.txt
pytest
```

### Pipeline

The tests will be run in the pipeline automatically when you create a pull request for the main branch or when you make
a commit to the main branch. You can
also [run them manually](https://docs.github.com/en/actions/managing-workflow-runs/manually-running-a-workflow).

## Writing tests

The tests are written using the Python test framework `pytest`. For guidance and quick-start guides, check out
the [pytest website](https://docs.pytest.org/en/6.2.x/).

To make requests to our backend, you can use the `requests` package. The base url of the backend is stored on the
config.py module. Please use that module to store anything relevant for all the API-tests.

`utils.py` contains useful methods for multiple test modules. If you need to use similar/the same logic in multiple test
modules, put that code in utils (instead if referencing from one test module to another).
