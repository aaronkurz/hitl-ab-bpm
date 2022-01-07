import random


def get_decision(process_id, customer_category) -> str:
    """ Returns either a or b

    :returns 'a' or 'b'
    """
    return ['a', 'b'][random.randint(0, 1)]
