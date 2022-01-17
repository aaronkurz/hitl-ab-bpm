""" Useful utilities that can be used by multiple rest modules """
# If it is only relevant for one rest module, consider putting it in that module
from flask import abort


def validate_backend_process_id(process_id):
    try:
        int(process_id)
    except TypeError or ValueError:
        abort(400, "Process ID is not a number, but is should be.")
