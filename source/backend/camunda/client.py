import requests


class CamundaClient:
    def __init__(self, url):
        self.url = url

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
