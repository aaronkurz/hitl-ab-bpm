
from models import db
# https://docs.camunda.org/manual/7.5/reference/rest/task/get/
class Task(db.Model):
    __tablename__='tasks'
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(100))
    assignee = db.Column(db.String(100))
    created  = db.Column(db.String(100))
    due = db.Column(db.String(100))
    followUp = db.Column(db.String(100))
    delegationState = db.Column(db.String(100))
    description = db.Column(db.String(100))
    executionId = db.Column(db.String(100))
    owner = db.Column(db.String(100))
    parentTaskId = db.Column(db.String(100))
    priority = db.Column(db.String(100))
    processDefinitionId = db.Column(db.String(100))
    processInstanceId = db.Column(db.String(100))
    caseExecutionId = db.Column(db.String(100))
    caseDefinitionId = db.Column(db.String(100))
    caseInstanceId = db.Column(db.String(100))
    formKey = db.Column(db.String(100))
    tenantId = db.Column(db.String(100))


    def __init__(self,id,name):
        self.id=id
        self.name=name

    def __repr__(self):
        return f'Task {self.id} : {self.name}'



