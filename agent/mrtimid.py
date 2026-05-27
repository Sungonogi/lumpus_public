"""
    To use this implementation, you simply have to implement `get_action` such that it returns a legal action.

    ACTIONS
    An action is either the string 'STOP' to stop the run or a list of the coordinates of square that you
    want to explore next.
    By listing multiple squares at the same time,
    your agent might run more efficiently because it reduces the number of interactions with the server.

    HISTORY
    The server provides you with a history of all squares that you've visited.
    For each square you have a Python dictionary like this one:
        {'percepts': ['breeze'], 'pos': [11, 0], 'type': 'stone'}
    'pos' indicates the coordinates of the square that we are currently looking at.
    'type' indicates the type of the square ('water', 'grass', 'stone')
    'percepts' lists extra information. Possible values are 'breeze', 'smell', 'sight-*' where * is the name of a sight
    (e.g. sight-TechFak).

    RUNNING YOUR AGENT
    You can then let your agent compete on the server by calling
        python3 client_simple.py path/to/your/config.json
    It will run forever. You can interrupt it at any point (e.g. by pressing Ctrl-C).
"""

import itertools
import json
import logging

import requests
import time


def get_action(history):
    last_entry = history[-1]
    x, y = last_entry['pos']     # previous position
    if x == 11:    # we have reached the right edge of the map
        return 'STOP'
    percepts = last_entry['percepts']
    if 'smell' in percepts or 'breeze' in percepts:
        return 'STOP'
    return [[x+1, y]]   # it's safe to move one square to the right


def run(config_file, action_function, single_request=False):
    logger = logging.getLogger(__name__)

    with open(config_file, 'r') as fp:
        config = json.load(fp)

    actions = []
    for request_number in itertools.count():
        logger.info(f'Iteration {request_number} (sending {len(actions)} actions)')
        # send request
        response = requests.put(f'{config["url"]}/act/{config["env"]}', json={
            'agent': config['agent'],
            'pwd': config['pwd'],
            'actions': actions,
            'single_request': single_request,
        })
        if response.status_code == 200:
            response_json = response.json()
            for error in response_json['errors']:
                logger.error(f'Error message from server: {error}')
            for message in response_json['messages']:
                logger.info(f'Message from server: {message}')

            action_requests = response_json['action-requests']
            if not action_requests:
                logger.info('The server has no new action requests - waiting for 1 second.')
                time.sleep(1)  # wait a moment to avoid overloading the server and then try again
            # get actions for next request
            actions = []
            for action_request in action_requests:
                actions.append({'run': action_request['run'], 'action': action_function(action_request['percept'])})
        elif response.status_code == 503:
            logger.warning('Server is busy - retrying in 3 seconds')
            time.sleep(3)  # server is busy - wait a moment and then try again
        else:
            # other errors (e.g. authentication problems) do not benefit from a retry
            logger.error(f'Status code {response.status_code}. Stopping.')
            logger.error(response.reason)
            logger.error(response.json())
            break


if __name__ == '__main__':
    import sys
    run(sys.argv[1], get_action, single_request=True)
