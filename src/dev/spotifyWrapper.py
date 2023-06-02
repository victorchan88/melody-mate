import requests

class SpotifyWrapper:
    def __init__(self, spotifyApiUrl, token):
        self.spotify_api_url = spotifyApiUrl
        self.token = token
    
    def get_auth_header(self):
        return {
            "Authorization": "Bearer " + self.token
        }
    
    def post_auth_header(self):
        return {
            "Authorization": "Bearer " + self.token,
            "Content-Type": "application/json",
        }
    
    def set_token(self, token):
        self.token = token
    
    def get_playlists(self, query):
        headers = self.get_auth_header()
        params = {
            "q": query,
            "type": "playlist",
            "limit": 5,
        }
        response = requests.get(self.spotify_api_url + "/search", headers=headers, params=params)

        if response.status_code == 401:
            return ["401"]
        if response.status_code != 200:
            result = response.json()
            return ["Fail", result["error"]]

        result = response.json()
        playlist_ids = [playlist["id"] for playlist in result["playlists"]["items"]]
        return playlist_ids

    def get_track_ids(self, playlist_ids):
        track_results = []
        headers = self.get_auth_header()
        params = {
            "limit": 100,
        }
        for id in playlist_ids:
            response = requests.get(self.spotify_api_url + f"/playlists/{id}/tracks", headers=headers, params=params)

            if response.status_code == 401:
                return ["401"]
            if response.status_code != 200:
                result = response.json()
                return ["Fail", result["error"]]

            track_result = response.json()
            track_ids = [track["track"]["id"] for track in track_result["items"]]
            track_results.append(track_ids)
        return track_results

    def get_audio_features(self, track_ids_dict):
        audio_features = {}
        headers = self.get_auth_header()
        for playlist_id, track_ids in track_ids_dict.items():
            track_ids_string = ",".join(track_ids)

            params = {
                "ids": track_ids_string,
            }
            response = requests.get(self.spotify_api_url + f"/audio-features", headers=headers, params=params)

            if response.status_code == 401:
                return ["401"]
            if response.status_code != 200:
                result = response.json()
                return ["Fail", result["error"]]

            audio_features_result = response.json()
            audio_features[playlist_id] = audio_features_result["audio_features"]
        return audio_features

    def get_avg_audio_features(self, audio_features):
        avg_audio_features = {
            "acousticness": 0.0,
            "danceability": 0.0,
            "energy": 0.0,
            "instrumentalness": 0.0,
            "liveness": 0.0,
            "loudness": 0.0,
            "speechiness": 0.0,
            "tempo": 0.0,
            "valence": 0.0
        }
        for _, audio_feature in audio_features.items():
            for key, value in audio_feature[0].items():
                if key in avg_audio_features:
                    avg_audio_features[key] += value
        
        for audio_feature in avg_audio_features.keys():
            avg_audio_features[audio_feature] = avg_audio_features[audio_feature] / len(audio_features)
        
        return avg_audio_features

    def get_recommended_tracks(self, avg_audio_features, seed_track):
        headers = self.get_auth_header()
        params = {
            "limit": "20",
            "seed_tracks": seed_track,
            "target_acousticness": avg_audio_features["acousticness"],
            "target_danceability": avg_audio_features["danceability"],
            "target_energy": avg_audio_features["energy"],
            "target_instrumentalness": avg_audio_features["instrumentalness"],
            "target_liveness": avg_audio_features["liveness"],
            "target_loudness": avg_audio_features["loudness"],
            "target_tempo": avg_audio_features["tempo"],
            "target_valence": avg_audio_features["valence"],
        }
        response = requests.get(self.spotify_api_url + "/recommendations", headers=headers, params=params)

        if response.status_code == 401:
            return ["401"]
        if response.status_code != 200:
            result = response.json()
            return ["Fail", result["error"]]

        result = response.json()
        recommended_tracks = [track["uri"] for track in result["tracks"]]
        return recommended_tracks

    def get_user_id(self):
        headers = self.get_auth_header()
        response = requests.get(self.spotify_api_url + "/me", headers=headers)

        if response.status_code == 401:
            return ["401"]
        if response.status_code != 200:
            result = response.json()
            return ["Fail", result["error"]]

        result = response.json()
        user_id = result["id"]
        return user_id

    def create_playlist(self, user_id, query):
        headers = self.post_auth_header()
        params = {
            "name": "Melody-Mate Playlist",
            "description": f"Playlist based on query of {query}",
        }
        response = requests.post(self.spotify_api_url + f"/users/{user_id}/playlists", headers=headers, json=params)

        if response.status_code == 401:
            return ["401"]
        if response.status_code != 201:
            result = response.json()
            return ["Fail", result["error"]]
        
        result = response.json()
        playlist_id = result["id"]
        url = result["external_urls"]["spotify"]
        return playlist_id, url

    def add_tracks_to_playlist(self, playlist_id, recommended_tracks):
        headers = self.post_auth_header()
        params = {
            "uris": recommended_tracks,
            "position": 0,
        }
        response = requests.post(self.spotify_api_url + f"/playlists/{playlist_id}/tracks", headers=headers, json=params)

        if response.status_code == 401:
            return ["401"]
        if response.status_code != 201:
            result = response.json()
            return ["Fail", result["error"]]
        
        return ["Success"]