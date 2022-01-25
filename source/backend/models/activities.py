from datetime import datetime

from models import db


class Activities(db.Model):
    __tablename__ = "historic_activity_instances"
    id = db.Column(db.Integer, primary_key=True)
    parentActivityInstanceId = db.Column(db.String(100), nullable=False)
    activityId = db.Column(db.String(100), nullable=False)
    activityName = db.Column(db.String(100), nullable=False)
    activityType = db.Column(db.String(100), nullable=False)
    processDefinitionKey = db.Column(db.String(100), nullable=False)
    processDefinitionId = db.Column(db.String(100), nullable=False)
    processInstanceId = db.Column(db.String(100), nullable=False)
    executionId = db.Column(db.String(100), nullable=False)
    taskId = db.Column(db.String(100), nullable=False)
    assignee = db.Column(db.String(100), nullable=False)
    calledProcessInstanceId = db.Column(db.String(100), nullable=False)
    calledCaseInstanceId = db.Column(db.String(100), nullable=True)
    startTime = db.Column(db.DateTime, nullable=False, default=datetime.now())
    endTime = db.Column(db.DateTime, nullable=False, default=datetime.now())
    durationInMillis = db.Column(db.Integer, nullable=True)
    canceled = db.Column(db.Boolean, nullable=False, default=True)
    completeScope = db.Column(db.Boolean, nullable=False, default=True)
    tenantId = db.Column(db.String(100), nullable=True)
    removalTime = db.Column(db.String(100), nullable=True)
    rootProcessInstanceId = db.Column(db.String(100), nullable=True)


'''

Name	Value	Description
id	String	The id of the activity instance.
parentActivityInstanceId	String	The id of the parent activity instance, for example a sub process instance.
activityId	String	The id of the activity that this object is an instance of.
activityName	String	The name of the activity that this object is an instance of.
activityType	String	The type of the activity that this object is an instance of.
processDefinitionKey	String	The key of the process definition that this activity instance belongs to.
processDefinitionId	String	The id of the process definition that this activity instance belongs to.
processInstanceId	String	The id of the process instance that this activity instance belongs to.
executionId	String	The id of the execution that executed this activity instance.
taskId	String	The id of the task that is associated to this activity instance. Is only set if the activity is a user task.
assignee	String	The assignee of the task that is associated to this activity instance. Is only set if the activity is a user task.
calledProcessInstanceId	String	The id of the called process instance. Is only set if the activity is a call activity and the called instance a process instance.
calledCaseInstanceId	String	The id of the called case instance. Is only set if the activity is a call activity and the called instance a case instance.
startTime	String	The time the instance was started. Default format* yyyy-MM-dd'T'HH:mm:ss.SSSZ.
endTime	String	The time the instance ended. Default format* yyyy-MM-dd'T'HH:mm:ss.SSSZ.
durationInMillis	Number	The time the instance took to finish (in milliseconds).
canceled	Boolean	If true, this activity instance is canceled.
completeScope	Boolean	If true, this activity instance did complete a BPMN 2.0 scope.
tenantId	String	The tenant id of the activity instance.
removalTime	String	The time after which the activity instance should be removed by the History Cleanup job. Default format* yyyy-MM-dd'T'HH:mm:ss.SSSZ.
rootProcessInstanceId	String	The process instance id of the root process instance that initiated the process containing this activity instance.
'''
