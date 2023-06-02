import os
import logging
from logging import StreamHandler
from waitress import serve
from flask import Flask, request, session, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import urllib.parse
import random
import requests
import spotifyWrapper
import tokenHandler
from utility import generate_random_string, extract_code_from_url

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")
db = SQLAlchemy(app)
load_dotenv()

SPOTIFY_API_URL = "https://api.spotify.com/v1"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "user-read-private user-read-email playlist-read-private playlist-modify-public playlist-modify-private"

TokenCaller = tokenHandler.TokenHandler(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

# Remove default logger handler
app.logger.handlers.clear()

# Add custom logging handler for Replit
handler = StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Log when the application starts
app.logger.info("Application started")

class SpotifyTokens(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(), unique=True, nullable=False)
    access_token = db.Column(db.String(), nullable=False)
    refresh_token = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f'<User {self.user_id}>'

def handle_refresh_db(user_id, access_token, refresh_token):
    tokens = SpotifyTokens.query.filter_by(user_id=user_id).first()

    if not tokens:
        tokens = SpotifyTokens(user_id=user_id, access_token=access_token, refresh_token=refresh_token)
        db.session.add(tokens)
    else:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token

    db.session.commit()

@app.route('/callback')
def handle_redirect():
    code, state = extract_code_from_url(request.url)
    if code is None or state is None:
        return jsonify({"error": "No code/state parameter in URL"}), 400
    
    if state != session["state"]:
        return jsonify({"error": "The state does not match"}), 400
    
    TokenCaller.set_token(code)

    token, refresh_token = TokenCaller.get_token(), TokenCaller.get_refresh_token()
    headers = {
        "Authorization": "Bearer " + token
    }
    response = requests.get(SPOTIFY_API_URL + "/me", headers=headers)

    if response.status_code != 200:
        result = response.json()
        return jsonify({"error": result["error"]}), 400

    result = response.json()
    user_id = result["id"]
    session["user_id"] = user_id

    handle_refresh_db(user_id, token, refresh_token)

    return jsonify({
        "message": "The token was successfully captured",
        "user_id": user_id
    }), 200


@app.route('/login', methods=['GET'])
def login():
    app.logger.info("Requesting user authorization")
    state = generate_random_string(16)
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'redirect_uri': REDIRECT_URI,
        'state': state
    }
    session["state"] = state

    url = SPOTIFY_AUTH_URL + '?' + urllib.parse.urlencode(params)
    return redirect(url, code=302)

@app.route('/index')
def start_session():
    user_id = session.get("user_id")
    tokens = SpotifyTokens.query.filter_by(user_id=user_id).first()

    if tokens:
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        tokens.access_token = new_token
        tokens.refresh_token = refresh_token
        db.session.commit()
        return jsonify({"message": "Session started with existing tokens"}), 200
    
    return redirect("https://melody-mate.victorchan88.repl.co/login")


@app.route('/playlist', methods=['GET'])
def fetch_playlist():
    app.logger.info("Creating a new playlist")
    query = request.args.get('query')

    # user_id = session.get("user_id")
    # tokens = SpotifyTokens.query.filter_by(user_id=user_id).first()
    # token = tokens.access_token

    token = TokenCaller.get_token()

    if token == "":
        return jsonify({"error": "Please login to Spotify to generate a token"}), 400

    SpotifyCaller = spotifyWrapper.SpotifyWrapper(SPOTIFY_API_URL, token)

    user_id = SpotifyCaller.get_user_id()

    if not user_id:
        return jsonify({"error": "Unable to get user id"}), 400
    if user_id[0] == "Fail":
        return jsonify({"error": user_id[1]}), 400
    if user_id[0] == "401":
        app.logger.info("Refreshing token")
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        user_id = SpotifyCaller.get_user_id()
        handle_refresh_db(user_id, new_token, refresh_token)
    

    playlist_ids = SpotifyCaller.get_playlists(query)

    if not playlist_ids:
        return jsonify({"error": "Unable to fetch playlists"}), 400
    if playlist_ids[0] == "Fail":
        return jsonify({"error": playlist_ids[1]}), 400
    if playlist_ids[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        playlist_ids = SpotifyCaller.get_playlists(query)
        handle_refresh_db(user_id, new_token, refresh_token)

    track_results = SpotifyCaller.get_track_ids(playlist_ids)

    if not track_results:
        return jsonify({"error": "Unable to fetch track ids from playlists"}), 400
    if track_results[0] == "Fail":
        return jsonify({"error": track_results[1]}), 400
    if track_results[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        track_results = SpotifyCaller.get_track_ids(playlist_ids)
        handle_refresh_db(user_id, new_token, refresh_token)
    
    seed_track = random.choice(track_results[0])

    track_ids_dict = {playlist_ids[i]: track_results[i] for i in range(len(playlist_ids))}

    audio_features = SpotifyCaller.get_audio_features(track_ids_dict)

    if not audio_features:
        return jsonify({"error": "Unable to audio features from tracks"}), 400
    if track_results[0] == "Fail":
        return jsonify({"error": audio_features[1]}), 400
    if track_results[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        audio_features = SpotifyCaller.get_audio_features(track_ids_dict)
        handle_refresh_db(user_id, new_token, refresh_token)

    avg_audio_features = SpotifyCaller.get_avg_audio_features(audio_features)
    
    recommended_tracks = SpotifyCaller.get_recommended_tracks(avg_audio_features, seed_track)

    if not recommended_tracks:
        return jsonify({"error": "Unable to get recommended tracks"}), 400
    if recommended_tracks[0] == "Fail":
        return jsonify({"error": recommended_tracks[1]}), 400
    if recommended_tracks[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        recommended_tracks = SpotifyCaller.get_recommended_tracks(avg_audio_features, seed_track)
        handle_refresh_db(user_id, new_token, refresh_token)
            
    playlist_id, playlist_url = SpotifyCaller.create_playlist(user_id, query)

    if not playlist_id:
        return jsonify({"error": "Unable to create a playlist"}), 400
    if playlist_id[0] == "Fail":
        return jsonify({"error": playlist_id[1]}), 400
    if playlist_id[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        playlist_id, playlist_url = SpotifyCaller.create_playlist(user_id, query)
        handle_refresh_db(user_id, new_token, refresh_token)

    final_result = SpotifyCaller.add_tracks_to_playlist(playlist_id, recommended_tracks)

    if final_result[0] == "Fail":
        return jsonify({"error": "Unable to add tracks to the playlist"}), 400
    if final_result[0] == "401":
        TokenCaller.set_refresh_token()
        new_token = TokenCaller.get_token()
        refresh_token = TokenCaller.get_refresh_token()
        SpotifyCaller.set_token(new_token)
        final_result = SpotifyCaller.add_tracks_to_playlist(playlist_id, recommended_tracks)
        handle_refresh_db(user_id, new_token, refresh_token)

    return jsonify({
        "message": "You have successfully added the playlist. Click the playlist_url to view it.",
        "playlist_url": playlist_url,
    })

@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
    app.logger.info("Serving ai-plugin.json")
    return send_from_directory('.',
                                'ai-plugin.json',
                                mimetype='application/json')

@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
    app.logger.info("Serving openapi.yaml")
    return send_from_directory('.', 'openapi.yaml', mimetype='text/yaml')

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
