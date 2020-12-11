# Capstone project proposal

 My capstone project will be a Flask-SQLAlchemy app hosted on Heroku. The website will display posts from the r/ListenToThis subreddit, which describes itself as "The place to discover new and overlooked music". Users will be able to sort the posts by reddit's sorting methods, and choose a post to listen to. The song will play without leaving the website, and the user will have an option to rate the song, add it to a playlist, and view the poster's post history. The user can then log in to their spotify and add their custom playlist to their spotify account for later listening. Once the user has added a few songs to the playlist, they can view a list of recommended songs based on their ratings of similar music. 

 The website is designed to help users find new music they would have otherwise overlooked or not discovered. The user is someone who loves music, but finds themselves stuck listening to the same bands and wants to branch out. 

 This app will use data from the Reddit API and the Spotify API. The reddit API will be used to fetch the posts from the subreddit, which will contain information about the song as well as a link to listen to it. The Spotify API will be used to login to the user's account, create playlists, and get recommendations based on a list of liked songs. 

 The database schema will require a table to keep track of users, with their username, hashed password, spotify token, and a reference to the playlists table stored. The playlist table will store the name of the playlist and a reference to a table with the track listing of that playlist. The user's spotify token and password need to be secured so that the end user can not see either of these values. 

 It may be difficult to reliably take the song title and artist name from the reddit post and find the correct song on Spotify. This could be because of an error in the title or because the artist's music is not on spotify. In this case, the app will display spotify search results to the user to see if they can find it. 

+ Functionalities include: 
	+ ability to listen to the song on the webpage without opening a new tab or window
	+  ability to sort the posts by reddit's sorting methods e.g: hot, new, top of the week/month, etc
	+   ability to save a song/post to a playlist
	+    ability to rate songs after listening to tune recommendations
	+     ability to turn playlists into spotify playlists
	+      ability to recommend new songs to the user based on their custom playlist and the song ratings they give. 
	+      ability to create a pdf/image of a playlist and post it to instagram

 The general user flow will start with logging in or creating a new user account. Then users will see a feed of posts from the reddit API. They will listen to a song, then rate it up or down. They can click a button to add this song to one of their playlists. After adding a few songs to a particular playlist, they can view recommendations based off that playlist and the user's ratings. They can then sign into their spotify, and copy their custom playlist over to their spotify account for later listening. The recommendation feature is what makes this app more than just simple CRUD.