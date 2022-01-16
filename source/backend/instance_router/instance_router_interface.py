""" This is the main entry point to interact with the instance router from the outside """
# Just "fake" methods for now, in order to define an interface to connect the work that has been done
# on the RL side and the api/web-app side (has been kind if separate until now)
from instance_router.private import controller


def is_ready_for_instantiation() -> bool:
    """ Check whether there is an active process and a batch/learning-policy and maybe other things """
    return True


def instantiate(process_id: int, customer_category: str) -> str:
    """ Returns either a or b

    :returns 'a' or 'b'
    """
    camunda_instance_id = controller.instantiate(process_id, customer_category)
    return camunda_instance_id



