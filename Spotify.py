from Entities import *
import requests
import Domoticz
import time
import base64
import json
import os


class SpotifyConnection:
    def __init__(self, credentials, code):
        self.credentials = credentials
        self.api_base_url = 'https://api.spotify.com/v1'
        self.api_account_url = 'https://accounts.spotify.com/api/token'
        self.redirect_url = 'https://spotify.ipictserver.nl/index.php'
        self.token = self._load_token(code=code)

    def _token(self):
        if self.token.is_expired() is False:
            return self.token.access
        else:
            self.token = self._request_token()
            self._store_token(self.token)
            return self.token.access

    def _store_token(self, token):
        with open(os.getcwd() + '/plugins/.spotifycache', 'w+') as file:
            file.write(json.dumps(token.raw))

    def _load_token(self, code):
        try:
            with open(os.getcwd() + '/plugins/.spotifycache', 'r') as file:
                token = Token(json.load(file))
                Domoticz.Debug("Loaded token from file.")
                return token
        except FileNotFoundError:
            token = self._request_token(refresh=False, code=code)
            self._store_token(token)
            Domoticz.Debug("Requested token from spotify")
            return token

    def _request_token(self, refresh=True, code=None):
        data = {}
        if refresh:
            if self.token is not None:
                data['grant_type'] = 'refresh_token'
                data['refresh_token'] = self.token.refresh
        else:
            if code is not None:
                data['grant_type'] = 'authorization_code'
                data['code'] = code
                data['redirect_uri'] = self.redirect_url
        base64string = base64.b64encode('{}:{}'.format(self.credentials['id'],
                                                       self.credentials['secret']).encode('utf-8'))
        headers = {'Authorization': 'Basic {}'.format(base64string.decode('ascii'))}
        response = self._account_request(headers, data)
        response['expires_at'] = time.time() + response['expires_in']
        response['refresh_token'] = self.token.refresh
        return Token(response)

    def _account_request(self, headers, data):
        response = {'error_description': 'N/A'}
        try:
            response = requests.post(url=self.api_account_url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            Domoticz.Debug("{} ({})".format(e, response.json()['error_description']))

    def _request(self, method, endpoint, data=None, headers=None):
        if headers is None:
            headers = {}
        headers["Authorization"] = "Bearer {}".format(self._token())
        try:
            if method == "POST":
                response = requests.post(url=self.api_base_url + endpoint, headers=headers, json=data)
            elif method == "PUT":
                response = requests.put(url=self.api_base_url + endpoint, headers=headers, json=data)
            else:
                response = requests.get(url=self.api_base_url + endpoint, headers=headers)
            response.raise_for_status()
            return response
        except Exception as e:
            Domoticz.Debug("{} ({})".format(e, response.json()))

    def get_devices(self):
        Domoticz.Debug("Retrieving spotify devices.")
        device_list = []
        response = self._request("GET", "/me/player/devices")
        if response.status_code == 200:
            for item in response.json()['devices']:
                device_list.append(Device(item))
            return device_list

    def transfer_playback(self, device_id):
        Domoticz.Debug("Transferring playback to device with id {}.".format(device_id))
        data = {"device_ids": [str(device_id)], "play": "true"}
        headers = {"Content-Type": "application/json"}
        self._request("PUT", "/me/player", data, headers)

    def get_current_playback(self):
        Domoticz.Debug("Retrieving current playback.")
        response = self._request("GET", "/me/player")
        if response.status_code == 200:
            if response.json() is None:
                return None
            return CurrentPlayback(response.json())

    def set_volume(self, percentage):
        Domoticz.Debug("Setting volume to {}.".format(percentage))
        self._request("PUT", "/me/player/volume?volume_percent=" + str(percentage), None)
