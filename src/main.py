import logging
from logging import StreamHandler
from waitress import serve
from flask import Flask, request, jsonify, send_from_directory, send_file
import random
from services.spotify import SpotifyClient

app = Flask(__name__)

SPOTIFY_API_URL = "https://api.spotify.com/v1"

# Remove default logger handler
app.logger.handlers.clear()

# Add custom logging handler for Replit
handler = StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Log when the application starts
app.logger.info("Application started")

@app.route('/')
def index():
    return jsonify({"message": "Welcome to MelodyMate - a ChatGPT plugin for making playlists on Spotify"})

@app.route('/getImage')
def get_logo():
    filename = './static/logo.png'
    return send_file(filename, mimetype='image/png')

@app.route('/playlist', methods=['GET'])
def fetch_playlist():
    Test = SpotifyClient(SPOTIFY_API_URL, "abc")
    app.logger.info(Test.get_auth_header())
    app.logger.info("Creating a new playlist")
    query = request.args.get('query')
    auth_header = request.headers.get('Authorization')
    token = ""
    if auth_header is not None and auth_header.startswith('Bearer '):
        token = auth_header[7:]

    if token == "":
        return jsonify({"error":
                        "Please login to Spotify to generate a token"}), 400

    SpotifyCaller = SpotifyClient(SPOTIFY_API_URL, token)

    user_id = SpotifyCaller.get_user_id()

    if not user_id:
        return jsonify({"error": "Unable to get user id"}), 400
    if user_id[0] == "Fail":
        return jsonify({"error": user_id[1]}), 400


    playlist_ids = SpotifyCaller.get_playlists(query)

    if not playlist_ids:
        return jsonify({"error": "Unable to fetch playlists"}), 400
    if playlist_ids[0] == "Fail":
        return jsonify({"error": playlist_ids[1]}), 400

    track_results = SpotifyCaller.get_track_ids(playlist_ids)

    if not track_results:
        return jsonify({"error": "Unable to fetch track ids from playlists"}), 400
    if track_results[0] == "Fail":
        return jsonify({"error": track_results[1]}), 400

    seed_track = random.choice(track_results[0])

    track_ids_dict = {
        playlist_ids[i]: track_results[i]
        for i in range(len(playlist_ids))
    }

    audio_features = SpotifyCaller.get_audio_features(track_ids_dict)

    if not audio_features:
        return jsonify({"error": "Unable to audio features from tracks"}), 400
    if track_results[0] == "Fail":
        return jsonify({"error": audio_features[1]}), 400

    avg_audio_features = SpotifyCaller.get_avg_audio_features(audio_features)

    recommended_tracks = SpotifyCaller.get_recommended_tracks(
        avg_audio_features, seed_track)

    if not recommended_tracks:
        return jsonify({"error": "Unable to get recommended tracks"}), 400
    if recommended_tracks[0] == "Fail":
        return jsonify({"error": recommended_tracks[1]}), 400

    playlist_id, playlist_url = SpotifyCaller.create_playlist(user_id, query)

    if not playlist_id:
        return jsonify({"error": "Unable to create a playlist"}), 400
    if playlist_id[0] == "Fail":
        return jsonify({"error": playlist_id[1]}), 400

    final_result = SpotifyCaller.add_tracks_to_playlist(playlist_id,
                                                        recommended_tracks)

    if final_result[0] == "Fail":
        return jsonify({"error": "Unable to add tracks to the playlist"}), 400

    return jsonify({
        "message":
        "You have successfully added the playlist. Click the playlist_url to view it.",
        "playlist_url": playlist_url,
    })


@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
    app.logger.info("Serving ai-plugin.json")
    return send_from_directory('./static',
                                'ai-plugin.json',
                                mimetype='application/json')


@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
    app.logger.info("Serving openapi.yaml")
    return send_from_directory('./static', 'openapi.yaml', mimetype='text/yaml')


if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=8080)
