import json
import os
from urllib.parse import urlparse

from chalice import Chalice, Response, ForbiddenError
from requests_oauthlib import OAuth2Session

from chalicelib.state_management import create_state, validate_state

client_id = os.environ.get("OAUTH_CLIENT_ID")
client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_host = os.environ.get('GIT_HOSTNAME', 'https://github.com')
token_path = os.environ.get('OAUTH_TOKEN_PATH', '/login/oauth/access_token')
token_url = f"{token_host}{token_path}"
scope = os.environ.get('SCOPES', 'public_repo,read:user')

app = Chalice(app_name="netlify-cms-oauth-chalice")

def get_base_url(current_request):
    headers = current_request.headers
    return '%s://%s' % (headers['x-forwarded-proto'], headers['host'])

def get_url(current_request):
    headers = current_request.headers
    url = '%s://%s' % (headers['x-forwarded-proto'], headers['host'])

    url += "?"
    
    for k, v in app.current_request.query_params.items():
        url += f"{k}={v}&"

    return url

@app.route("/")
def index():
    return Response(
        status_code=200,
        body=f'Hello<br><a href="{get_base_url(app.current_request)}/api/auth">Log in with Github</a>',
        headers={'Content-Type': 'text/html; charset=UTF-8'}
        )

@app.route("/auth")
def auth():
    state = create_state()

    github = OAuth2Session(client_id, scope=scope)
    authorization_url, server_state = github.authorization_url(authorization_base_url, state=state)

    if state != server_state:
        return Response(
            status_code=403,
            body=""
            )
    else:
        return Response(
            status_code=302,
            body='',
            headers={'Location': authorization_url}
            )

@app.route("/callback")
def callback():
    state = app.current_request.query_params.get('state')

    if not validate_state(state):
        return Response(
            status_code=403,
            body=""
            )

    authorization_response = get_url(app.current_request)
    try:
        github = OAuth2Session(client_id, state=state, scope=scope)
        token = github.fetch_token(token_url, client_secret=client_secret, authorization_response=authorization_response)
        content = json.dumps({'token': token.get('access_token', ''), 'provider': 'github'})
        message = 'success'
    except BaseException as e:
        message = 'error'
        content = str(e)
    post_message = json.dumps(f"authorization:github:{message}:{content}")
    return Response(
        status_code=200,
        body="""<html><body><script>
            (function() {
            function receiveMessage(e) {
                console.log("receiveMessage %o", e)
                window.opener.postMessage(
                """+post_message+""",
                e.origin
                )
            }
            window.addEventListener("message", receiveMessage, false)
            console.log("Sending message: %o", "github")
            window.opener.postMessage("authorizing:github", "*")
            })()
            </script></body></html>""",
        headers={'Content-Type': 'text/html; charset=UTF-8'}
        )


@app.route("/success")
def success():
    return Response(
        status_code=204,
        body=''
        )
