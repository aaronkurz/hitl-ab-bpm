import requests


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

    def status_code_successful(self,status_code: int):
        return str(status_code)[0] == '2'

    def deploy_process(self,bpmn_file: str):

        multipart_form_data = { 
        'deployment-name': (None, 'store'),
        'data': (bpmn_file, open(bpmn_file, 'r')),
}
        response = requests.post(self.url + "/deployment/create", files=multipart_form_data)
        assert(self.status_code_successful(response.status_code))


        for elem in response.json().get('deployedProcessDefinitions'):
            new_process_id = elem

        return new_process_id

    def deploy_processes(self,bpmn_files: list):
        new_process_ids=[]
        for bpmn_file in bpmn_files:
            new_process_ids+=self.deploy_process(bpmn_file)
        return new_process_ids

    def start_instance(self,process_id: int):
        headers = {'Content-Type': 'application/json'}
        response = requests.post("http://localhost:8080/engine-rest/process-definition/" + str(process_id)+ "/start", headers=headers)
        assert(self.status_code_successful(response.status_code))

    def start_instances(self,process_id: int,instance_count: int):
        for _ in range(instance_count):
            self.start_instance(process_id)

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

    
    def clean_process_data(self):

        for elem in ["process-instance", "process-definition", "deployment", "decision-definition"]:
            self.delete_all_data(elem)

    



