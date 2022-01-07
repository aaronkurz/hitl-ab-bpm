import random
# Just "fake" methods for now, in order to define an interface to connect the work that has been done
# on the RL side and the api/web-app side (has been kind if separate until now)


def is_ready_for_decision() -> bool:
    """ Check whether there is an active process and a batch/learning-policy and maybe other things """
    return True


def get_decision(process_id: int, customer_category: str) -> str:
    """ Returns either a or b

    :returns 'a' or 'b'
    """
    return ['a', 'b'][random.randint(0, 1)]
