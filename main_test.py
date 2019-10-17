from flask import Flask, request
import os

import main

app = Flask(__name__)

@app.route('/')
@app.route('/auth')
@app.route('/callback', methods=['GET'])
@app.route('/success', methods=['GET'])
def main_index():
    return main.cloud_run(request)

app.secret_key = os.urandom(24)