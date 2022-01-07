from process_bandit import process_bandit


def test_pb_ready():
    """ Test of process bandit returns a or b when it is ready """
    assert True, process_bandit.is_ready_for_decision()
    decision = process_bandit.get_decision(5, "gov")
    assert decision == 'a' or decision == 'b'
