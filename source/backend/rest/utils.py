""" Useful utilities that can be used by multiple rest modules """
# If it is only relevant for one rest module, consider putting it in that module
from flask import abort
from models.process import Process


def validate_backend_process_id(process_id: int):
    assert Process.query.filter(Process.id == process_id).count() == 1, "Amount of processes with that id is not 1."
