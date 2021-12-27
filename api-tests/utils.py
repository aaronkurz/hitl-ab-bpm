import requests

from config import BASE_URL


def set_processes_a_b(process_name: str, path_a: str, path_b: str):
    # given
    files_in = {
        "variantA": open(path_a),
        "variantB": open(path_b)
    }
    # when
    response = requests.post(BASE_URL + "/process-variants/" + process_name, files=files_in)
    # then
    assert response.status_code == requests.codes.ok


def remove_all_process_rows():
    assert requests.delete(BASE_URL + "/process-variants").status_code == requests.codes.OK