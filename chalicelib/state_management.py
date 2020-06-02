from os import environ
from uuid import uuid4

import bucketstore

def save_state(state):
    bucket = bucketstore.get('rightright.state')
    bucket[state] = "valid"

def create_state():
    state = str(uuid4())
    save_state(state)
    return state

def validate_state(state):
    bucket = bucketstore.get('rightright.state')

    state_valid = False
    if state in bucket:
        state_valid = True
        del bucket[state]

    return state_valid
