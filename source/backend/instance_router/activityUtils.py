import time
import pycamunda.processinst
import pycamunda.activityinst
import requests
import logging

logging.basicConfig(format='%(levelname)s:%(message)s',level=logging.INFO)

url = 'http://localhost:8080/engine-rest'

COST={'Schedule':25,
      'Eligibility Test':190,
      'Medical Exam':75,
      'Theory Test':455,
      'Practical Test':1145,
      'Approve':100,
      'Reject':0
}
time_elapsed = {'Schedule':0,
      'Eligibility Test':0,
      'Medical Exam':0,
      'Theory Test':0,
      'Practical Test':0,
      'Approve':0,
      'Reject':0
                }
def instance_terminated():
    '''
    Rnsure all instances have terminated, instead of sleeping for 2 minutes
    In order to avoid an error and ensure the proper execution, it has be ensured that every instance has terminated
    before the data is retrieved.

    :return: True
    '''
    instance_not_terminated = True
    while (instance_not_terminated):
        get_instances = pycamunda.processinst.GetList(url)
        instances = get_instances()
        # instance list is empty, all terminated, proceed
        if not instances:
            instance_not_terminated = False
        time.sleep(1)
    return True

def fetch_acticity_duration():
    '''
    get the duration of each task for all instances
    :return: a dict of time_elapsed of each task for all instances in one batch
    '''
    activity_dict = {}
    time_start = time.time()
    instance_batch_list = []
    while (True):
        get_instances = pycamunda.processinst.GetList(url)
        instances = get_instances()
        for instance in instances:
            get_activityInstance = pycamunda.processinst.GetActivityInstance(url, instance.id_)
            response = requests.get(get_activityInstance.url)
            if instance.id_ not in instance_batch_list:
                instance_batch_list.append(instance.id_)
            if 'childActivityInstances' in response.json():
                activityName = response.json()['childActivityInstances'][0]['activityName']
                actibityId = response.json()['childActivityInstances'][0]['id']
                if not activity_dict.__contains__(actibityId):
                    time_start = time.time()
                    for value in activity_dict.values():
                        # print(value)
                        if value[0]!=None:
                            time_elapsed[value[0]] += value[1]
                activity_dict[actibityId] = [activityName, time.time()-time_start]
                # print(activity_dict)
        time.sleep(0.1)
        if len(instances) == 0:
            logging.info('time_elapsed:')
            logging.info(time_elapsed)
            return(time_elapsed)

def cal_time_based_cost(batch_size):
    '''
    COST*batch_size/time_elapsed
    Offers an additional dimension to compare the variants. This also helps in terms of finding useful parameters for
    the human expert.
    :param batch_size:
    :return: dict of time based cost
    '''
    dict = COST.copy()
    for k, v in COST.items():
        if time_elapsed[k]!=0:
            dict[k] = (dict[k]*batch_size)/time_elapsed[k]

    logging.info('time_based_cost')
    logging.info(dict)
    return(dict)
