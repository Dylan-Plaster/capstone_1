from unittest import TestCase
import os
from models import db, User, Song, Playlist, Playlist_Song
from app import *
from flask import session

os.environ['DATABASE_URL'] = "postgresql:///L2T_test"
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

       
        # db.drop_all()
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

        db.session.commit()


    def tearDown(self):

        db.session.commit()
        db.session.close_all()
        db.drop_all()
     
  
    

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

    def test_new_playlist(self):
        """Test the /playlists/new route"""

        with self.client as client:
            # Test GET /playlists/new with no user logged in:
            resp = client.get('/playlists/new', follow_redirects=True)
            html = resp.get_data(as_text=True)
            # Should flash error message:
            self.assertIn('You must be logged in to create a playlist!', html)

            # Now, login a user, test again. Should render new playlist form:
            


            




            




