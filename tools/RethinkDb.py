from rethinkdb import r
import logging
import os
from socket import gethostname
from threading import Thread

def create_logging():
    """
    This method is in place to write to the corresponding logging file, it checks in what directory it is currently
    running, and it will resolve if which path it should use to write the logs
    :return: No return
    """
    if os.getcwd().split('/')[-1] == "tools":
        logging.basicConfig(filename='rethinkdb.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    else:
        logging.basicConfig(filename='tools/rethinkdb.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
create_logging()


class DataManager():
    """
    This class is responsible to manage all the data transfering to and form the given host with a RethinkDB
    More info on Rethinkdb can be found here: https://rethinkdb.com/
    """

    def __init__(self, host: str, database: str):
        """
        This function is used once for initializing the class, this will try to connect to the database with the given
        'host' and 'database'.
        :param host: The address where the database is hosted, this can be an ip or domain name
        :param database: The name of the specific database you want to connect to
        """
        self._database = database
        self._host = host
        self._location = None
        try:
            self.make_connection()
        except Exception as ex:
            logging.critical(f"Exception while trying to connect: {ex}")

    def make_connection(self):
        """
        This function is used to establish a connection with the database, it will connect to the host and check if the
        chosen database exists. If it does not exist, it will create a new one. After those checks, it will connect to
        the corresponding database
        :return: No return
        """
        self._conn = r.connect(host=self._host, port=28015)
        self._conn2 = r.connect(host=self._host, port=28015)
        logging.info("Succesfully connected to host")
        if not self._database in r.db_list().run(self._conn):
            r.db_create(self._database).run(self._conn)
            logging.info("Succesfully created database")
        self._conn.use(self._database)
        self._conn2.use(self._database)
        logging.info("Succesfully selected database")

        tables = ["device", "location"]
        for table in tables:
            if not self._check_table_exist(table):
                self._make_table(table)

        self._check_device_entry()

        Thread(target=self._update_location).start()

    def send_data(self, action):
        """
        This function is used to send data to the database, this will check if the given 'table' exists. If so, it will
        retrieve the latest value and calculate the new one.
        :param table: The table where your data should be written to
        :param action: The action that should be taken with the data
        :return: No return
        """
        if not self._conn:
            self.make_connection()

        data_dict = {}
        data_dict["timestamp"] = r.now()
        previous = self._get_latest_value(self._location)
        if action == "+1":
            new_n_people = previous + 1
        else:
            if previous > 0:
                new_n_people = previous - 1
            else:
                new_n_people = 0
        data_dict["people"] = new_n_people
        logging.info(f"Sending {data_dict} to db.")
        r.table("location").filter({"name": self._location}).update({"people": new_n_people}).run(self._conn)
        r.table(self._location).insert(data_dict).run(self._conn)


    def _check_device_entry(self):
        if r.table("device").filter({"name": gethostname()}).count().run(self._conn) == 0:
            r.table("device").insert({"name": gethostname()}).run(self._conn)
    
    def _update_location(self):
        # Get initial location
        self._location = list(r.table("device").filter({"name": gethostname()}).limit(1).eq_join("location", r.table("location")).run(self._conn))[0]["right"]["name"]
        
        # When the location updates in the db, update the local variable
        feed = r.table("device").filter({"name": gethostname()}).changes().run(self._conn2)
        for changes in feed:
            self._location = r.table("location").get(changes["new_val"]["location"]).run(self._conn2)["name"]

    def _get_latest_value(self, location):
        """
        This function is only available inside the class, it is used to retrieve the latest value from a certain table.
        :param table: The name of the table you want to get the latest value from
        :return: The latest added value for 'people' in this table
        """
        result = r.table("location").filter({"name": location}).run(self._conn)
        logging.debug(f"Last value: {result}")
        if result:
            return list(result)[0]["people"]
        return 0

    def _check_table_exist(self, table):
        """
        This function is only available inside the class, it is used to check if the 'table' exists.
        :param table: The name of the table you want to check
        :return: True if the table exists and false if it does not
        """
        logging.info(f"Checking if {table} exists")
        return table in r.table_list().run(self._conn)

    def _make_table(self, table):
        """
        This function is only available inside the class, it is used to create a new table in the case that you want to
        write data to a not existing table.
        :param table: The name the table that will be created
        :return: No return
        """
        logging.info(f'Creating table {table}')
        r.table_create(table).run(self._conn)
