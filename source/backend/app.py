""" Meta tasks to set up and coordinate flask app"""
from flask_swagger_ui import get_swaggerui_blueprint
import config
import create_app
from camunda.client import CamundaClient
from rest.instance_router import instance_router_api
from rest.batch_policy import batch_policy_api
from rest.process import process_api
from rest.meta import meta_api
from rest.batch_policy_proposal import batch_policy_proposal_api

app = create_app.create_app()

app.register_blueprint(batch_policy_api, url_prefix="/batch-policy")
app.register_blueprint(process_api, url_prefix="/process")
app.register_blueprint(instance_router_api, url_prefix="/instance-router")
app.register_blueprint(batch_policy_proposal_api, url_prefix="/batch-policy-proposal")
app.register_blueprint(meta_api, url_prefix="/meta")

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.yaml"
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "sbe_prototyping_backend"}
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

client = CamundaClient(config.CAMUNDA_ENGINE_URI)


@app.route("/")
# pylint: disable=missing-return-doc, missing-return-type-doc
def index():
    """ Just used to manually test whether app is live """
    return "Hello World!"





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
