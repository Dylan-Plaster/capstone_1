import os
from flask import Flask, render_template, request, session, g, flash, redirect
from flask_debugtoolbar import DebugToolbarExtension
from models import db, Playlist, Playlist_Song, Song, User, connect_db
from forms import LoginForm, SignupForm, PlaylistForm
from sqlalchemy.exc import IntegrityError
import requests
import praw
from urllib.parse import urlparse, parse_qs

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
    query = urlparse(url)
    
    if query.hostname == 'youtu.be':
        # If the hostname is youtu.be, the video id will be the next part of the url. Get it and exclude the slash
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            path = parse_qs(query.query)
            return path['v'][0]
        if query.path[:7] == '/embed/':
            # check the first 7 characters after the hostname, if they have the /embed/ path:
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]

    # all else failed? Return None
    return None    




@app.route('/')
def show_homepage():
    """show the homepage for the app.
       Users who are not logged in see login/Signup version,
       logged in users see their username on navbar"""
    
    # Here we need to get a list of reddit posts from the subreddit.
    # Default sort is HOT
    posts = reddit.subreddit('ListenToThis').hot(limit=20)
    
    # Here we want to exclude the posts stickied to the top of the sub by the moderators
    not_sticky = []
    for post in posts:
        if not post.stickied:
            url = post.url
            post.video_id = get_video_id(url)
            not_sticky.append(post)
    
        

    if g.user:
        return render_template('home.html', user=g.user, posts=not_sticky)
    else:
        return render_template('home_anon.html', posts=not_sticky)


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
            return redirect('/')
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

            return redirect('/')
    
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
        return redirect('/login')


@app.route('/playlists')
def playlists():
    """Show playlist listing. Allow user to view their playlists and others"""
    if not g.user:
        print('show anonymous page here')
        raise
    else:
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
            playlist = Playlist(name=form.name.data, description=form.description.data)
            db.session.add(playlist)
            db.session.commit()
            return redirect(f'/users/{g.user.id}/playlists')
        else:
            return render_template('new_playlist.html', user=g.user, form=form)
    