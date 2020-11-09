# Capstone Project Proposal   

####My idea is an app that will work with both the Reddit and Spotify APIs to make discovering new music and adding it to your Spotify playlists easier.   

The website will get posts from the r/ListenToThis subreddit, which is a sub dedicated to posting lesser-known or overlooked artists. This makes it an ideal music subreddit to choose, as users are less likely to have already heard songs posted here. These posts will be displayed on the website, where users can sort them in the same ways they do on reddit (i.e. sort by new/hot/top of the week/etc), and listen to the songs through their spotify account or youtube. After listening to each song, users will rate the song out of 5 stars, and have options to add the song to a custom Spotify playlist created by the app, and to save the song in the user's profile. Once the user has added several songs to the custom playlist, the app will make recommendations of new music to listen to, weighted based on the user's rating of each song. The benefit of this app is that it provides a centralized place to discover new songs, get recommendations, and create spotify playlists. 



####1. What goal will your website be designed to achieve?


+ The website will be designed to help users find new music they like and would otherwise have not discovered. 

####2. What kind of users will visit your site? In other words, what is the demographic of your users?

+ The target user is someone who loves music, but finds they often get stuck listening to the same bands and songs they already know. They know they want to branch out and listen to new music but find it hard to discover new artists. The rating system on the website should make the recommendations more accurate 

####3.What data do you plan on using? You may have not picked your actual API yet, which is fine, just outline what kind of data you would like it to contain.

+ The data for this app will come from both the reddit and the spotify APIs. The reddit api will provide posts, which have the song name and artist name in a specified format. The spotify api will provide lots of information about each individual song as well as providing information about the user's playlists. When creating a list of recommendations for the user, the spotify api will provide song data like genre, danceability, liveness, acousticness, and other stats which can be used to help tailor the recommendations made to the user

####4.  In brief, outline your approach to creating your project (knowing that you may not know everything in advance and that these details might change later). Answer questions like the ones below, but feel free to add more information: 

####a. What does your database schema look like?

+ The database schema would include a table for a user, including an id, spotify token credentials, and a reference to a playlists table. The playlist table will have a name of the playlist, and a reference to a table which has a track listing for the playlist. 

####b. What kinds of issues might you run into with your API?

+ It may be difficult to take the song title and artist and reliably convert it to a spotify track id, which can then be used to get info about each track. I need to do more research into this part.


####c. Is there any sensitive information you need to secure?

+ The user's spotify login token/credentials will need to be secured, and I will need to use spotify's auth flows to have the user login on spotify's website, so the password is never seen by the app.

####d. What functionality will your app include?


+ Functionalities include: 
	+ ability to listen to the song on the webpage without opening a new tab or window
	+  ability to sort the posts by reddit's sorting methods e.g: hot, new, top of the week/month, etc
	+   ability to save a song/post to a different tab or section of the website for later listening
	+    ability to rate songs after listening to tune recommendations
	+     ability to click a button on a post to add it to a custom spotify playlist
	+      ability to recommend new songs to the user based on their custom playlist and the song ratings they give. 


####e. What will the user flow look like?

+ The user will first be prompted to login to their spotify account through spotify's interface. Then, they will be able to view the posts from the r/ListenToThis subreddit, choosing the sorting method they prefer. They can click on a song to listen to it, and after listening they have the option to rate the song out of 5 stars if they wish. On each post will be a "add to custom playlist" button, which will create a new spotify playlist on the user's account if it is their first time, and then add each song to the playlist. After the user has added a certain number of songs, the app will then create a list of personalized recommendations based on the genre and other stats provided about each track from spotify

####f. What features make your site more than CRUD? Do you have any stretch goals? 
+ The recommendation feature of the app makes it more than just simple CRUD and should provide a good challenge to do successfully. My stretch goal is to get the song from the reddit post to be added directly to the playlist without the user having to select it from a search box, but this may prove difficult with lesser known artists or duplicate song titles.