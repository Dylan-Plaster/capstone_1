from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
db = SQLAlchemy()

class User(db.Model):
    """user"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False, unique=True)
    hashed_pw = db.Column(db.String, nullable=False)
    spotify_token = db.Column(db.String, unique=True)

    playlists = db.relationship('Playlist', backref='user')

    @classmethod
    def signup(cls,username, password):
        """Sign up NEW user. Hash password before saving to DB"""

        # Hash password:
        hashed_pw = bcrypt.generate_password_hash(password).decode('UTF-8')

        # Save username and hashed password to DB
        user = User(username=username, hashed_pw=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find a user with given username and password.
        Returns user object if found.
        If no user found, returns False"""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_authorized = bcrypt.check_password_hash(user.hashed_pw, password)
            if is_authorized:
                return user
            
        return False





class Playlist(db.Model):
    """playlist"""
    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))
    description = db.Column(db.String)
    img = db.Column(db.String, default='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT6NPCLGI_gY9sNngd3XBui4wnSzgwQH2lmaw&usqp=CAU', nullable=False)

    songs = db.relationship('Song', secondary='playlists_songs', backref='playlists')

class Playlist_Song(db.Model):
    '''playlist_song'''
    __tablename__ = 'playlists_songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlists.id', ondelete='cascade'))
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id', ondelete='cascade'))

class Song(db.Model):
    """song"""
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    artist = db.Column(db.String, nullable=False)
    link = db.Column(db.String, nullable=False)
    spotify_id = db.Column(db.String)
    rating = db.Column(db.String)


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)
