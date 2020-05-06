import time


class Device:
    def __init__(self, data):
        self.id = data['id']
        self.active = data['is_active']
        self.private = data['is_private_session']
        self.restricted = data['is_restricted']
        self.name = data['name']
        self.type = data['type']
        self.volume = data['volume_percent']


class CurrentPlayback:
    def __init__(self, data):
        self.raw = data
        self.shuffle = data['shuffle_state']
        self.device = Device(data['device'])
        self.playing = data['is_playing']


class Token:
    def __init__(self, data):
        self.raw = data
        self.access = data['access_token']
        self.expires_at = data['expires_at']
        self.refresh = data['refresh_token']

    def is_expired(self):
        if time.time() > self.expires_at:
            return True
        else:
            return False


class SpotifyError(Exception):
    def __init__(self, msg):
        self.msg = msg
