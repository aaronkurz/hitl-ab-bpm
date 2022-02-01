import pycamunda.processinst
import requests
from sqlalchemy import and_

from config import CAMUNDA_ENGINE_URI
from models import db
from models.process_instance import ProcessInstance


def collect_finished_instances(process_id):
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time is not None,
                                                           ProcessInstance.do_evaluate is True,
                                                           ProcessInstance.reward is None))
    query_param = f'finished=true&processInstanceId={process_id}'
    history_url = '/history/activity-instance?'
    query_url = CAMUNDA_ENGINE_URI + history_url + query_param
    result = requests.get(query_url)
    for _ in relevant_instances:
        for instance in result.json():
            process_instance = ProcessInstance(process_id=instance['processInstanceId'],
                                               camunda_instance_id=instance['endTime'])
            relevant_instances.update(process_instance)
    db.session.commit()