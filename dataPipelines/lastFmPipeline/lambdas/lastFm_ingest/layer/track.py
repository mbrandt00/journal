import datetime as dt


class Track:
    def __init__(self, track, album, timestamp):
        self.track = track
        self.album = album
        self.timestamp = int(timestamp)

    def get_artist(self):
        return self.track.artist.get_name()

    def readable_timestamp(self):
        return dt.datetime.fromtimestamp(int(self.timestamp))

    def get_duration(self):
        """
        returns duration in seconds
        """
        return int(self.track.get_duration() / 1000)

    def serialize_track(self):
        dict = {
            "title": self.track.title,
            "artist": self.get_artist(),
            "duration": self.get_duration(),
            "album": self.album,
            "timestamp": self.timestamp,
            "url": self.track.get_url(),
        }
        return dict
