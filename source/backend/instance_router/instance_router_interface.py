""" This is the main entry point to interact with the instance router from the outside """
# Just "fake" methods for now, in order to define an interface to connect the work that has been done
# on the RL side and the api/web-app side (has been kind if separate until now)
from instance_router.private import controller


def is_ready_for_instantiation() -> bool:
    """Check whether there is an active process and a batch/learning-policy and maybe other things.

    :return: True or False
    """
    return True


def instantiate(process_id: int, customer_category: str) -> dict:
    """ Returns either a or b

    :param process_id: specify process
    :param customer_category: specify customer category
    :return: 'a' or 'b'
    """
    instantiation_dict = controller.instantiate(process_id, customer_category)
    return instantiation_dict
