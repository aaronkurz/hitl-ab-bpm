""" Collects data about finished instances from camunda engine """
import requests
from sqlalchemy import and_
from config import CAMUNDA_ENGINE_URI
from models import db
from models.process_instance import ProcessInstance


def collect_finished_instances(process_id: int):
    """Collect data about instances which have been finished in camunda engine

    ... but from which we have not collected the relevant information yet.
    :param process_id: specify process
    """
    relevant_instances = ProcessInstance.query.filter(and_(ProcessInstance.process_id == process_id,
                                                           ProcessInstance.finished_time.is_(None)))
    query_param = dict(finished='true')
    history_url = '/history/process-instance?'
    query_url = CAMUNDA_ENGINE_URI + history_url
    result = requests.get(query_url, params=query_param)
    for backend_instance in relevant_instances:
        for camunda_instance in result.json():
            if camunda_instance.get('id') == backend_instance.camunda_instance_id:
                setattr(backend_instance, 'finished_time', camunda_instance['endTime'])
                setattr(backend_instance, 'instantiation_time', camunda_instance['startTime'])
    db.session.commit()
