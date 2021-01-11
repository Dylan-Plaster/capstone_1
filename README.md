# capstone_1:
# ListenToThis Playlist
## This project is deployed at https://listen2thisplaylist.herokuapp.com
This website works with the reddit API to get posts from the r/ListenToThis subreddit, which describes itself as "the place to discover new and overlooked music". These posts are displayed on the homepage, where users can listen to the songs through embedded youtube videos. Logged in users can create playlists and add songs to them. These playlists can be listened to on the website, or converted to Spotify playlists via the Spotify API for listening on the go. Of course, not every artist is on Spotify, so if a song can't be found through the API's search function it will not show up in the Spotify version of the playlist. Once a Spotify version of a playlist has been created, users can also have a recommendation playlist created based on a playlist they crafted, which is automatically added to their Spotify account.

#### The standard user flow of this website is as follows:
- Create account/login
 - Link Spotify account (optional to create playlists)
 - Discover new music! Listen to new artists
 - Add your favorite songs to different playlists
 - Convert playlists to your Spotify account. Listen to them on your phone or other devices on the go!
 - Get recommendations based on the new music you've found!
 - View other users playlists to discover more!


The APIs used in this project are the Spotify and Reddit APIs: www.reddit.com and https://api.spotify.com . The Reddit API is used to fetch post data from the r/ListenToThis Subreddit, and the Spotify API is used to log in users and create playlists on their account. 
