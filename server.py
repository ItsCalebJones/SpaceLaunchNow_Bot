import sys

import time

from onesignalsdk import OneSignalSdk
from launchlibrarysdk import LaunchLibrarySDK

AUTH_TOKEN_HERE = ''
APP_ID = ''
DAEMON_SLEEP = 600


def main():
    slns = SpaceLaunchNowNotificationServer()
    slns.run()


class SpaceLaunchNowNotificationServer:
    def __init__(self):
        self.onesignal = OneSignalSdk(AUTH_TOKEN_HERE, APP_ID)
        self.launchLibrary = LaunchLibrarySDK()
        response = self.onesignal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.app_auth_key = self.app['basic_auth_key']

    def check_next_launch(self):
        response = self.launchLibrary.get_next_launches()
        launchdata = response.json()
        for launches in launchdata["launches"]:
            print launches
            launch = Launch(launches)
            print '%s launching from %s' % (launch.launchName, launch.location)
            self.send_notification(launch)

    def send_notification(self, launch):
        self.onesignal.user_auth_key = self.app_auth_key
        self.onesignal.app_id = APP_ID

        # Create a notification
        contents = '%s launching from %s' % (launch.launchName, launch.location)
        kwargs = dict(
            android_group="thisGroup",
            included_segments=['Debug'],
            isAndroid=True,
            small_icon='ic_rocket_white',
            large_icon='ic_human_explore'
        )
        url = 'https://launchlibrary.net'
        heading = 'Space Launch Now'
        response = self.onesignal.create_notification(contents, heading, url, **kwargs)
        assert response.status_code == 200
        notification_data = response.json()
        notification_id = notification_data['id']
        assert notification_data['id'] and notification_data['recipients']
        # Get the notification
        response = self.onesignal.get_notification(APP_ID, notification_id, self.app_auth_key)
        notification_data = response.json()
        assert notification_data['id'] == notification_id
        assert notification_data['contents']['en'] == contents

    def log(self, message):
        print message

    def run(self):
        """The daemon's main loop for doing work"""
        self.log('Space Launch Now daemon is now running...')
        while True:
            self.check_next_launch()
            self.log('Sleeping for %d seconds...' % DAEMON_SLEEP)
            time.sleep(DAEMON_SLEEP)


class Launch:
    def __init__(self, launch):
        self.launchName = launch["name"]
        self.status = launch["status"]
        self.netstamp = launch["netstamp"]
        if len(launch["location"]["pads"]) > 0:
            self.location = launch["location"]["pads"][0]["name"]
        if len(launch["missions"]) > 0:
            self.missions = launch["missions"]


if __name__ == '__main__':
    sys.exit(main())
