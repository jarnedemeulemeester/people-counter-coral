from rethinkdb import r
from datetime import datetime
import time
import logging
import os

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


class DataManager():

    def __init__(self, host: str, database: str):
        self._database = database
        self._host = host
        try:
            self.make_connection()
        except Exception as ex:
            logging.critical(f"Exception while trying to connect: {ex}")

    def make_connection(self):
        self._conn = r.connect(host=self._host, port=28015)
        logging.info("Succesfully connected to host")
        if not self._database in r.db_list().run(self._conn):
            r.db_create(self._database).run(self._conn)
            logging.info("Succesfully created database")
        self._conn.use(self._database)
        logging.info("Succesfully selected database")

    def send_data(self, table, action):
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
        r.table(table).insert(data_dict).run(self._conn)

    def _get_latest_value(self, table):
        if not self._check_table_exist(table):
            self._make_table(table)
        result = r.table(table).order_by(r.desc("TimeStamp")).limit(1).run(self._conn)
        logging.debug(f"Last value: {result}")
        if result:
            return result[0]["People"]
        return 0

    def _check_table_exist(self, table):
        logging.info(f"Checking if {table} exists")
        return table in r.table_list().run(self._conn)

    def _make_table(self, table):
        logging.info(f'Creating table {table}')
        r.table_create(table).run(self._conn)
