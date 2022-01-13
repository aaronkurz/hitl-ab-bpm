from flask_swagger_ui import get_swaggerui_blueprint
import config
import create_app
from camunda.client import CamundaClient
from rest.instance_router import instance_router_api
from rest.learning_policy import learning_policy_api
from rest.processes import process_variants_api

app = create_app.create_app()

app.register_blueprint(learning_policy_api, url_prefix="/learning-policy")
app.register_blueprint(process_variants_api, url_prefix="/process-variants")
app.register_blueprint(instance_router_api, url_prefix="/instance-router")

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.yaml"
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "sbe_prototyping_backend"}
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

client = CamundaClient(config.CAMUNDA_ENGINE_URI)


@app.route("/")
def index():
    """ Just used to manually test whether app is live """
    return "Hello World!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
