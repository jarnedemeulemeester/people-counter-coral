import logging
import os
from socket import gethostname
from threading import Thread
import requests
import time

logging.basicConfig(level=logging.INFO)


class DataManager():
    """
    This class is responsible to manage all the data transfering to and form the given host with a NSDb
    More info on nsdb can be found here: https://nsdb.io/
    """
    
    def __init__(self, host: str, port: int, database: str, namespace: str, metric: str):
        self._host = host
        self._port = port
        self._database = database
        self._namespace = namespace
        self._metric = metric
        self._location = "room"
        self._latest_value = 0


    def send_data(self, action):
        new_n_people = self._latest_value + action
        if new_n_people < 0: new_n_people = 0

        payload = {
            "db": self._database,
            "namespace": self._namespace,
            "metric": self._metric,
            "bit": {
                "timestamp": time.time(),
                "value": new_n_people,
                "dimensions": {
                    "location": self._location
                },
                "tags": {}
            }
        }

        r = requests.post(f'http://{self._host}:{self._port}/data', json=payload)

        if r.status_code != 200:
            logging.error(r.text)


    def _update_location(self):
        # TODO
        pass


    async def _get_latest_value(self, location):
        # Redis code...
        pass
