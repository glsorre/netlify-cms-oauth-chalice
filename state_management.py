from uuid import uuid4
from google.cloud import firestore
from os import environ

STATE_STORAGE_COLLECTION = environ.get('STATE_STORAGE_COLLECTION', 'ffxiv_pg/oauth_state_storage/states')


def save_state(state):
    db = firestore.Client()
    state_storage = db.collection(STATE_STORAGE_COLLECTION)
    state_storage.document(state).set({'created': firestore.SERVER_TIMESTAMP})
    
    return


def create_state():
    state = str(uuid4())
    
    save_state(state)

    return state


def validate_state(state):
    db = firestore.Client()
    state_doc_ref = db.collection(STATE_STORAGE_COLLECTION).document(state)
    state_doc = state_doc_ref.get()

    state_valid = False
    if state_doc.exists:
        state_valid = True
        state_doc_ref.delete()

    return state_valid