from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

con = sqlite3.connect("ottertune.db", check_same_thread=False)
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS user(
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT, 
            password TEXT
            )""")

cid = os.getenv('SPOTIPY_CLIENT_ID')
secret = os.getenv('SPOTIPY_CLIENT_SECRET')
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager
=
client_credentials_manager)


app = Flask(__name__) 
boostrap = Bootstrap5(app)



# liking the song
cur.execute("""CREATE TABLE IF NOT EXISTS likedSongs(
            likeID INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER,
            songID INTEGER,
            songURL TEXT,
            FOREIGN KEY (userId) REFERENCES user(userId)
            )""")
con.commit() 

#search history later
# cur.execute("""CREATE TABLE IF NOT EXISTS searchHistory(
#           searchID INTEGER PRIMARY KEY AUTOINCREMENT,
#           userId INTEGER,
#           songSearched TEXT,
#           FOREIGN KEY (userId) REFERENCES user(userId)
#           )""")
# con.commit()


                
                

@app.route('/')
def index():

    # will use later for search history
    # userID = request.args.get('userId')
    # searchHistory = []

    # if userID:
    #     cur.execute("SELECT songSearched FROM searchHistory WHERE userId = ? LIMIT 10", (userID))
    #     searchHistory = cur.fetchall()

    return  render_template('index.html')
    #add it to render later searchHistory = searchHistory, userID = userID

@app.route('/signIn', methods=['GET', 'POST'])
def signIn():
    return  render_template('index.html')

@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    username = request.form['username']
    password = request.form['password']

    print(f"username: {username}")
    print(f"password: {password}")

    data = [(username, password)]
    cur.executemany("INSERT INTO user (username, password) VALUES(?, ?)", data)
    con.commit()

    print("all users in db:")
    for row in cur.execute("SELECT * FROM user"):
        print(row)

    return  render_template('index.html')

@app.route('/searchResults')
def searchResults():
    track = request.args.get('track')

    # will use later for the search history
    # userID = request.args.get('userId')
    
    # if track and userID: #WORK IN PROGRESS
    #     cur.execute("INSERT INTO searchHistory (userId, songSearched) VALUES (?,?)", (userID, track))
    #     con.commit()

    results = sp.search(q=track, type='track', limit=5)
    results = results['tracks']['items']
    return render_template('searchResults.html', results=results, track_name=track)



@app.route('/songInfo/<track_id>')
def song_info(track_id):
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    artistAlbums = sp.artist_albums(artist_id, album_type='album',limit=20)
    imageArtists = artist_info['images'][0]['url']

    
    return render_template("songInfo.html", track=track, artist_albums = artistAlbums['items'], artist_image = imageArtists)

@app.route('/likedSongs', methods =['POST'])
def likedSongs():
    userID = request.form['userId']
    songID = request.form['songID']
    songURL = request.form['songURL']
    print(f"userID: {userID}")
    print(f"songID: {songID}")
    print(f"songURL: {songURL}")
   

    # for database purposes so there's no duplicates
    cur.execute("SELECT * FROM likedSongs WHERE userId = ? AND songID = ? AND songURL = ?", (userID, songID, songURL))
    already_liked = cur.fetchone()

    if not already_liked:
        cur.execute("INSERT INTO likedSongs (userId, songID, songURL) VALUES (?,?,?)", (userID, songID, songURL))
        con.commit()

    #searched song
    track_query = request.form['trackQuery']
    return redirect(url_for('searchResults', track=track_query, userId=userID, liked=songID, message="Added to Liked Songs"))


#i need to figure out the user thing. Because right now im just liking the song but im not signed in yet
@app.route('/checkLikes')
def checkLikes():
    userID = request.args.get('userId')
    likedSongs = []

    if userID:
        cur.execute("SELECT songID, songURL FROM likedSongs WHERE userId = ?", (userID))
        likedSongs = cur.fetchall()

    return render_template('likedSongs.html', likedSongs =likedSongs, userID = userID)