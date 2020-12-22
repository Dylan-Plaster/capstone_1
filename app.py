import os
from flask import Flask, render_template, request, session, g, flash, redirect, Markup, url_for, Response
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


reddit = praw.Reddit(client_id="JLjDaGTCPpLteg",
     client_secret="K-vU4R4Ilp4gpmYB-RCfdeXAdCc0kw",
     user_agent="web:JLjDaGTCPpLteg:ListenToThisPlaylist")


def get_video_id(url):
    """This function will get the video ID link from any youtube linkformat given"""
    # There are several different types of youtube links:
    # http://youtu.be/video_id
    # http://www.youtube.com/watch?v=video_id
    # http://www.youtube.com/embed/video_id
    # http://www.youtube.com/v/video_id
    # query = urlparse(url)
    
    # if query.hostname == 'youtu.be':
    #     # If the hostname is youtu.be, the video id will be the next part of the url. Get it and exclude the slash
    #     return query.path[1:]
    # if query.hostname in ('www.youtube.com', 'youtube.com'):
    #     if query.path == '/watch':
    #         path = parse_qs(query.query)
    #         try:
    #             return path['v'][0]
    #         except KeyError:
    #             return None
    #     if query.path[:7] == '/embed/':
    #         # check the first 7 characters after the hostname, if they have the /embed/ path:
    #         return query.path.split('/')[2]
    #     if query.path[:3] == '/v/':
    #         return query.path.split('/')[2]

    # # all else failed? Return None
    # return None 
    # if url.startswith(('youtu', 'www')):
    #     url = 'http://' + url
        
    query = urlparse(url)

    if 'youtube' in query.hostname:
        
        if query.path == '/watch':
            return parse_qs(query.query)['v'][0]
        elif query.path.startswith(('/embed/', '/v/')):
            return query.path.split('/')[2]
    elif 'youtu.be' in query.hostname:
        return query.path[1:]
    else:
        
        raise KeyError 
    # query = urlparse(url)
    # if query.hostname == 'youtu.be': return query.path[1:]
    # if query.hostname in {'www.youtube.com', 'youtube.com'}:
    #     if query.path == '/watch': return parse_qs(query.query)['v'][0]
    #     if query.path[:7] == '/embed/': return query.path.split('/')[2]
    #     if query.path[:3] == '/v/': return query.path.split('/')[2]
    # # fail?
    # return None



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
    
    """show the homepage for the app.
       Users who are not logged in see login/Signup version,
       logged in users see their username on navbar"""
    

    # The following line makes sure we're not trying to add a duplicate of a song already in the DB
    songs_in_db = [song.post_id for song in Song.query.all()]

    # Here we want to exclude the posts stickied to the top of the sub by the moderators
    # Also, we want to save the info and post id into the database for later viewing

    
    if page % 5 == 0 or page == 1 or len(Song.query.all()) < 100:
        # Here we need to get a list of reddit posts from the subreddit.
        # Default sort is HOT
        posts = reddit.subreddit('ListenToThis').hot(limit=(page*20))

        for post in posts:
            if not post.stickied:
                if post.id not in songs_in_db:
                    url = post.url
                    try:
                        video_id = get_video_id(url)
                    except KeyError:
                        continue
                    if video_id != None:
                            (title, artist) = extract_title(post.title)
                            if title == 'error' or artist == 'error':
                                song = Song(post_id=post.id, post_title=post.title, link=video_id)
                                db.session.add(song)
                                db.session.commit()
                                # show_user.append(song)
                            else:
                                song = Song(post_id=post.id, title=title, artist=artist, post_title=post.title, link=video_id)
                                db.session.add(song)
                                db.session.commit()
                                # show_user.append(song)
                       
    
    
    
    
    import pdb
    pdb.set_trace
        

    show_user = Song.query.order_by(Song.id).paginate(page=page, error_out=False, max_per_page=20)
  
    if g.user:
        return render_template('home.html', user=g.user, posts=show_user, page=page)
    else:
        flash(Markup("<a href='/login'>Log in</a> to create playlists!"), 'warning')
        return render_template('home.html', user=g.user, posts=show_user, page=page)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login, show login form and authenticate user"""

    form = LoginForm()

    if g.user:
        flash(f'{g.user.username} is already logged in', 'danger')
        return redirect('/')

    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f'Welcome, {user.username}!', 'success')
            return redirect('/home/1')
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle NEW user signup. Show signup form and save user's credentials to DB. Redirect to home
    If form not valid, show the form with errors. 
    If there is already a user with the entered username, flash error message and show form again."""

    form = SignupForm()

    if g.user:
        flash('You must logout first', 'danger')
        return redirect('/')
    else:    
    # if the form validates:
        if form.validate_on_submit():
            try:
                # Try to add user to database with the User.signup method
                user = User.signup(username=form.username.data, password=form.password.data)
                db.session.commit()
        
            except IntegrityError:
                flash('Username already taken', 'danger')
                return render_template('signup.html', form=form)
        
            do_login(user)
            flash(f'Welcome, {user.username}')
            return redirect('/home/1')
    
        else:
            return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    """"Logout current user"""

    if CURR_USER_KEY not in session : 
        # If there is not a user logged in, redirect to login page
        return redirect('/login')
    else:
        user = User.query.get(session[CURR_USER_KEY])
        do_logout(user)
        flash(f'{user.username} logged out', 'success')
        return redirect('/home/1')


@app.route('/playlists')
def playlists():
    """Show all playlists from all users"""
    playlists = Playlist.query.all()
    return render_template('playlists.html', user=g.user, playlists=playlists)
    
@app.route('/playlists/new', methods=['GET', "POST"])
def new_playlist():
    """Show new playlist form, handle form submission. Redirect to my playlists"""
    if not g.user:
        flash('You must be logged in to create a playlist!', 'danger')
        return redirect('/login')
    else:
        form = PlaylistForm()

        if form.validate_on_submit():
            playlist = Playlist(name=form.name.data, description=form.description.data, user_id=g.user.id)
            db.session.add(playlist)
            db.session.commit()
            return redirect(f'/users/{g.user.id}/playlists')
        else:
            return render_template('new_playlist.html', user=g.user, form=form)


@app.route('/users/<int:id>/playlists')
def my_playlists(id):
    """Find the user with the given id and show their playlists.
     If that user is not found redirect to all playlists and flash error"""
    
    owner = User.query.get_or_404(id)

    if not owner:
        flash('Could not find that user', 'danger')
        return redirect('/playlists')
    else:
        playlists = owner.playlists
        return render_template('user_playlists.html', owner=owner, user=g.user, playlists=playlists)


@app.route('/playlists/<int:id>')
def view_playlist(id):
    """View the songs on a playlist"""

    playlist = Playlist.query.get_or_404(id)

    return render_template('view_playlist.html', playlist=playlist, user=g.user)


@app.route('/playlists/<int:p_id>/add/<string:s_id>', methods=["POST"])
def add_song(p_id, s_id):
    """Add song with given ID to playlist with given ID"""

    previous_url = request.referrer

    playlist = Playlist.query.get_or_404(p_id)
    song = Song.query.get_or_404(s_id)

    playlist.songs.append(song)
    db.session.commit()


    return redirect(previous_url)


# ------------------------------------------------------------------------------------
# Now for working with the spotify API:
# ( AKA the hard part )

@app.route('/spotify')
def spotify_login():
    """Sign user into their spotify using spotify Oauth"""

    endpoint = 'https://accounts.spotify.com/authorize?'
    params={"client_id": SPOTIPY_CLIENT_ID, "response_type": 'code', "redirect_uri" : 'http://localhost:5000/callback', 'scope' : 'playlist-modify-public', 'state' : 'shdtehg32'}
    # request_data = (scheme='https', netloc='accounts.spotify.com', path='/authorize', query=)
    query_str = urlencode(params)

    url = endpoint + query_str
        
    if g.user:
        return redirect(url)
        # return redirect(url_for('https://accounts.spotify.com/authorize', client_id=SPOTIPY_CLIENT_ID, response_type='code',redirect_uri='http://localhost:5000/callback', scope='playlist-modify-public'))
    #     resp = requests.get(
    #         "https://accounts.spotify.com/authorize",
    #         params={"client_id": SPOTIPY_CLIENT_ID, "response_type": 'code', "redirect_uri" : 'http://localhost/callback', 'scope' : 'playlist-modify-public', }
    #    )
    #     return resp


    else:
        flash(Markup("<a href='/login'>Log in or create an account</a> first"), 'danger')

@app.route('/callback')
def callback():
    """Handle the response from the user logging in with the Spotify Auth"""

    user = g.user
    args =  request.args
    
    if 'errors' in args:
        print('do something')
    else:
        code = args.get('code')
        state = args.get('state')
        
        endpoint = 'https://accounts.spotify.com/api/token'
        params = {'client_id' : SPOTIPY_CLIENT_ID, 'client_secret' : SPOTIPY_CLIENT_SECRET, 'grant_type' : 'authorization_code', 'code' : code, 'redirect_uri' : 'http://localhost:5000/callback'}

        resp = requests.post(endpoint, data=params)

        data = resp.json()
        if 'error' in data:
            flash('There was an error connecting to Spotify. Try again', 'danger')
            return redirect('/home')
        if 'access_token' in data:
            access_token = data['access_token']
            refresh_token = data['refresh_token']
            g.user.spotify_token = access_token
            g.user.spotify_refresh_token = refresh_token
            db.session.commit()
            
        return render_template('test.html', user=g.user)


