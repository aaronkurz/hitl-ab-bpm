from instance_router import instance_router_interface


def test_pb_ready():
    """ Test if process bandit returns a or b when it is ready """
    assert True, instance_router_interface.is_ready_for_instantiation()
    decision = instance_router_interface.instantiate(5, "gov")
    assert decision == 'a' or decision == 'b'
