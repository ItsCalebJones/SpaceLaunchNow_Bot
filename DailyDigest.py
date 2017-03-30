import time
import sys

from twitter import *
from libraries.launchlibrarysdk import LaunchLibrarySDK
from libraries.onesignalsdk import OneSignalSdk
from utils.config import keys
from utils.util import db, log

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
DAEMON_SLEEP = 600
TAG = 'Digest Server'


def main():
    daily_digest = DailyDigestServer()
    daily_digest.run()


class DailyDigestServer:
    def __init__(self):
        self.onesignal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK()
        response = self.onesignal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.app_auth_key = self.app['basic_auth_key']
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )
        self.launch_table = db.table('launch')
        self.time_to_next_launch = None
        self.next_launch = None

    def run(self):
        """The daemon's main loop for doing work"""
        log(TAG, 'Daemon is now running.')
        while True:
            if self.time_to_next_launch > 600:
                log(TAG, 'Sleeping for %d seconds.' % DAEMON_SLEEP)
                time.sleep(DAEMON_SLEEP)


if __name__ == '__main__':
    sys.exit(main())
