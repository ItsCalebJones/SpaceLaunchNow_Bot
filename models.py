from tinydb import TinyDB, Query

db = TinyDB('H:\GitHub\Space-Launch-Now-Server\db.json')


class Launch:
    def __init__(self, launch):
        self.launch_id = launch["id"]
        self.launch_name = launch["name"]
        self.status = launch["status"]
        self.net_stamp = launch["netstamp"]
        self.data = launch
        self.notified = False
        self.location = launch["location"]

        if len(launch["missions"]) > 0:
            self.missions = launch["missions"]

        self.launch_table = db.table('launch')

        response = self.launch_table.search(Query().launch == self.launch_id)
        if len(response) > 0:
            self.last_twitter_post = response[len(response) - 1]['last_twitter_update']
        else:
            self.last_twitter_post = None

        launch_cache = self.launch_table.search(Query().launch == self.launch_id)
        if launch_cache:
            self.wasNotifiedTwentyFourHour = launch_cache[0]['isNotified24']
            self.wasNotifiedOneHour = launch_cache[0]['isNotifiedOne']
            self.wasNotifiedTenMinutes = launch_cache[0]['isNotifiedTen']
            if launch_cache[0]['net'] != self.net_stamp:
                self.reset_notifiers()
        else:
            self.launch_table.insert({'launch': self.launch_id,
                                      'last_twitter_update': None,
                                      'net': self.net_stamp,
                                      'name': self.launch_name,
                                      'isNotified24': False,
                                      'isNotifiedOne': False,
                                      'isNotifiedTen': False})

    def reset_notifiers(self):
        self.wasNotifiedTwentyFourHour = False
        self.wasNotifiedOneHour = False
        self.wasNotifiedTenMinutes = False
        self.update_record()

    def is_notified_24(self, boolean):
        self.wasNotifiedTwentyFourHour = boolean
        self.update_record()

    def is_notified_one_hour(self, boolean):
        self.wasNotifiedOneHour = boolean
        self.update_record()

    def is_notified_ten_minutes(self, boolean):
        self.wasNotifiedTenMinutes = boolean
        self.update_record()

    def update_record(self):
        self.launch_table.update({'isNotified24': self.wasNotifiedTwentyFourHour,
                                  'isNotifiedOne': self.wasNotifiedOneHour,
                                  'isNotifiedTen': self.wasNotifiedTenMinutes},
                                 Query().launch == self.launch_id)



