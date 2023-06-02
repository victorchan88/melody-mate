import requests
import json
import base64

class TokenHandler:
    def __init__(self, clientId, clientSecret, redirectUri):
        self.refresh_token = ""
        self.client_id = clientId
        self.client_secret = clientSecret
        self.token = ""
        self.redirect_uri = redirectUri
    
    def get_token(self):
        return self.token

    def get_refresh_token(self):
        return self.refresh_token

    def set_token(self, code):
        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        result = requests.post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        refresh_token = json_result["refresh_token"]
        self.token, self.refresh_token = token, refresh_token


    def set_refresh_token(self):
        auth_string = self.client_id + ":" + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        result = requests.post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        self.token = token

        if "refresh_token" in json_result:
            self.refresh_token = json_result["result_token"]
