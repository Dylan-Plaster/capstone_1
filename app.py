from flask import Flask, render_template, redirect, flash, session, request
import startup
from startup import SECRET_KEY, TOKEN_DATA
import spotipy
import spotipy.util as util
# from credentz import *
import time
import json
app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY

API_BASE = 'https://accounts.spotify.com'
CLI_ID = '07050efdb1e8469187a4cb88f9388020'
CLI_SEC = 'b63521b241914810aa562f96083717a2'

# Make sure you add this to Redirect URIs in the setting of the application dashboard
REDIRECT_URI = "http://localhost:5000/callback"

SCOPE = 'playlist-modify-private,playlist-modify-public,user-top-read,streaming,playlist-read-private,user-modify-playback-state,user-read-private,user-read-email'

# Set this to True for testing but you probaly want it set to False in production.
SHOW_DIALOG = True


# authorization-code-flow Step 1. Have your application request authorization; 
# the user logs in and authorizes access
@app.route("/verify")
def verify():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

@app.route("/home")
def homepage():
    return render_template("home.html")

# authorization-code-flow Step 2.
# Have your application request refresh and access tokens;
# Spotify returns access and refresh tokens
@app.route("/callback")
def api_callback():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    # Saving the access token along with all other token related info
    session["token_info"] = token_info


    return redirect("/home")

# authorization-code-flow Step 3.
# Use the access token to access the Spotify Web API;
# Spotify returns requested data
@app.route("/go", methods=['POST'])
def go():
    session['token_info'], authorized = get_token(session)
    session.modified = True
    if not authorized:
        flash("Must login first!")
        return redirect('/home')
    data = request.form
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))

    # q = data['title'].replace(' ', '%20')
    response = sp.search(type='track', q=data['title'])

    # print(json.dumps(response))
    id = response['tracks']['items'][0]['id']
    # return(response)
    return render_template("results.html", data=response, auth=session.get('token_info').get('access_token'), id=id)

# Checks to see if token is valid and gets a new token if not
def get_token(session):
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_token_expired):
        # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you reuse a SpotifyOAuth object
        sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id = CLI_ID, client_secret = CLI_SEC, redirect_uri = REDIRECT_URI, scope = SCOPE)
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid
