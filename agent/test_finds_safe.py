from mrtimid import get_action

def test_get_action_safe_square():
    history = [
        {"pos": [0,0], "percepts": []},
        {"pos": [1,0], "percepts": ["breeze"]},
    ]

    # The agent should choose, the only safe action
    action = get_action(history)
    assert [0, 1] in action and len(action) == 1

test_get_action_safe_square()
