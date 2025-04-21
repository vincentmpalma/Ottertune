from flask import Flask, render_template, request
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


@app.route('/')
def index():
    return  render_template('landing.html')

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
    results = sp.search(q=track, type='track', limit=5)
    results = results['tracks']['items']
    return render_template('searchResults.html', results=results, track=track)

@app.route('/songInfo/<track_id>')
def song_info(track_id):
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    artistAlbums = sp.artist_albums(artist_id, album_type='album',limit=20)
    imageArtists = artist_info['images'][0]['url']

    
    return render_template("songInfo.html", track=track, artist_albums = artistAlbums['items'], artist_image = imageArtists)

