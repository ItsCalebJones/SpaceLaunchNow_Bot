import sys

import time
import datetime

from config import keys
from twitter import *
from onesignalsdk import OneSignalSdk
from launchlibrarysdk import LaunchLibrarySDK
from tinydb import TinyDB, Query

db = TinyDB('H:\GitHub\Space-Launch-Now-Server\db.json')

AUTH_TOKEN_HERE = keys['AUTH_TOKEN_HERE']
APP_ID = keys['APP_ID']
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
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )

    def send_to_twitter(self, message, launch):
        # self.twitter.statuses.update(status=message)
        self.twitter.direct_messages.new(
            user="ItsCalebJones",
            text=message)
        if launch.last_twitter_update is None:
            db.insert({'launch': launch.launch_id, 'last_twitter_update': time.time()})
        else:
            db.update({'last_twitter_update': time.time()}, Query().launch == launch.launch_id)

    def check_next_launch(self):
        response = self.launchLibrary.get_next_launches()
        launch_data = response.json()
        for launches in launch_data["launches"]:
            launch = Launch(launches)
            if launch.netstamp > 0:
                current_time = datetime.datetime.utcnow()
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.netstamp))
                if current_time <= launch_time:
                    diff = int((launch_time - current_time).total_seconds())
                    print diff
                    if launch.last_twitter_update is not None:
                        time_since_last_twitter_update = (current_time - datetime.datetime.utcfromtimestamp(
                            int(launch.last_twitter_update))).total_seconds()
                        print 'Seconds since last update on Twitter %d' % time_since_last_twitter_update
                        if diff < 86400 & diff > 3600:
                            if time_since_last_twitter_update > 43200:
                                self.send_to_twitter('%s launching from %s in %s' %
                                                     (launch.launchName, launch.location, self.seconds_to_time(diff)),
                                                     launch)
                        if diff < 3600 & diff > 3600:
                            if time_since_last_twitter_update > 3600:
                                self.send_to_twitter('%s launching from %s in %s' %
                                                     (launch.launchName, launch.location, self.seconds_to_time(diff)),
                                                     launch)
                    else:
                        print 'Launch has not been posted to Twitter.'
                        self.send_to_twitter('%s launching from %s in %s' % (
                            launch.launchName, launch.location, self.seconds_to_time(diff)), launch)

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

    def seconds_to_time(self, seconds):
        seconds_in_day = 86400
        seconds_in_hour = 3600
        seconds_in_minute = 60

        days = seconds // seconds_in_day
        seconds -= days * seconds_in_day

        hours = seconds // seconds_in_hour
        seconds -= hours * seconds_in_hour

        minutes = seconds // seconds_in_minute
        seconds -= minutes * seconds_in_minute
        return "{0:.0f} days, {1:.0f} hours, {2:.0f} minutes.".format(days, hours, minutes, seconds)


class Launch:
    def __init__(self, launch):
        self.launch_id = launch["id"]
        self.launchName = launch["name"]
        self.status = launch["status"]
        self.netstamp = launch["netstamp"]
        if len(launch["location"]["pads"]) > 0:
            self.location = launch["location"]["pads"][0]["name"]
        if len(launch["missions"]) > 0:
            self.missions = launch["missions"]
        response = db.search(Query().launch == self.launch_id)
        if len(response) > 0:
            self.last_twitter_update = response[len(response) - 1]['last_twitter_update']
        else:
            self.last_twitter_update = None

    def record_twitter_update(self, time):
        pass


if __name__ == '__main__':
    sys.exit(main())
