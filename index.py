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

app.config["SESSION_PERMANENT"] = False 
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# liking the song
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

cur.execute("""CREATE TABLE IF NOT EXISTS playlist (
            playlistId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            userId INTEGER,
            desc TEXT,
            FOREIGN KEY (userId) REFERENCES user(userId) ON DELETE CASCADE
            )""")

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

cur.execute("""CREATE TABLE IF NOT EXISTS playlistSongs (
            playlistId INTEGER,
            songId TEXT,
            PRIMARY KEY (playlistId, songId),
            FOREIGN KEY (playlistId) REFERENCES playlist(playlistId) ON DELETE CASCADE
            )""")
            # FOREIGN KEY (songId) REFERENCES song(songId) ON DELETE CASCADE
con.commit() 

#search history later
cur.execute("""CREATE TABLE IF NOT EXISTS searchHistory(
          searchID INTEGER PRIMARY KEY AUTOINCREMENT,
          userId INTEGER,
          songSearched TEXT,
          FOREIGN KEY (userId) REFERENCES user(userId)
          )""")
con.commit()


                
                

@app.route('/')
def index():

    # will use later for search history
    # userID = request.args.get('userId') #add the session thing
    # searchHistory = []
   
    # if userID:
    #     cur.execute("SELECT songSearched FROM searchHistory WHERE userId = ? LIMIT 10", (userID))
    #     searchHistory = cur.fetchall()


    # will use later for the search history
    userID = session.get("userId") 
    track = request.args.get('track')
    
    #add to search history
    # if track and userID: 
    #     cur.execute("INSERT INTO searchHistory (userId, songSearched) VALUES (?,?)", (userID, track))
    #     con.commit()


    cur.execute("SELECT songSearched FROM searchHistory WHERE userId = ? ORDER BY searchID DESC LIMIT 10", (userID,))
    search_history = cur.fetchall()   

    print("in /")
    print(session.get("userId"))
    print(session.get("username"))
    if session.get("userId") is not None and session.get("username") is not None:
        return render_template('index.html', track_name=track, search_history = search_history)

    return  render_template('landing.html')
    #add it to render later searchHistory = searchHistory, userID = userID

@app.route('/profile')
def profile():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')

    return  render_template('profile.html')


@app.route('/signIn', methods=['GET', 'POST'])
def signIn():

    print("session userId: ",  session.get("userId"))
    print("session username: ",  session.get("username"))

    if session.get("userId") is not None and session.get("username") is not None:
        return render_template('index.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return redirect("/")


    username = request.form['username']
    password = request.form['password']

    print("username passed in: ", username)
    res = cur.execute("SELECT * FROM user WHERE username = ?", (username,))
    userData = res.fetchone()
    print(userData)

    if userData is None or userData[2] != password:
        print(" is none or password is wrong")
        # return render_template('landing.html')
        return redirect('/')
    
    session["userId"] = userData[0]
    session["username"] = userData[1]
    
    print(userData[0])
    print(session.get("userId"))
    print(session.get("username"))

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

    res = cur.execute("SELECT * FROM user WHERE username = ?", (username,))
    userData = res.fetchone()
    print(userData)

    session["userId"] = userData[0]
    session["username"] = userData[1]

    return  redirect('/')

@app.route("/logout")
def logout():
    session["userId"] = None
    session["username"] = None
    return redirect("/")

@app.route('/searchResults')
def searchResults():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    track = request.args.get('track')


    # # will use later for the search history
    userID = session.get("userId") 
    
    # #add to search history
    if track and userID: 
        cur.execute("INSERT INTO searchHistory (userId, songSearched) VALUES (?,?)", (userID, track))
        con.commit()


    # cur.execute("SELECT songSearched FROM searchHistory WHERE userId = ? ORDER BY searchID DESC LIMIT 5", (userID,))
    # search_history = cur.fetchall()   

    results = sp.search(q=track, type='track', limit=6)
    results = results['tracks']['items']
    # print(results)
    return render_template('searchResults.html', results=results, track_name=track)



@app.route('/songInfo/<track_id>')
def song_info(track_id):
    track = sp.track(track_id)
    artist_id = track['artists'][0]['id']
    artist_info = sp.artist(artist_id)
    artistAlbums = sp.artist_albums(artist_id, album_type='album',limit=20)
    imageArtists = artist_info['images'][0]['url']

    
    return render_template("songInfo.html", track=track, artist_albums = artistAlbums['items'], artist_image = imageArtists)

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
    
    # no duplicates
    cur.execute("SELECT * FROM likedSongs WHERE userId = ? AND songID = ? AND songURL = ?", (userID, songID, songURL))
    already_liked = cur.fetchone()

    if not already_liked:
       
        cur.execute("INSERT INTO likedSongs (userId, songID, songURL, imageURL, songName) VALUES (?,?,?,?,?)", (userID, songID, songURL, imageURL, songName))
        con.commit()


    track_query = request.form['trackQuery']
    return redirect(url_for('searchResults', track=track_query, userId=userID, liked=songID, message="Added to Liked Songs"))



#i need to figure out the user thing. Because right now im just liking the song but im not signed in yet
@app.route('/checkLikes')
def checkLikes():


    userID = session.get("userId")
    track = request.args.get('track')
    likedSongs = []

    test = cur.execute("SELECT * FROM likedSongs WHERE userId = ?", (userID,))
    test = cur.fetchall()
    print("checkLiked data: ", test)

    print("userId in checkLikes: ", userID)

    if userID:
        cur.execute("SELECT songID, songURL, imageURL, songName FROM likedSongs WHERE userId = ?", (userID,))
        likedSongs = cur.fetchall()
        
        print("Liked songs: ", likedSongs)


    return render_template('likedSongs.html', likedSongs =likedSongs, userID = userID)


@app.route('/playlists')
def playlists():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    

    userId = session.get("userId")
    
    cur.execute("SELECT * FROM playlist WHERE userId = ?", (userId,))
    playlists = cur.fetchall()
    print(playlists)
    
    return render_template("playlists.html", playlists=playlists)

@app.route('/createPlaylist', methods =['POST'])
def createPlaylist():
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    print("in create playlist route")
    name = request.form.get('name')
    desc = request.form.get('desc')
    userId = session.get("userId")

    data = [(userId, name, desc)]
    cur.executemany("INSERT INTO playlist (userId, name, desc) VALUES(?, ?, ?)", data)
    con.commit()


    print(name)
    print(desc)
    return redirect("/playlists")

@app.route('/random_playlist')
def random_playlist():
    # checks if user is logged in
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    
    # renders the random playlist page
    return render_template('random_playlist.html')

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

    # search using spotify api
    results = sp.search(q=search_term, type='track', limit=6)
    results = results['tracks']['items']

    # renders the results of questionnaire
    return render_template('random_playlist_results.html', results=results, track_name=search_term)

@app.route('/save_random_playlist')
def save_random_playlist():
    # checks if user is logged in
    if session.get("userId") is None or session.get("username") is None:
        return redirect('/')
    
    # gets songs from random playlist
    songs = []
    song1 = request.args.get('song1')
    songs.append(song1)
    song2 = request.args.get('song2')
    songs.append(song2)
    song3 = request.args.get('song3')
    songs.append(song3)
    song4 = request.args.get('song4')
    songs.append(song4)
    song5 = request.args.get('song5')
    songs.append(song5)
    song6 = request.args.get('song6')
    songs.append(song6)

    # user inputted name and description for playlist
    name = request.args.get('playlist_name')
    desc = request.args.get('playlist_desc')
    userId = session.get("userId")

    # protection against sql injection
    data = [(userId, name, desc)]
    # save new playlist into database
    cur.executemany("INSERT INTO playlist (userId, name, desc) VALUES(?, ?, ?)", data)
    con.commit()

    # get's the ID of the recently created playlist
    cur.execute("SELECT playlistId FROM playlist WHERE userId = ? AND name = ? AND desc = ?", (userId, name, desc))
    playlistId = cur.fetchall()

    # converts tuple to string
    playlistId = str(playlistId[0])
    # removes "(" and ",)" from string
    playlistId = playlistId.replace("(", "")
    playlistId = playlistId.replace(",)", "")
    # converts string to int
    playlistId = int(playlistId)

    # loops all the songs into the recently created playlist
    for song in songs:
        data = [(playlistId, song)]
        cur.executemany("INSERT INTO playlistSongs (playlistId, songId) VALUES(?, ?)", data)
        con.commit()

    # redirects to playlists page
    return redirect('/playlists')
