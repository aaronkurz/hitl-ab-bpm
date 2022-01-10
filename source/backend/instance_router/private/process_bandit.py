import random


def get_decision(process_id: int, customer_category: str) -> str:
    """

    :param process_id:
    :param customer_category:
    :return: 'a' or 'b'
    """
    return ['a', 'b'][random.randint(0, 1)]
