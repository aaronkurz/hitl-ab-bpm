""" Used for communication with Camunda Engine """
import requests
import config


class CamundaClient:
    """ Class used for communication with camunda engine """
    def __init__(self, url=config.CAMUNDA_ENGINE_URI):
        self.url = url

    # Status
    @classmethod
    def status_code_successful(cls, status_code: int) -> bool:
        """Assert whether an HTTP status code is successful

        :param status_code: HTTP status code
        :return: True or False
        """
        return str(status_code)[0] == '2'

    ### Section: Deployment & Starting ##

    # Deploying a single process
    def deploy_process(self, path_bpmn_file: str) -> str:
        """Send a process to Camunda Engine and retrieve process id in Camunda Engine.

        :param path_bpmn_file: path of bpmn file on filesystem of server
        :return: id of process in camunda engine
        """
        with open(path_bpmn_file, 'r', encoding="UTF-8") as bpmn_file:
            multipart_form_data = {
                'deployment-name': (None, 'store'),
                'data': (path_bpmn_file.split("/")[len(path_bpmn_file.split("/")) - 1], bpmn_file),
            }
            response = requests.post(self.url + "/deployment/create", files=multipart_form_data)
            assert self.status_code_successful(response.status_code)

            assert len(response.json().get('deployedProcessDefinitions')) == 1
            new_process_id = None
            for elem in response.json().get('deployedProcessDefinitions'):
                new_process_id = elem

            return new_process_id

    # Starting a single instance
    def start_instance(self, process_id: str) -> str:
        """Start an instance with a certain camunda process id.

        :param process_id: specify which process with !camunda process id!
        :return: instance id in camunda engine
        """
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url + "/process-definition/" + str(process_id) + "/start", headers=headers)
        assert self.status_code_successful(response.status_code)
        return response.json().get('id')
