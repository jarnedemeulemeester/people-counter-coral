import requests
from google.cloud import pubsub_v1
import logging
import os

#environment variable in code aanmaken (linux zelf gaf problemen)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/mendel/project3/Project3-ML6-515024366790.json"
logging.basicConfig(filename='tools/CloudManager.log',level=logging.INFO)

class CloudManager():
    def __init__(self, project_id, topic_name):
        logging.info("Initialized cloud manager with project-id: %s and topic-name: %s"% (project_id,topic_name))
        self.cache_file = "tools/publish-message.cache"
        self.cache_file_local = "publish-message.cache"
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)

    def publish_to_topic(self,data:str):
        logging.info("Sending attempt for data: %s"% data)
        message = data.encode('utf-8')
        if self.check_internet():
            publish_message = self.publisher.publish(self.topic_path,data=message)
            logging.info("Message Confirmation: %s" % publish_message.result())
            if not publish_message.result() == None:
                lines = self.get_all_local_storage()
                if lines:
                    self.sent_local_storage(lines)
            #publish_message.add_done_callback(self.callback_status) #validate if it was sent succesfully
        else:
            self.save_to_local_storage(data)

    """
    Deze callback function gaf problemen, dus nu is het aan de hand van een simpele .result() zodanig dat er confirmatie is dat het gewerkt heeft.
    Hierdoor is de afhandeling iets minder goed, echter de kans dat google cloud down is is zodanig klein dat dit de normale werking niet zou moeten beinvloeden.
    """
    def callback_status(self, publish_message):
        if not publish_message.exception(timeout=5):
            logging.info("Message Confirmation: %s"%publish_message.result())
            #self.sent_local_storrage()
        else:
            logging.info("Message sending failed...")

    """ 
    Deze functie schrijft alle data weg naar locale storage
    """
    def save_to_local_storage(self, data):
        logging.info("Localy caching the following message: %s"%data)
        cache = open(self.cache_file, "a")
        cache.write("%s \n" % data.replace('"',""))
        cache.close()


    """
    Deze functie haat alle locale data op en overschrijft en cleart vervolgens de file
    """
    def get_all_local_storage(self):
        try:
            lines = [line.rstrip('\n') for line in open(self.cache_file)]
            open(self.cache_file, 'w').close()
        except:
            lines = [line.rstrip('\n') for line in open(self.cache_file_local)]
            open(self.cache_file_local, 'w').close()
        logging.info("Retrieved all local data: %s" % lines)
        return lines

    def sent_local_storage(self, lines):
        lines_failed = []
        if lines:
            for line in lines:
                if self.check_internet():
                    self.publish_to_topic(line)
                else:
                    lines_failed.append(line)
        else:
            logging.info("No local cache")
        try:
            cache = open(self.cache_file, "w")
        except:
            cache = open(self.cache_file_local, "w")
        for line in lines_failed:
            cache.write("%s \n" % line)

    def check_internet(self):
        url = 'http://www.google.com/'
        timeout = 5
        try:
            _ = requests.get(url, timeout=timeout)
            logging.info("Internet connectivity")
            return True
        except requests.ConnectionError:
            logging.info("No internet connectivity")
            return False