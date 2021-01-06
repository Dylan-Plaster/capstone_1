from unittest import TestCase
import os
from models import db, User, Song, Playlist, Playlist_Song
from urllib.parse import urlparse



os.environ['DATABASE_URL'] = "postgresql:///L2T_test"

from app import *
from flask import session
app.config['WTF_CSRF_ENABLED'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db.create_all()

class ViewTest(TestCase):
    """Test view routes"""

    def create_app(self):

        
        app = Flask(__name__)
        app.config['TESTING'] = True
        db.init_app(app)
        return app
    

    def setUp(self):
        """Set up test client and add test data"""

        # db.session.expunge_all()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.u1 = User.signup(username='testuser1', password='password1')
        u1_id = 100
        self.u1.id = u1_id
        self.u1.password = 'password1'

        self.u2 = User.signup(username='testuser2', password='password2')
        u2_id = 200
        self.u2.id = u2_id
        self.u2.password = 'password2'

        self.u3 = User.signup(username='testuser3', password='password3')
        u3_id = 300
        self.u3.id = u3_id
        self.u3.password = 'password3'

        db.session.add(self.u1)
        db.session.add(self.u2)
        db.session.add(self.u3)
        db.session.commit()


    def tearDown(self):
        db.session.rollback()

        # db.session.commit()
        # db.session.close_all()
        # db.session.close()
        # db.engine.dispose()
        # db.drop_all()
     
  
    

    def test_signup(self):
        
        
        with self.client as client:
            # Test GET /signup. make sure it renders the signup form template
            resp = client.get('/signup')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form method="POST">', html)

            # Test POST /signup with user data. make sure it saves info to database and redirects home
            resp = client.post('/signup', data={'username':'testuser4', 'password':'password4'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            user = User.query.filter_by(username = 'testuser4').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'testuser4')

            # Make sure the password is not stored in plaintext
            self.assertNotEqual(user.hashed_pw, 'password4')

            self.assertIn('Welcome, testuser4', html)


            # Now test submitting the same username again, make sure it flashes an error message
            client.get('/logout')
            resp = client.post('/signup', data={'username':'testuser4', 'password':'password4'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken', html)
    

    def test_login(self):
        """Test login route and template"""

        with self.client as client:
            # Test GET /login. Check that it renders the form 
            resp = client.get('/login')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<form method="POST">',html)

            # Test POST /login with user data
            resp = client.post('/login', data={"username":'testuser1', 'password':'password1'}, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Welcome, testuser1', html)

            # Test the user instance is stored in Flask g:
            self.assertEqual(g.user.id, 100)
            self.assertEqual(g.user.username, 'testuser1')

            # Test the flask session for current user key:
            self.assertEqual(session[CURR_USER_KEY], 100)

            # Now try to log in again with the same user. The user should be redirected home:
            resp = client.post('/login', data={"username":'testuser1', 'password':'password1'}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('testuser1 is already logged in', html)

            # Now logout user, and test an invalid username, should flash error message:
            client.get('/logout') # Clear current user
            resp = client.post('/login', data={"username":'testuser9', 'password':'password1'}, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Invalid credentials', html) # Check for error message
            self.assertIsNone(g.user) # Check that flask g does not have a current user
    
    def test_homepage(self):
        """Test homepage route and template"""

        with self.client as client:
            # Test GET /home/1. Check that the template is displaying and a login message is flashed:
            resp = client.get('/home/1')
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("<a href='/login'>Log in</a> to create playlists!", html)

            # Test that reddit posts have been successfully saved to the database
            self.assertGreater(len(Song.query.all()), 0)
    
    def test_logout(self):
        """Test logout route. Should clear CURR_USER_KEY in flask session and redirect"""

        with self.client as client:
            # Test GET /logout without a user logged in. This should simply redirect to the login page
            resp = client.get('/logout')
            self.assertEqual(resp.status_code, 302)

            # Log in a user, then test the same route
            client.post('/login', data={'username':self.u1.username, 'password':self.u1.password})
            # Make sure the user's key is in the flask session:
            self.assertEqual(session[CURR_USER_KEY], 100)
            # Now test and make sure the logout route clears session[CURR_USER_KEY]
            resp = client.get('/logout', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertNotIn(CURR_USER_KEY, session)
            self.assertIn(f"{self.u1.username} logged out", html)


    def test_playlists(self):
        """Test the /playlists route that shows all playlists from all users"""
        with self.client as client:
            # Set up test playlist data with 2 users:
            data1 = {'username':'testuser1', 'password':'password1'}
            data2 = {'username':'testuser2', 'password':'password2'}
            client.post('/login', data=data1)
            client.post('/playlists/new', data={'name':'user1playlist', 'description':'user1description'})
            client.post('/login', data=data2)
            client.post('/playlists/new', data={'name':'user2playlist', 'description':'user2description'})

            # Test GET /playlists, make sure playlists from both users appear here:
            resp = client.get('/playlists')
            html = resp.get_data(as_text=True)
            self.assertIn('user1playlist', html)
            self.assertIn('user1description', html)
            self.assertIn('user2playlist', html)
            self.assertIn('user2description', html)



        

    def test_new_playlist(self):
        """Test the /playlists/new route"""

        with self.client as client:
            # Test GET /playlists/new with no user logged in:
            resp = client.get('/playlists/new', follow_redirects=True)
            html = resp.get_data(as_text=True)
            # Should flash error message:
            self.assertIn('You must be logged in to create a playlist!', html)

            # Now, login a user, test again. Should render new playlist form:
            client.post('/login', data={'username':'testuser2', 'password':'password2'})
            resp = client.get('/playlists/new')
            html = resp.get_data(as_text=True)
        
            self.assertIn('<form method="POST">',html)

            # Test POST /playlists/new. Should save playlist name and description and redirect to user's playlist page:
            data1 = {"name": 'test_playlist_1', 'description':'description_test'}
            resp = client.post('/playlists/new', data=data1)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(urlparse(resp.location).path, '/users/200/playlists')

            data2 = {"name":'test_playlist_2', 'description':'description_test_2'}
            resp = client.post('/playlists/new', data=data2, follow_redirects=True)
            html = resp.get_data(as_text=True)
            playlist = Playlist.query.filter_by(name='test_playlist_2').first()
            self.assertIsNotNone(playlist)
            self.assertEqual(playlist.name, 'test_playlist_2')
            self.assertEqual(playlist.description, 'description_test_2')

            # Test submitting the same playlist name a second time. Should flash error message and render template
            resp = client.post('/playlists/new', data=data1)
            html = resp.get_data(as_text=True)
            self.assertIn('You already have a playlist with that name', html)


    def test_user_playlists(self):
        """Test the /users/<user_id>/playlists view route"""

        with self.client as client:
            # login user and create some playlists to use for test data
            data = {'username' : 'testuser1', 'password' : 'password1'}
            client.post('/login', data=data)
            client.post('/playlists/new', data={'name':'1playlist1', 'description':'1description1'})
            client.post('/playlists/new', data={'name':'2playlist2', 'description':'2description2'})
            data = {'username' : 'testuser2', 'password' : 'password2'}
            client.get('/logout')
            client.post('/login', data=data)
            client.post('/playlists/new', data={'name':'user2playlist', 'description':'user2description'})

            # Test GET /users/100/playlists. Should display user1's playlists and not user2s
            resp = client.get('users/100/playlists')
            html = resp.get_data(as_text=True)
            self.assertIn('1playlist1', html)
            self.assertIn('2playlist2', html)
            self.assertIn('1description1', html)
            self.assertIn('2description2', html)
            self.assertNotIn('user2playlist', html)
            self.assertNotIn('user2description', html)

            # Test trying to get playlists from a user that does not exist. Should redirect to /playlists and flash error
            resp = client.get('/users/50/playlists', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Could not find that user', html)
            
    def test_add_song(self):
        """Test the add_song route"""
        with self.client as client:
            # Test without user logged in. Should redirect and flash message:
            resp = client.post('/playlists/1/add/1', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('Log in to add songs', html)

            # Log in user, create some sample playlists and songs to work with:
            data = {'username' : 'testuser1', 'password' : 'password1'}
            client.post('/login', data=data)
            playlist = Playlist(id=100, name='playlist1', user_id=100, description='description')
            song1 = Song(id=100, post_id=100, post_title='test1', title='song1', artist='artist1', link='https://youtu.be/DLzxrzFCyOs')
            song2 = Song(id=200, post_id=200, post_title='test2', title='song2', artist='artist2', link='https://youtu.be/DLzxrzFCyOs')
            song3 = Song(id=300, post_id=300, post_title='test3', title='song3', artist='artist3', link='https://youtu.be/DLzxrzFCyOs')

            db.session.add(playlist)
            db.session.add(song1)
            db.session.add(song2)
            db.session.add(song3)
            db.session.commit()
            
            # Now test adding these songs to the playlist
            client.post('/playlists/100/add/100')
            client.post('/playlists/100/add/200')
            client.post('/playlists/100/add/300')
          
            
            songs = [song.id for song in Playlist.query.get(100).songs]
            song1 = Song.query.get(100)
            song2 = Song.query.get(200)
            song3 = Song.query.get(300)
            self.assertIn(song1.id, songs)
            self.assertIn(song2.id, songs)
            self.assertIn(song3.id, songs)
            
    
    def test_spotify_login(self):
        """Test the spotify login route"""
        with self.client as client:
            # Test without logged in user, should flash error message and redirect home
            resp = client.get('/spotify', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("<a href='/login'>Log in or create an account</a> first", html)
            # Log in user:
            data = {'username' : 'testuser1', 'password' : 'password1'}
            client.post('/login', data=data)

            # Test that the /spotify route redirects to the correct endpoint to log in with spotify
            resp = client.get('/spotify')
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, f'https://accounts.spotify.com/authorize?client_id={SPOTIPY_CLIENT_ID}&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fcallback&scope=playlist-modify-public&state=shdtehg32')


    def test_convert_playlist(self):
        """Test the convert playlist view route"""

        with self.client as client:
            # Test with no logged in user, should flash error and redirect
            resp = client.get('/playlists/1/spotify')
            self.assertEqual(resp.status_code, 302)
            resp = client.get('/playlists/1/spotify', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn('You must login to create spotify playlists!', html)








            


            


            




            




