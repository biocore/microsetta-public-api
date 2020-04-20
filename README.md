# microsetta-public-api
A public microservice to support The Microsetta Initiative

## Installation
Create a new `conda` environment:

`conda create -n microsetta-public-api python=3.7 flask

Once the conda environment is created, activate it:

`conda activate microsetta-public-api`

Install connexion version 2.0 (which supports the OpenAPI Specification 3.0) as well as the Swagger UI:

`pip install "connexion[swagger-ui]" pyyaml`

Then install the microsetta-public-api in editable mode:

`pip install -e .`

## Test Usage

In the activated conda environment, start the microservice using flask's built-in server by running, e.g., 

`python ./microsetta_public_api/server.py`

which will start the server on http://localhost:8083 . Note that this usage is suitable for 
**development ONLY**--real use of the service would require a production-level server. 

The Swagger UI should now be available at http://localhost:8083/api/ui .

