
import json
from flask import request,jsonify
import create_app,config
from camunda.client import CamundaClient
from models import db
from models.task import Task
from flask_swagger_ui import get_swaggerui_blueprint

app = create_app.create_app()

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "sbe_prototyping_backend"
    }
)

app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

client=CamundaClient(config.CAMUNDA_ENGINE_URI)

@app.route('/')
def index():
    return 'Hello World!!!'

# TODO: remove (just for demonstration)
@app.route('/tasks')
def list_tasks():
    client=CamundaClient(config.CAMUNDA_ENGINE_URI)
    tasks=client.list_tasks().json()

    return jsonify(tasks)

# TODO: remove (just for demonstration)
@app.route('/task/create',methods=['POST'])
def create_task():
    client=CamundaClient(config.CAMUNDA_ENGINE_URI)
    data=request.json
    response=client.create_task(data)

    return jsonify(response.status_code)

# TODO: remove (just for demonstration)
@app.route('/db/tasks')
def list_tasks_db():
    tasks=Task.query.all()
    return (str(tasks))

# TODO: remove (just for demonstration)
@app.route('/db/task/create',methods=['POST'])
def create_task_db():
    data=request.json
    task=Task(**data)
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.name)




# @app.route('/process/deploy',methods=['POST'])
# def deploy_process():
    
#     bpmn_file='resources/food_testing_2.bpmn'


#     pid=client.deploy_process(bpmn_file)

#     return {'pid':pid}

@app.route('/process/deploy',methods=['POST'])
def deploy_process():
    
    bpmn_files=['resources/food_testing_2.bpmn','resources/food_testing.bpmn']


    pids=client.deploy_processes(bpmn_files)

    return json.dumps(pids)


@app.route('/process/<process_id>/start_instance',methods=['POST'])
def start_instance(process_id):

    



    client.start_instance(process_id)

    return {'status':'200'}

@app.route('/process/<process_id>/start_instances',methods=['POST'])
def start_instances(process_id):

    data=request.json
    
    
    instance_count=data['count']



    client.start_instances(process_id,instance_count)

    return {'status':'200'}


@app.route('/process/definition',methods=['DELETE'])
def delete_process_definitions():

    
    client.delete_all_data('process-definition')

    return {'status': '200'}

@app.route('/process/instances',methods=['DELETE'])
def delete_process_instances():

    
    client.delete_all_data('process-instance')

    return {'status': '200'}




@app.route('/process/all',methods=['DELETE'])
def clean_process_data():

    client.clean_process_data()

    return {'status': '200'}


@app.route('/process/history',methods=['GET'])
def retrieve_data():

    return jsonify(client.retrieve_data())






if __name__ == "__main__":
  app.run(host='0.0.0.0',port=5001,debug=True)






    