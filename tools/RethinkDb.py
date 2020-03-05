from rethinkdb import r
from datetime import datetime
import time
import logging
import os

def create_logging():
    """
    This method is in place to write to the corresponding logging file, it checks in what directory it is currently
    running, and it will resolve if which path it should use to write the logs
    :return: No return
    """
    if os.getcwd().split('/')[-1] == "tools":
        if not os.path.exists("Rethinkdb.log"):
            with open('Rethinkdb', 'a'):
                pass
        logging.basicConfig(filename='Rethinkdb.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    else:
        if not os.path.exists("tools/Rethinkdb.log"):
            with open('tools/Rethinkdb', 'a'):
                pass
        logging.basicConfig(filename='tools/Rethinkdb.log', level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
create_logging()


class DataManager():

    def __init__(self, host: str, database: str):
        """
        This function is used once for initializing the class, this will try to connect to the database with the given
        'host' and 'database'.
        :param host: The address where the database is hosted, this can be an ip or domain name
        :param database: The name of the specific database you want to connect to
        """
        self._database = database
        self._host = host
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
        logging.info("Succesfully connected to host")
        if not self._database in r.db_list().run(self._conn):
            r.db_create(self._database).run(self._conn)
            logging.info("Succesfully created database")
        self._conn.use(self._database)
        logging.info("Succesfully selected database")

    def send_data(self, table, action):
        """
        This function is used to send data to the database, this will check if the given 'table' exists. If so, it will
        retreave the latest value and calculate the new one.
        :param table: The table where your data should be written to
        :param action: The action that should be taken with the data
        :return: No return
        """
        if not self._conn:
            self.make_connection()
        data_dict = {}
        data_dict["TimeStamp"] = r.now()
        previous = self._get_latest_value(table)
        if action == "+1":
            data_dict["People"] = previous + 1
        else:
            if previous > 0 or not previous == []:
                data_dict["People"] = previous - 1
            else:
                data_dict["People"] = 0
        logging.info(f"Sending {data_dict} to db.")
        r.table(table).insert(data_dict).run(self._conn)


    def _get_latest_value(self, table):
        """
        This function is only availabe inside the class, it is used to retreave the latest value from a certain table.
        :param table: The name of the table you want to get the latest value from
        :return: The latest added value for 'people' in this table
        """
        if not self._check_table_exist(table):
            self._make_table(table)
        result = r.table(table).order_by(r.desc("TimeStamp")).limit(1).run(self._conn)
        logging.debug(f"Last value: {result}")
        if result:
            return result[0]["People"]
        return 0

    def _check_table_exist(self, table):
        """
        This functoin is only available inside the class, it is used to check if the 'table' exists.
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
