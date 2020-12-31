import os
from flask import Flask, render_template, request, session, g, flash, redirect, Markup, url_for, Response, jsonify, json
from flask_debugtoolbar import DebugToolbarExtension
from models import db, Playlist, Playlist_Song, Song, User, connect_db
from forms import LoginForm, SignupForm, PlaylistForm
from sqlalchemy.exc import IntegrityError
import requests
import praw
from urllib.parse import urlparse, parse_qs, urlencode
import re
from sqlalchemy import desc
from secrets import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import codecs
from prawcore.exceptions import RequestException
import random

CURR_USER_KEY = 'curr_user'


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ListenToThis'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

toolbar = DebugToolbarExtension(app)

connect_db(app)
# db.drop_all()
# db.create_all()

## Here we will deal with adding the user to flask global and session. This will keep track of who is logged in:
@app.before_request
# This decorator makes sure this code runs before each request. This way we're always checking to make sure the user is logged in before displaying page contents
def add_user_to_g():
    """Check if user is logged in, if so add to g"""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Add the user to flask session"""
    
    session[CURR_USER_KEY] = user.id

def do_logout(user):
    """Logout user. Delete their user key from flask session"""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


# This sets up the requirements for the Python Reddit API Wrapper - PRAW. This will be used to get information from the reddit API
reddit = praw.Reddit(client_id="JLjDaGTCPpLteg",
     client_secret="K-vU4R4Ilp4gpmYB-RCfdeXAdCc0kw",
     user_agent="web:JLjDaGTCPpLteg:ListenToThisPlaylist_01")


def get_video_id(url):
    """This function will get the video ID link from any youtube linkformat given"""
    # There are several different types of youtube links:
    # http://youtu.be/video_id
    # http://www.youtube.com/watch?v=video_id
    # http://www.youtube.com/embed/video_id
    # http://www.youtube.com/v/video_id
    # query = urlparse(url)
    
    
    # Parse the URL
    query = urlparse(url)

    # Only deal with youtube links on this site for simplicity
    if 'youtube' in query.hostname:
        # Get the youtube video id from the url, return this value to be used in embed links
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        
        raise KeyError 
    



def extract_title(title):
    """Function to extract the title and artist of a post/song"""

    try:
        # The post titles are all in the same format : ArtistName -- Songname [genre] (year)
        # First, find the ArtistName by searching for a set of characters before '-'
        artist = re.search('[^-]*', title).group()
        # Strip the whitespace off 
        stripped_artist = artist.strip()

        # Now, find characters between '-' and '['
        title = re.search('(?<=- )(.*)(?=\[)', title).group()
        # Strip the whitespace
        stripped_title = title.strip()
        return (stripped_title, stripped_artist)

        # If the song title or artist name has unexpected characters, return errors
    except AttributeError:
        return ('error','error')

@app.route('/')
def redirect_home():
    return redirect('/home/1')

@app.route('/home')
def redirect_first_page():
    return redirect('/home/1')


@app.route('/home/<int:page>')
def show_homepage(page):
    
    """Show the homepage for the app.
       Users who are not logged in see login/Signup version,
       logged in users see their username on navbar"""
    

    # To ensure we don't add duplicates into the database, get a list of all songs already saved to DB
    songs_in_db = [song.post_id for song in Song.query.all()]

    # Here we want to exclude the posts stickied to the top of the sub by the moderators
    # Also, we want to save the info and post id into the database for later viewing

    
    # The API call loads enough posts for 5 pages at a time. If the page number is a multiple of 5, load more
    if page % 5 == 0 or page == 1 or len(Song.query.all()) < 100:
        # Here we need to get a list of reddit posts from the subreddit.
        # Default sort is HOT
        try:
            posts = reddit.subreddit('ListenToThis').hot(limit=(page*20))
        except RequestException:
            # This can happen if the reddit API calls get rate limited
            return render_template('reddit_error.html')
            

        for post in posts:
            # Exclude stickied posts : usually a weekly discussion/melting pot post
            if not post.stickied:
                # Check to make sure the current post isn't already saved to the DB -- no duplicates
                if post.id not in songs_in_db:
                    url = post.url
                    try:
                        video_id = get_video_id(url)
                    except KeyError:
                        # If errors are raised trying to get the video ID, skip this post, it's probably another kind of link like bandcamp/spotify/soundcloud
                        continue
                    if video_id != None:
                            (title, artist) = extract_title(post.title)

                            # If the extract_title function returns an error for either artist or title,
                            # just use the post's full title in place of the extracted values.
                            # This can be caused by the post not following the correct title format or other unexpected characters in the regular expression
                            if title == 'error' or artist == 'error':
                                # Save the song to DB
                                song = Song(post_id=post.id, post_title=post.title, link=video_id)
                                db.session.add(song)
                                db.session.commit()
                                # show_user.append(song)
                            else:
                                song = Song(post_id=post.id, title=title, artist=artist, post_title=post.title, link=video_id)
                                db.session.add(song)
                                db.session.commit()
                                # show_user.append(song)
                       
    
    
    
    
        
    # get posts to show the user from the database. Paginate the results. The page is specified in the query string
    show_user = Song.query.order_by(Song.id.desc()).paginate(page=page, error_out=False, max_per_page=20)
  
    # If no user is logged in, flash a message telling them to login
    if g.user:
        return render_template('home.html', user=g.user, posts=show_user.items, page=page)
    else:
        flash(Markup("<a href='/login'>Log in</a> to create playlists!"), 'warning')
        return render_template('home.html', user=g.user, posts=show_user.items, page=page)




@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login, show login form and authenticate user"""

    form = LoginForm()

    # If there is already a user logged in, redirect them home
    if g.user:
        flash(f'{g.user.username} is already logged in', 'danger')
        return redirect('/home/1')

    # If the form gets submitted:
    if form.validate_on_submit():

        # Use the authenticate class function on the user's username and password data
        user = User.authenticate(form.username.data, form.password.data)

        # if the login credentials are correct, User.authenticate will return the instance of user. If not, user will be False
        if user:
            # Save the user's id in the flask session
            do_login(user)
            # Flash welcome message and redirect user to homepage
            flash(f'Welcome, {user.username}!', 'success')
            return redirect('/home/1')
        else:
            # If the user's login info is incorrect, flash error message, then the form template will render again
            flash('Invalid credentials', 'danger')
    
    # Show login form
    return render_template('login.html', form=form)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle NEW user signup. Show signup form and save user's credentials to DB. Redirect to home
    If form not valid, show the form with errors. 
    If there is already a user with the entered username, flash error message and show form again."""

    form = SignupForm()

    # If user is currently logged in, they can't make a new account. Tell them to logout first.
    if g.user:
        flash('You must logout first', 'danger')
        return redirect('/home/1')
    else:    
    # if the form validates:
        if form.validate_on_submit():
            try:
                # Try to add user to database with the User.signup method. This will fail if trying to add a username that's already taken
                user = User.signup(username=form.username.data, password=form.password.data)
                db.session.commit()
        
            except IntegrityError:
                # Show error message to user 
                flash('Username already taken', 'danger')
                return render_template('signup.html', form=form)

            # Save user ID to flask session and g 
            do_login(user)
            # flash welcome message, redirect home
            flash(f'Welcome, {user.username}', 'success')
            return redirect('/home/1')
    
        else:
            # Show signup form
            return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    """"Logout current user"""


    if CURR_USER_KEY not in session : 
        # If there is not a user logged in, redirect to login page
        return redirect('/login')
    else:
        # Logout user, flash logout message, redirect home
        user = User.query.get(session[CURR_USER_KEY])
        do_logout(user)
        flash(f'{user.username} logged out', 'success')
        return redirect('/home/1')



##### PLAYLIST ROUTES ######

@app.route('/playlists')
def playlists():
    """Show all playlists from all users"""
    playlists = Playlist.query.all()
    return render_template('playlists.html', user=g.user, playlists=playlists)
    

@app.route('/playlists/new', methods=['GET', "POST"])
def new_playlist():
    """Show new playlist form, handle form submission. Redirect to my playlists"""
    # If no user logged in, flash error message and redirect them to login page
    if not g.user:
        flash('You must be logged in to create a playlist!', 'danger')
        return redirect('/login')

    else:
        form = PlaylistForm()

        # If form is submitted:
        if form.validate_on_submit():
            # save playlist to DB, redirect to user's playlist page
            playlist = Playlist(name=form.name.data, description=form.description.data, user_id=g.user.id)
            db.session.add(playlist)
            db.session.commit()
            return redirect(f'/users/{g.user.id}/playlists')

        else:
            # show new playlist form:
            return render_template('new_playlist.html', user=g.user, form=form)


@app.route('/users/<int:id>/playlists')
def user_playlists(id):
    """Find the user with the given id and show their playlists.
     If that user is not found redirect to all playlists and flash error"""
    
    
    owner = User.query.get_or_404(id)

    # If specified user can't be found (IE they have been deleted), show error message and redirect to all playlists
    if not owner:
        flash('Could not find that user', 'danger')
        return redirect('/playlists')

    else:
        # Get specified user's playlists and display them
        playlists = owner.playlists
        return render_template('user_playlists.html', owner=owner, user=g.user, playlists=playlists)


@app.route('/playlists/<int:id>')
def view_playlist(id):
    """View the songs on a playlist"""

    # Get specified playlist. If not found 404
    playlist = Playlist.query.get_or_404(id)

    return render_template('view_playlist.html', playlist=playlist, user=g.user)


@app.route('/playlists/<int:p_id>/add/<string:s_id>', methods=["POST"])
def add_song(p_id, s_id):
    """Add song with given ID to playlist with given ID"""

    # If user is not logged in, do not allow them to add songs:
    if not g.user:
        flash('Log in to add songs', 'warning')
        return redirect('/login')
    
    # Get the previous url to redirect the user back to the page they came from 
    previous_url = request.referrer

    # Get the playlist the user wants to add a song to 
    playlist = Playlist.query.get_or_404(p_id)

    # Make sure the owner of the playlist is the current user. If the playlist is owned by someone else, don't let them change it!
    if playlist.user != g.user:
        flash("Using the url to try to change other users playlists?? How rude", 'danger')
        return redirect(previous_url)

    # Get the song the user wants to add    
    song = Song.query.get_or_404(s_id)

    # Add song to playlist
    playlist.songs.append(song)
    db.session.commit()

    # Redirect back to the page the user came from 
    return redirect(previous_url)


# ------------------------------------------------------------------------------------
########## SPOTIFY ROUTES #############3

@app.route('/spotify')
def spotify_login():
    """Sign user into their spotify using spotify Oauth"""

    # Make sure a user is logged in: 
    if g.user:

        # If the user does not have a spotify token saved in the DB, then that means it is their first time linking their spotify account:
        if g.user.spotify_token == None:

            # Set up requrements for spotify Oauth:
            endpoint = 'https://accounts.spotify.com/authorize?'
            params={"client_id": SPOTIPY_CLIENT_ID, "response_type": 'code', "redirect_uri" : 'http://localhost:5000/callback', 'scope' : 'playlist-modify-public', 'state' : 'shdtehg32'}
            # encode this information into the query string:
            query_str = urlencode(params)

            url = endpoint + query_str

            # Send the user to login with Spotify:
            return redirect(url)

        # If the user already has a spotify token saved in the DB, they have already linked their spotify.
        # All we need to do is check their token for validity, and refresh the token if needed. This is all handled by the check_token() func
        else:
            if check_token():
                return redirect('/home')
        

    # If user is not logged in, flash a login message and redirect them home
    else:
        flash(Markup("<a href='/login'>Log in or create an account</a> first"), 'danger')
        return redirect('/home/1')


def check_token():
    """Function to check the status of the current user's access token"""

    # To check if the user's spotify token is still valid, ask the api for information about the user's profile:
    endpoint = 'https://api.spotify.com/v1/me'
    headers = {'Authorization' : 'Bearer' + g.user.spotify_token}
    response = requests.get(endpoint, headers=headers)
    data = json.loads(response.text)

    # If the api sends back an error, that means the token has expired, so refresh the token. Otherwise return True
    if 'error' in data:
        refresh_token()
    else: 
        return True


def refresh_token():
    """Refresh spotify token"""

    # Set up requirements for refreshing the token:
    endpoint = 'https://accounts.spotify.com/api/token'
    params = {'client_id' : SPOTIPY_CLIENT_ID, 'client_secret' : SPOTIPY_CLIENT_SECRET, 'grant_type' : 'refresh_token', 'refresh_token' : g.user.spotify_refresh_token}
    
    # Send post request to the /token endpoint
    response = requests.post(endpoint,data=params)
    data = json.loads(response.text)
    
    # If the api returns an error, flash error message and redirect home
    if 'error' in data:
        flash('There was an error connecting to Spotify. Try again', 'danger')
        return redirect('/home/1')


    if 'access_token' in data:
        # Get new access token from api
        access_token = data['access_token']

        # Save the new access token to the DB:
        g.user.spotify_token = access_token
        db.session.commit()



@app.route('/callback')
def callback():
    """Handle the response from the user logging in with the Spotify Auth"""

    user = g.user
    args =  request.args
    
    # Check the response from the Spotify API for errors. If errors, redirect home and show error message
    if 'errors' in args:
        flash('There was an error connecting to Spotify. Try again', 'danger')
        return redirect('/home/1')

    else:
        # Get the code and state values from the spotify callback
        code = args.get('code')
        state = args.get('state')
        
        # Set up parameters for a post request to ask for an access token:
        endpoint = 'https://accounts.spotify.com/api/token'
        params = {'client_id' : SPOTIPY_CLIENT_ID, 'client_secret' : SPOTIPY_CLIENT_SECRET, 'grant_type' : 'authorization_code', 'code' : code, 'redirect_uri' : 'http://localhost:5000/callback'}
        headers = {'Authorization' : f'Basic {SPOTIPY_CLIENT_ID}:{SPOTIPY_CLIENT_SECRET}'}
        resp = requests.post(endpoint, data=params)

        data = resp.json()

        # Again, check for errors:
        if 'error' in data:
            flash('There was an error connecting to Spotify. Try again', 'danger')
            return redirect('/home/1')

        # Get the access token returned by Spotify, save it to the DB for the current user
        if 'access_token' in data:
            access_token = data['access_token']
            # The access token will expire after default 1 hour. Spotify also sends a refresh token that can be used to 
            # exchange for a new access token. Save this too, it will be used later 
            refresh_token = data['refresh_token']
            g.user.spotify_token = access_token
            g.user.spotify_refresh_token = refresh_token
            g.user.spotify_code = code
            db.session.commit()

            flash('Spotify account successfully linked!' , 'success')
        
        # Now we need to get the user's spotify id and save it to the DB
        endpoint = 'https://api.spotify.com/v1/me'
        headers = {"Authorization" : "Bearer " + g.user.spotify_token}
        res = requests.get(endpoint, headers=headers)
        data = json.loads(res.text)
        user_id = data['id']
        user.spotify_id = user_id
        db.session.commit()
            
        return redirect('/home/1')
    


@app.route('/playlists/<int:pid>/spotify')
def convert_playlist(pid):
    """Convert local playlist to spotify playlist"""

    # If no user is logged in, redirect them to login, they need to login before accessing this route
    if not g.user:
        flash('You must login to create spotify playlists!', 'warning')
        return redirect('/login')

    # If the user has not linked their spotify account, redirect them home
    elif not g.user.spotify_token:
        flash('You must link your spotify account to create spotify playlists!', 'warning')
        return redirect('/home/1')

    else:
        # check_token() will make sure the user's spotify access token is still active. If not, it will refresh it so
        # we can continue to have access to the API
        check_token()

        # required headers for calling the spotify API:
        headers={ 'Authorization': "Bearer " + g.user.spotify_token}

        # Get the playlist the user wants to add to spotify
        playlist = Playlist.query.get_or_404(pid)

        # If the playlist in question does not already have a spotify ID associated with it, call create_playlist to make it,
        # and save the playlist spotify ID to the DB
        if playlist.spotify_id == None:
            playlist_sid = create_playlist(playlist.name, playlist.description)
            playlist.spotify_id = playlist_sid
            db.session.commit()

        # Get the spotify ids for all the songs in the playlist
        get_spotify_ids(playlist.songs)

        # add the songs to the playlist. Returns Falsy value if none of the song titles could be found
        res = add_songs_spotify(playlist.songs, playlist)

        # if no songs can be found on spotify (i.e. all the songs are from artists with no music on Spotify), flash error message
        # and return to playlist page
        if not res:
            flash("Could not find any of those songs on Spotify! Add more songs and try again", 'warning')
            return redirect(f'/playlists/{playlist.id}')

        flash('Playlist created on Spotify! Go check your spotify playlists page!' , 'success')
        return redirect(f'/playlists/{playlist.id}')



def get_spotify_ids(songs):
    """Get spotify IDs for a list of tracks."""

    # Headers for Spotify API:
    headers={ 'Authorization': "Bearer " + g.user.spotify_token}

    # loop through a list of songs passed as an argument to this function:
    for item in songs:

            # Get each song from the DB
            song = Song.query.get(item.id)

            # Pass the song title and artist into the url to pass to spotify:
            url = f'https://api.spotify.com/v1/search?q=track:{song.title}%20artist:{song.artist}&type=track'

            # Send get request to Spotify
            response = requests.get(url, headers=headers)

            # Check spotify response. If status code is correct, load the response data
            if response.status_code == 200:
                data = json.loads(response.text)

                # If the response data is an empty list, Spotify could not find the song, continue to next song in loop
                if len(data['tracks']['items']) == int(0):
                    
                    continue
                else:
                    # Save the spotify ID and URI to the song's row in the database
                    spotify_id = data['tracks']['items'][0]['id']
                    spotify_uri = data['tracks']['items'][0]['uri']
                    song.spotify_id = spotify_id
                    song.spotify_uri = spotify_uri
                    db.session.commit()
                    
            else:
                continue



def create_playlist(name, description):
    """Create a playlist with given name and description"""
    # Headers for spotify API call
    headers = {'Authorization' : 'Bearer ' + g.user.spotify_token}

    # Pass the current user's spotify ID into the url
    url = f'https://api.spotify.com/v1/users/{g.user.spotify_id}/playlists'

    # Pass in the name and description of the playlist, make it public 
    data = {'name' : name, 'description' : description, 'public' : 'True'}

    # Send post request to create playlist
    res = requests.post(url, json=data, headers=headers)
    
    # Spotify returns information about the newly created playlist. Get the spotify ID for this playlist, and return it 
    data = json.loads(res.text)
    playlist_sid = data['id']
    return playlist_sid
    

def add_songs_spotify(songs, playlist):
    """Add songs to an existing spotify playlist"""

    # Now we need to get a list of the tracks already on the spotify playlist in question to make sure we don't add duplicates:
    on_spotify = []
    headers = {'Authorization' : f'Bearer {g.user.spotify_token}', 'Content-Type' : 'application/json'}

    # Pass in the playlist's spotify ID to the url
    url = f'https://api.spotify.com/v1/playlists/{playlist.spotify_id}/tracks'

    # Send a get request to Spotify, getting a list of tracks already on the spotify version of this playlist
    res = requests.get(url, headers=headers)
    
    if res.status_code != 400:
        # If successful, save the spotify track id of all songs already in the spotify playlist,
        # hold these values in on_spotify []
        
        data = json.loads(res.text)
        for track in data['items']:
            id = track['track']['id']
            on_spotify.append(id)
    # else:
    #     # This part should make sure that if the user deletes their playlist on spotify's app, this function still works. 
    #     playlist.spotify_id = None
    #     db.session.commit()
    #     return redirect(f'/playlists/{playlist.id}/spotify')
    

    # Initialize dictionary to hold the spotify URIs for the songs we want to add
    data = {'uris':[]}

    # Loop through each song in the playlist:
    for item in playlist.songs:

        # Get each song, check to make sure the song has a spotify ID and it's not already in the playlist
        song = Song.query.get(item.id)
        
        if song.spotify_id != None and song.spotify_id not in on_spotify:
            # Add the song URI to the list of URIs to give to Spotify
            data['uris'].append(song.spotify_uri)
            
            
    # If the list is empty, return false. None of the songs were found
    if len(data['uris']) == 0:
        return False
        
    # This request adds the songs to the playlist that was created earlier
    headers = {'Authorization' : f'Bearer {g.user.spotify_token}', 'Content-Type' : 'application/json'}
    url = f'https://api.spotify.com/v1/playlists/{playlist.spotify_id}/tracks'
    res = requests.post(url, headers=headers, json=data)
    return True


        



@app.route('/playlists/<int:pid>/recommend')
def recommend(pid):
    """Create a playlist on the user's spotify with recommended songs based on a playlist"""

    # Make sure user is logged in and has linked their spotify:
    if not g.user.spotify_token:
        flash('Login and link your spotify account first', 'warning')

    # check user's access token
    check_token()
    
    # Get the playlist the user wants recommendations on:
    playlist = Playlist.query.get_or_404(pid)

    # Get the spotify IDs for all songs in playlist
    get_spotify_ids(playlist.songs)

    on_spotify = []

    # Loop through each song:
    for song in playlist.songs:
        # IF the song can't be found on spotify through the search, it will have no Spotify ID, skip it
        if song.spotify_id == None:
            continue
        else:
            on_spotify.append(song.spotify_id)
    
    # The recommendation algorithm takes up to 5 songs, so we need to choose 5 at random to pass to the API
    if len(on_spotify) == 0:
        flash('Looks like none of the songs in this playlist are on Spotify! Add more songs and try again', 'danger')
        return redirect(f'/playlists/{pid}')
    else:
        try:
            # random.sample returns a valueError if the length of available songs is less than 5. In that case, just pass in however may songs we have
            seed_tracks = random.sample(on_spotify, 5)
        except ValueError:
            seed_tracks = on_spotify
    
    # So now we have an array called seed_tracks which we will pass to the recommendation API endpoint
    # We need to turn this array into a comma-separated string
    seed_string = ','.join(map(str, seed_tracks))
    headers = {'Authorization' : 'Bearer ' + g.user.spotify_token}
    url = 'https://api.spotify.com/v1/recommendations'
    params = {'seed_tracks' : seed_string} 
    res = requests.get(url, headers=headers, params=params)
    data = json.loads(res.text)

    # Create a list of recommended song uris
    track_uris = []


    # Get URIs for each track in the recommendations response
    for track in data['tracks']:
        track_uri = track['uri']
        track_uris.append(track_uri)
    

    recommend_id = create_playlist(f'{playlist.name} Recommendations', f'Recommendations based on playlist: {playlist.name}')
    headers = {'Authorization' : 'Bearer ' + g.user.spotify_token, 'Content-Type' : 'application/json'}
    url = f'https://api.spotify.com/v1/playlists/{recommend_id}/tracks'
    res = requests.post(url, headers=headers, json=track_uris)
    
    

    return render_template('test.html', data=res.text)



            
            



