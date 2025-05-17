# Imports needed and app configuration
from flask import Flask, render_template, request, redirect, url_for, session
from flask_bootstrap import Bootstrap5
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import sqlite3
import random

load_dotenv()

#SQLite database setup
con = sqlite3.connect("ottertune.db", check_same_thread=False)
cur = con.cursor()
#Users table for account info
cur.execute("""CREATE TABLE IF NOT EXISTS user(
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, 
            password TEXT
            )""")

#Spotify API Setup
cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager
=
client_credentials_manager)

#Flask App Setup
app = Flask(__name__) 
boostrap = Bootstrap5(app)

app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# database table for when a user like a song
cur.execute("""DROP TABLE IF EXISTS likedSongs""") # delete this 
cur.execute("""CREATE TABLE IF NOT EXISTS likedSongs(
            likeID INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            songID TEXT,
            songURL TEXT,
            imageURL TEXT,
            songName TEXT,
            FOREIGN KEY (userId) REFERENCES user(userId)
            )""")

#database table to store user's playlist
cur.execute("""CREATE TABLE IF NOT EXISTS playlist (
            playlistId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            userId INTEGER,
            desc TEXT,
            FOREIGN KEY (userId) REFERENCES user(userId) ON DELETE CASCADE
            )""")

#song table 
cur.execute("""
CREATE TABLE IF NOT EXISTS song (
    songId TEXT PRIMARY KEY,
    artistId TEXT,
    albumId TEXT,
    image TEXT,
    artist TEXT,
    album TEXT,
    link TEXT,
    score INTEGER,
    explicit INTEGER,
    duration INTEGER
)
""")


#playlistSongs Table that joins playlists and songs tables
cur.execute("""CREATE TABLE IF NOT EXISTS playlistSongs (
            playlistId INTEGER,
            songId TEXT,
            songName TEXT,
            artistName TEXT,
            imageURL TEXT,
            songURL TEXT,
            PRIMARY KEY (playlistId, songId),
            FOREIGN KEY (playlistId) REFERENCES playlist(playlistId) ON DELETE CASCADE
            )""")
            # FOREIGN KEY (songId) REFERENCES song(songId) ON DELETE CASCADE
con.commit() 

#logs the user's search input
cur.execute("""CREATE TABLE IF NOT EXISTS searchHistory(
          searchID INTEGER PRIMARY KEY AUTOINCREMENT,
          userId INTEGER,
          songSearched TEXT,
          FOREIGN KEY (userId) REFERENCES user(userId)
          )""")
con.commit()


                
#Vincent Palma         
#home page
@app.route('/')
def index():

    userID = session.get("userId") 
    track = request.args.get('track')
    
    # this the user to see their 10 most recent search history entries
    cur.execute("SELECT songSearched FROM searchHistory WHERE userId = ? ORDER BY searchID DESC LIMIT 10", (userID,))
    search_history = cur.fetchall()   

    print("in /")
    print(session.get("userId"))
    print(session.get("username"))
    #after logging in, it goes to the main page and the user should also be able to see their search history
    if session.get("userId") is not None and session.get("username") is not None:
        return render_template('index.html', track_name=track, search_history = search_history)

    return  render_template('landing.html')

#profile page
@app.route('/profile')
def profile():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

    return  render_template('profile.html')



#Vincent Palma
#user sign in
@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    print("session userId: ",  session.get("userId"))
    print("session username: ",  session.get("username"))

  
    #goes to the main page after logging in
    if session.get("userId") is not None and session.get("username") is not None:
        return render_template('index.html')
    
    #user credentials
    username = request.form.get('username')
    password = request.form.get('password')
    
    #wrong credentials
    if not username or not password:
        return redirect("/")

    #retrieve user from database
    username = request.form['username']
    password = request.form['password']
    print("username passed in: ", username)
    res = cur.execute("SELECT * FROM user WHERE username = ?", (username,))
    userData = res.fetchone()
    print(userData)

    #check if user exists and password matches
    if userData is None or userData[2] != password:
        print(" is none or password is wrong")
        return redirect('/')
    
    #set session variables
    session["userId"] = userData[0]
    session["username"] = userData[1]
    
    print(userData[0])
    print(session.get("userId"))
    print(session.get("username"))

    #after successful login
    return render_template('index.html')

#Vincent Palma
#for creating an account
@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    #user credentials
    username = request.form['username']
    password = request.form['password']

    print(f"username: {username}")
    print(f"password: {password}")

    #inserts new user into the database
    data = [(username, password)]
    cur.executemany("INSERT INTO user (username, password) VALUES(?, ?)", data)
    con.commit()

     #retrieve the newly created user data
    res = cur.execute("SELECT * FROM user WHERE username = ?", (username,))
    userData = res.fetchone()
    print(userData)

    #initialize session with new user's info
    session["userId"] = userData[0]
    session["username"] = userData[1]

    #after successfully signing up
    return  redirect('/')

#logging out
@app.route("/logout")
def logout():
    session["userId"] = None
    session["username"] = None
    return redirect("/")

#Vincent Palma
#handles track search
@app.route('/searchResults')
def searchResults():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    track = request.args.get('track')


  
    userID = session.get("userId") 
    
    #Janniel Tan
    #adding the track to seachHistory table
    if track and userID: 
        cur.execute("INSERT INTO searchHistory (userId, songSearched) VALUES (?,?)", (userID, track))
        con.commit()


    # Search for tracks using Spotify API
    results = sp.search(q=track, type='track', limit=6) #limited to 6 results for design purposes
    results = results['tracks']['items']
    # print(results)

    #retrieve user's playlists from the database
    userPlaylists = cur.execute("SELECT * FROM playlist WHERE userId = ?", (userID,))
    playlists = userPlaylists.fetchall()
    print("playlists for this user : ", playlists)
    #render search results page with track results and playlists
    return render_template('searchResults.html', results=results, track_name=track, playlists=playlists)



# Prabjot Pannu
# Grabbed track_id from Spotify's API whenever a user clicks on Info button
@app.route('/songInfo/<track_id>')
# Using track_id we can display content using the documentation from Spotipy

def song_info(track_id):
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    artistAlbums = sp.artist_albums(artist_id, album_type='album',limit=20)
    imageArtists = artist_info['images'][0]['url']
    topTracks = sp.artist_top_tracks(artist_id, country='US')
    # Rendered page songInfo and values
    return render_template("songInfo.html", track=track, artist_albums = artistAlbums['items'], artist_image = imageArtists, tracks = topTracks['tracks'])

#Janniel Tan
#handles liking a song
@app.route('/likedSongs', methods=['POST'])
def likedSongs():
    userID = session.get("userId")
    songID = request.form['songID']
    songURL = request.form['songURL']
    imageURL = request.form['imageURL']
    songName = request.form['songName']
    print(f"userID: {userID}")
    print(f"songID: {songID}")
    print(f"songURL: {songURL}")
    
    # this is to check if the song is already liked by the user to avoid duplicates
    cur.execute("SELECT * FROM likedSongs WHERE userId = ? AND songID = ? AND songURL = ?", (userID, songID, songURL))
    already_liked = cur.fetchone()

    if not already_liked:
        #insert the liked song into the database
        cur.execute("INSERT INTO likedSongs (userId, songID, songURL, imageURL, songName) VALUES (?,?,?,?,?)", (userID, songID, songURL, imageURL, songName))
        con.commit()


    track_query = request.form['trackQuery']
    return redirect(url_for('searchResults', track=track_query, userId=userID, liked=songID, message="Added to Liked Songs"))


#Janniel Tan
#to display all songs liked by the current user
@app.route('/checkLikes')
def checkLikes():


    userID = session.get("userId")
    track = request.args.get('track')
    likedSongs = []

    #fetch all liked songs for the user
    test = cur.execute("SELECT * FROM likedSongs WHERE userId = ?", (userID,))
    test = cur.fetchall()
    print("checkLiked data: ", test)

    print("userId in checkLikes: ", userID)

    #getting the liked songs and display the details
    if userID:
        cur.execute("SELECT songID, songURL, imageURL, songName FROM likedSongs WHERE userId = ?", (userID,))
        likedSongs = cur.fetchall()
        
        print("Liked songs: ", likedSongs)


    return render_template('likedSongs.html', likedSongs =likedSongs, userID = userID)

#Vincent Palma
#route to display all playlists of the user along with their songs
@app.route('/playlists')
def playlists():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

    userId = session.get("userId")

    #get all playlists for the user
    cur.execute("SELECT * FROM playlist WHERE userId = ?", (userId,))
    playlists = cur.fetchall()

    
    playlist_data = []
    #for each playlist, get its details and the songs it contains
    for playlist in playlists:
        playlist_id = playlist[0]
        playlist_name = playlist[1]
        playlist_desc = playlist[3]

       
        cur.execute("""
            SELECT songId, songName, artistName, imageURL, songURL
            FROM playlistSongs
            WHERE playlistId = ?
        """, (playlist_id,))
        songs = cur.fetchall()
        #add playlist and its songs to the list
        playlist_data.append({
            "id": playlist_id,
            "name": playlist_name,
            "desc": playlist_desc,
            "songs": songs
        })
    #render playlists.html with all playlists and their songs
    return render_template("playlists.html", playlist_data=playlist_data)


#Vincent Palma
#Creating a playlist for the user
@app.route('/createPlaylist', methods =['POST'])
def createPlaylist():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    print("in create playlist route")

    #getting the playlist name and description from form
    name = request.form.get('name')
    desc = request.form.get('desc')
    userId = session.get("userId")
    #inserting new playlist into the database
    data = [(userId, name, desc)]
    cur.executemany("INSERT INTO playlist (userId, name, desc) VALUES(?, ?, ?)", data)
    con.commit()


    print(name)
    print(desc)
    #redirect to playlists page after creation
    return redirect("/playlists")

# Angel Valdez
@app.route('/random_playlist')
def random_playlist():
   # checks if user is logged in
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    
   # renders the random playlist page
    return render_template('random_playlist.html')

# Angel Valdez
@app.route('/random_playlist_results')
def random_playlist_results():
    # checks if user is logged in
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

    # random word for search
    random_word = ['nifty', 'addicted', 'entire', 'heavenly', 'didactic',
        'exotic', 'ablaze', 'cultural', 'receptive', 'complete',
        'kindly', 'eatable', 'early', 'fuzzy', 'violet',
        'glorious', 'barbarous', 'chivalrous', 'sharp', 'right']
    # is randomized before selected
    random.shuffle(random_word)

    # user's responses for random playlist
    mood = request.args.get('mood')
    travel = request.args.get('travel')
    hobby = request.args.get('hobby')

    # combined for search
    search_term = f'{travel} {hobby} {mood} {random_word[0]}'

    
    results = sp.search(q=search_term, type='track', limit=6)
    results = results['tracks']['items']

    # renders the results of questionnaire
    return render_template('random_playlist_results.html', results=results, track_name=search_term)

# Angel Valdez
@app.route('/save_random_playlist', methods=['POST'])
def save_random_playlist():
    # checks if user is logged in
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

# user inputted name and description for playlist
    userId = session.get("userId")
    name = request.form.get('playlist_name')
    desc = request.form.get('playlist_desc')

    # save new playlist into database
    print("name of playlist is :", name )

    # get's the ID of the recently created playlist
    cur.execute("INSERT INTO playlist (userId, name, desc) VALUES (?, ?, ?)", (userId, name, desc))
    con.commit()

   # get's the ID of the recently created playlist
    cur.execute("SELECT last_insert_rowid()")
    playlistId = cur.fetchone()[0]

     # loops all the songs into the recently created playlist
    for i in range(6):
            song_id = request.form.get(f'song{i}')
            song_name = request.form.get(f'songName{i}')
            artist_name = request.form.get(f'artistName{i}')
            image_url = request.form.get(f'imageURL{i}')
            song_url = request.form.get(f'songURL{i}')

            print(f"\nSong {i}:")
            print(f"  ID: {song_id}")
            print(f"  Name: {song_name}")
            print(f"  Artist: {artist_name}")
            print(f"  Image URL: {image_url}")
            print(f"  Spotify URL: {song_url}")
    # inserts song info into recently created playlist
            if song_id:  
                cur.execute("""
                    INSERT INTO playlistSongs (playlistId, songId, songName, artistName, imageURL, songURL)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (playlistId, song_id, song_name, artist_name, image_url, song_url))
    con.commit()
 # redirects to playlists page
    return redirect('/playlists')



#Vincent Palma
#adding songs to the playlist 
@app.route('/addSongToPlaylist', methods=['POST'])
def addSongToPlaylist():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

    #getting song and playlist info from the form
    playlistId = request.form.get('playlistId')
    songId = request.form.get('songId')
    songName = request.form.get('songName')
    artistName = request.form.get('artistName')
    imageURL = request.form.get('imageURL')
    songURL = request.form.get('songURL')
    trackQuery = request.form.get('trackQuery')

    print(f"Adding song to playlist {playlistId}:")
    print(f"  ID: {songId}")
    print(f"  Name: {songName}")
    print(f"  Artist: {artistName}")
    print(f"  Image: {imageURL}")
    print(f"  URL: {songURL}")

    # Prevent duplicates of adding the same song to the playlist
    cur.execute("SELECT * FROM playlistSongs WHERE playlistId = ? AND songId = ?", (playlistId, songId))
    exists = cur.fetchone()
    
    #Add the song to the playlist   
    if not exists:
        cur.execute("""
            INSERT INTO playlistSongs (playlistId, songId, songName, artistName, imageURL, songURL)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (playlistId, songId, songName, artistName, imageURL, songURL))
        con.commit()

    return redirect(url_for('searchResults', track=trackQuery, added=songId, message="Added to Playlist"))


