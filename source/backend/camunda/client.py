import requests
import os

class CamundaClient:
    def __init__(self, url):
        self.url = url

# TODO: remove just for demonstration
    def get_task(self, task):
        response = requests.get(self.url + f"/task/{task}")
        return response

    def create_task(self, data):
        response = requests.post(self.url + "/task/create", json=data)
        return response

    def update_task(self, task, data):
        response = requests.put(self.url + f"/task/{task}", json=data)
        return response

    def list_tasks(self):
        response = requests.get(self.url + "/task")
        return response
# END TODO: remove just for demonstration


# Status
    def status_code_successful(self,status_code: int):
        return str(status_code)[0] == '2'


### Section: Deployment & Starting ##

# Deploying a single process
    def deploy_process(self,bpmn_file: str):

        

        multipart_form_data = { 
        'deployment-name': (None, 'store'),
        'data': (bpmn_file, open(os.getcwd()+'/'+bpmn_file, 'r')),
}
        response = requests.post(self.url + "/deployment/create", files=multipart_form_data)
        assert(self.status_code_successful(response.status_code))


        for elem in response.json().get('deployedProcessDefinitions'):
            new_process_id = elem

        return new_process_id


# Deploying multiple processes
    def deploy_processes(self,bpmn_files: list):
        new_process_ids=[]
        for bpmn_file in bpmn_files:
            new_process_ids+=self.deploy_process(bpmn_file)
        return new_process_ids


# Starting a single instance
    def start_instance(self,process_id: int):
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url+"/process-definition/" + str(process_id)+ "/start", headers=headers)
        assert(self.status_code_successful(response.status_code))


# Starting multiple instances
    def start_instances(self,process_id: int,instance_count: int):
        for _ in range(instance_count):
            self.start_instance(process_id)


### Section: Data Management ###

# Deleting all data
    def delete_all_data(self,target: str):
        POSSIBLE_TARGETS = ["process-instance", "process-definition", "deployment", "decision-definition"]
        if target not in POSSIBLE_TARGETS:
            raise Exception(str(target) + "not a valid data deletion target")
        
        get_response = requests.get(self.url + "/" + target)
        assert(self.status_code_successful(get_response.status_code))

        for elem in get_response.json():
            current_id = elem.get('id')
            del_response = requests.delete(self.url + "/" + target + "/" + str(current_id))
            assert(self.status_code_successful(del_response.status_code))

    
        get_response = requests.get(self.url + "/" + target)
        assert(self.status_code_successful(get_response.status_code))
        assert(len(get_response.json()) == 0)   


# Cleaning Data
    def clean_process_data(self):

        for elem in ["process-instance", "process-definition", "deployment", "decision-definition"]:
            self.delete_all_data(elem)

    
# Retrieving Data

    def retrieve_data(self):

        # Getting the ID, Key and Name of the process from the json file
        for elem in proc_def_response.json():
            processDefinitionId = elem.get('processDefinitionId')
            processDefinitionKey = elem.get('processDefinitionKey')
            processDefinitionName = elem.get('processDefinitionName')

            params = {'processDefinitionId': str(processDefinitionId)}
            proc_inst_response = requests.get(self.url + "/history/process-instance", params=params)

            assert (status_code_successful(proc_inst_response.status_code))

            # Calculating the duration of the process
            for elem2 in proc_inst_response.json():
                end_datetime = parser.parse(elem2.get('endTime'))
                start_datetime = parser.parse(elem2.get('startTime'))
                processDuration = (end_datetime - start_datetime)


"""
#lines 107-109 could be deleted. 
#Or "processDefinitionId" = processDefinitionId

        data = {
            "processDefinitionId" = elem.get('processDefinitionId')
            "processDefinitionKey" = elem.get('processDefinitionKey')
            "processDefinitionName" = elem.get('processDefinitionName')
        }

        return data
"""
