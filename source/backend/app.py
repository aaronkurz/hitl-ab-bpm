
from flask import request,jsonify
import create_app,config
from camunda.client import CamundaClient
from models import db
from models.task import Task
from process_bandit.batch_policy import batch_policy_api

app = create_app.create_app()

app.register_blueprint(batch_policy_api, url_prefix="/batch-policy")

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



if __name__ == "__main__":
  app.run(host='0.0.0.0',port=5001,debug=True)






    