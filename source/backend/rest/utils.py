""" Useful utilities that can be used by multiple rest modules """
# If it is only relevant for one rest module, consider putting it in that module, not here
from models.process import Process


def validate_backend_process_id(process_id: int):
    """Check whether a process exists for that process id.

    :param process_id: specify process
    :raises AssertionError: if amount of processes with that id is not 1
    """
    assert Process.query.filter(Process.id == process_id).count() == 1, "Amount of processes with that id is not 1."
