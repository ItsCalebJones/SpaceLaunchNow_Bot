import sys

import time
import datetime

from config import keys
from twitter import *
from models import Launch
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
        self.diff = None
        response = self.onesignal.get_app(APP_ID)
        assert response.status_code == 200
        self.app = response.json()
        assert isinstance(self.app, dict)
        assert self.app['id'] and self.app['name'] and self.app['updated_at'] and self.app['created_at']
        self.app_auth_key = self.app['basic_auth_key']
        self.twitter = Twitter(
            auth=OAuth(keys['TOKEN_KEY'], keys['TOKEN_SECRET'], keys['CONSUMER_KEY'], keys['CONSUMER_SECRET'])
        )
        self.twitter_table = db.table('twitter')
        self.launch_table = db.table('launch')

    def send_to_twitter(self, message, launch):
        # self.twitter.statuses.update(status=message)
        self.twitter.direct_messages.new(
            user="ItsCalebJones",
            text=message)
        if launch.last_twitter_post is None:
            self.twitter_table.insert({'launch': launch.launch_id, 'last_twitter_update': time.time()})
        else:
            self.twitter_table.update({'last_twitter_update': time.time()}, Query().launch == launch.launch_id)

    def check_next_launch(self):
        response = self.launchLibrary.get_next_launches()
        launch_data = response.json()
        for launches in launch_data["launches"]:
            launch = Launch(launches)
            if launch.net_stamp > 0:
                current_time = datetime.datetime.utcnow()
                launch_time = datetime.datetime.utcfromtimestamp(int(launch.net_stamp))
                if current_time <= launch_time:
                    self.diff = int((launch_time - current_time).total_seconds())
                    self.check_twitter(self.diff, launch)
                    self.check_launch_window(self.diff, launch)

    def check_twitter(self, diff, launch):
        if launch.last_twitter_post is not None:
            time_since_last_twitter_update = (datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(
                int(launch.last_twitter_post))).total_seconds()
            print 'Seconds since last update on Twitter %d' % time_since_last_twitter_update
            if diff < 86400:
                if diff > 3600:
                    if time_since_last_twitter_update > 43200:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.launch_name, launch.location, self.seconds_to_time(diff)),
                                             launch)
                if diff < 3600:
                    if time_since_last_twitter_update > 3600:
                        self.send_to_twitter('%s launching from %s in %s' %
                                             (launch.launch_name, launch.location, self.seconds_to_time(diff)),
                                             launch)
        else:
            self.log('Launch has not been posted to Twitter.')
            self.send_to_twitter('%s launching from %s in %s' % (launch.launch_name, launch.location,
                                                                 self.seconds_to_time(diff)), launch)

    def check_launch_window(self, diff, launch):
        # If launch is within 24 hours...
        if diff <= 86400:
            self.send_notification(launch)
            launch.is_notified_24(True)
        elif diff <= 3600:
            self.send_notification(launch)
            launch.is_notified_one_hour(True)
        elif diff <= 600:
            launch.is_notified_ten_minutes(True)

    def send_notification(self, launch):
        self.onesignal.user_auth_key = self.app_auth_key
        self.onesignal.app_id = APP_ID
        self.log('Creating notification for %s' % launch.launch_name)

        # Create a notification
        contents = '%s launching from %s' % (launch.launchName, launch.location)
        kwargs = dict(
            content_available=True,
            included_segments=['Debug'],
            isAndroid=True,
            data={"silent": True}
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
        self.log('Space Launch Now daemon is now running.')
        while True:
            self.check_next_launch()
            if self.diff > 600:
                self.log('Next launch in %i, sleeping for %d seconds.' % (self.diff, DAEMON_SLEEP))
                time.sleep(DAEMON_SLEEP)
            else:
                self.log('Sleeping for %d seconds.' % self.diff)
                time.sleep(self.diff)

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


if __name__ == '__main__':
    sys.exit(main())
