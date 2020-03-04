from tools.RethinkDb import DataManager
from datetime import datetime
import time
import logging
import os

manager = DataManager(host="10.10.20.53", database="Ruban")
while True:
    #small strestest :) 10k/reads for 12writes/sec :o
    manager.send_data("Ruben", "+1")
    manager.send_data("Test", "+1")
