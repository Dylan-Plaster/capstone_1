from flask_spotify_auth import getAuth, refreshAuth, getToken

SECRET_KEY = '9890Secret_key_hidden_from_user0923'

#Add your client ID
CLIENT_ID = "07050efdb1e8469187a4cb88f9388020"

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = "b63521b241914810aa562f96083717a2"

#Port and callback url can be changed or ledt to localhost:5000
PORT = "5000"
CALLBACK_URL = "http://localhost"

#Add needed scope from spotify user
SCOPE = "playlist-modify-private streaming playlist-read-private playlist-modify-public user-modify-playback-state"
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown 
TOKEN_DATA = []


def getUser():
    return getAuth(CLIENT_ID, "{}:{}/callback/".format(CALLBACK_URL, PORT), SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, "{}:{}/callback/".format(CALLBACK_URL, PORT))
 
def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA



print('**************************************************************************')
print(getAccessToken())
