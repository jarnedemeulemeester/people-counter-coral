import logging
import os
from socket import gethostname
from threading import Thread
import requests
import time
import redis

logging.basicConfig(level=logging.INFO)


class DataManager():
    """
    This class is responsible to manage all the data transfering to and form the given host with a NSDb
    More info on nsdb can be found here: https://nsdb.io/
    """
    
    def __init__(self, nsdb_host: str, nsdb_port: int, redis_host: str, redis_port: int, database: str, namespace: str, metric: str):
        self._nsdb_host = nsdb_host
        self._nsdb_port = nsdb_port
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._database = database
        self._namespace = namespace
        self._metric = metric
        self._hostname = gethostname()
        self._location = None

        self._r = redis.Redis(host=self._redis_host, port=self._redis_port, db=0, decode_responses=True)

        self._location = self._r.get(f'device:{self._hostname}:location')
        if not self._location:
            self._r.set(f'device:{self._hostname}:location', 0)


    def send_data(self, action):
        self._location = self._r.get(f'device:{self._hostname}:location')

        if self._location == '0':
            logging.critical('Location has not been set for this device, please do so in the dashboard settings')
            return

        new_n_people = self._r.incrby(f'location:{self._location}:people', action)
        
        if new_n_people < 0: 
            self._r.set(f'location:{self._location}:people', 0)
            new_n_people = 0

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

        r = requests.post(f'http://{self._nsdb_host}:{self._nsdb_port}/data', json=payload)

        if r.status_code != 200:
            logging.error(r.text)
