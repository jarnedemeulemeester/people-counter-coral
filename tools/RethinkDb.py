from rethinkdb import r
from datetime import datetime
import time
import json

data_dict= {}

#get insert data
with r.connect(host='10.10.20.53',port=28015, db='Ruban') as conn:

    for i in range (1,20):
        time.sleep(2)
        data_dict["TimeStemp"]=datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        data_dict["PeopleCounted"] = i
        r.table("Test").insert(data_dict).run(conn)

    response = r.table("Test").run(conn)
    print(response)