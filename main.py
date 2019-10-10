from requests_oauthlib import OAuth2Session
from flask import request, redirect, abort
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv


load_dotenv()
client_id = os.environ.get("OAUTH_CLIENT_ID")
client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_host = os.environ.get('GIT_HOSTNAME', 'https://github.com')
token_path = os.environ.get('OAUTH_TOKEN_PATH', '/login/oauth/access_token')
authorize_path = os.environ.get('OAUTH_AUTHORIZE_PATH', '/login/oauth/authorize')
token_url = '{token_host}{token_path}'.format(token_host=token_host, token_path=token_path)
scope = os.environ.get('SCOPES', 'public_repo,read:user')
ssl_enabled = os.environ.get('SSL_ENABLED', '0') == '1'


def index(request):
    """ Show a log in with github link """
    print([request.path, request.full_path, request.script_root, request.base_url, request.url, request.url_root])
    return f'Hello<br><a href="{request.url_root}auth">Log in with Github</a>'


def auth():
    """ We clicked login now redirect to github auth """
    github = OAuth2Session(client_id, scope=scope)
    authorization_url, state = github.authorization_url(authorization_base_url)
    return redirect(authorization_url)


def callback(request):
    """ retrieve access token """
    state = request.args.get('state', '')
    authorization_response = urlparse(request.url)._replace(scheme='https').geturl()
    try:
        github = OAuth2Session(client_id, state=state, scope=scope)
        token = github.fetch_token(token_url, client_secret=client_secret, authorization_response=authorization_response)
        content = json.dumps({'token': token.get('access_token', ''), 'provider': 'github'})
        message = 'success'
    except BaseException as e:
        message = 'error'
        content = str(e)
    post_message = json.dumps('authorization:github:{0}:{1}'.format(message, content))
    return """<html><body><script>
    (function() {
      function recieveMessage(e) {
        console.log("recieveMessage %o", e)
        // send message to main window with da app
        window.opener.postMessage(
          """+post_message+""",
          e.origin
        )
      }
      window.addEventListener("message", recieveMessage, false)
      // Start handshare with parent
      console.log("Sending message: %o", "github")
      window.opener.postMessage("authorizing:github", "*")
      })()
    </script></body></html>"""


def success():
    return '', 204


def cloud_run(request):
    function_enabled = os.environ.get('FUNCTION_ENABLED', 0)
    if not function_enabled == '1':
        return abort(404)

    if request.path == '/':
        return index(request)
    elif request.path == '/auth':
        return auth()
    elif request.path == '/callback' and request.method == 'GET':
        return callback(request)
    elif request.path == '/success' and request.method == 'GET':
        return success()
    else:
        return abort(404)


if __name__ == "__main__":
    # Flask should only run locally, as function is expected to be deployed in Google Cloud Function environment
    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/')
    @app.route('/auth')
    @app.route('/callback', methods=['GET'])
    @app.route('/success', methods=['GET'])
    def main_index():
        return cloud_run(request)
    
    run_config = {}
    if not ssl_enabled:
        # allows us to use a plain HTTP callback
        os.environ['DEBUG'] = "1"
        # If your server is not parametrized to allow HTTPS set this
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    else:
        run_config = {'ssl_context': 'adhoc'}
    app.secret_key = os.urandom(24)

    app.run(
            host=os.environ.get('RUN_HOST', '127.0.0.1'),
            port=int(os.environ.get('RUN_PORT', 5000)),
            debug=True,
            **run_config
            )
