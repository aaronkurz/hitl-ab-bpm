
from flask import request,jsonify
import create_app,config
from camunda.client import CamundaClient
from models import db
from models.task import Task

app = create_app.create_app()

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




@app.route('/task/deploy_process',methods=['POST'])
def deploy_process():
    
    bpmn_file='food_testing_2.bpmn'


    pid=client.deploy_process(bpmn_file)

    return {'pid':pid}

@app.route('/task/deploy_processes',methods=['POST'])
def deploy_processes():
    
    bpmn_files=['food_testing_2.bpmn','food_testing.bpmn','testCheckProcess.bpmn']


    pids=client.deploy_processes(bpmn_files)

    return {'pid':str(pids)}


@app.route('/task/start_instance',methods=['POST'])
def start_instance():

    data=request.json
    pid=data['pid']



    client.start_instance(pid)

    return {'status':'200'}

@app.route('/task/start_instances',methods=['POST'])
def start_instance():

    data=request.json
    pid=data['pid']
    instance_count=data['count']



    client.start_instances(pid,instance_count)

    return {'status':'200'}




if __name__ == "__main__":
  app.run(host='0.0.0.0',port=5001,debug=True)






    