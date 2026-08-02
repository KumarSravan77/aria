from server.incidents.state_machine import can_transition


def test_valid_transition():
    assert can_transition("TRIGGERED", "INVESTIGATING")


def test_invalid_transition():
    assert not can_transition("CLOSED", "INVESTIGATING")
