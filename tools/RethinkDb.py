from rethinkdb import r
from datetime import datetime
import time
import logging

try:
    logging.basicConfig(filename='tools/Rethinkdb.log', level=logging.INFO,
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
except FileNotFoundError:
    logging.basicConfig(filename='Rethinkdb.log', level=logging.INFO,
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
        self._conn = r.connect(host=self._host).repl()
        logging.info("Succesfully connected to host")
        if not self._database in r.db_list().run():
            r.db_create(self._database).run()
        self._conn.use(self._database).run()
        logging.info("Succesfully selected database")

    def send_data(self, table, change):
        data_dict = {}
        data_dict["TimeStamp"] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        previous = self._get_latest_value(table)
        if change == "+1":
            data_dict["People"] = previous + 1
        else:
            data_dict["People"] = previous - 1

        r.table(table).insert()

    def _get_latest_value(self, table):
        current_count = 0
        if self._check_table_exist(table):
            response = r.table("table").run(self._conn)
            current_count = response[-1]["People"]
        else:
            self._make_table()
        return current_count

    def _check_table_exist(self):
        raise NotImplemented

    def _make_table(self):
        raise NotImplemented
