#!/usr/bin/python
import requests
import json
from logger import Logger
import time

f = open('logs/outside_temp_history.txt', 'a')
# from february 15 through april

for month in range(3,8):
    if month < 10:
        month = '0' + str(month)
    else:
        month = str(month)
    if month == '03':
        days = range(14, 32)
    elif month == '07':
        days = range(1, 30)
    else:
        days = range(1,18)
    for day in days:
        if day < 10:
            day = '0' + str(day)
        else:
            day = str(day)
        success = False
        tries = 0
        while not success and tries <= 10:
            try:
                url = 'http://api.wunderground.com/api/62875508aeaaee2d/history_2017' + month + day + '/q/MA/Somerville.json'
                output = requests.get(url)
                dictionary = json.loads(output.text)
                observations = dictionary['history']['observations']
                success = True
            except Exception as e:
                print str(e)
                success = False
                tries += 1
        for i in xrange(len(observations)):
            # self.log.write(time.strftime("%m/%d/%y %H:%M:%S") + " " + str(time.time()) + "\t" + message + "\n")
            # 02/16/16 22:34:27 1455680067.13	72.275
            date = observations[i]['date']
            struct_time = (int(date['year']), int(date['mon']), int(date['mday']), int(date['hour']), int(date['min']), 0, 0, 0, -1)
            unixtime = time.mktime(struct_time)

            line = date['mon'] + '/' + date['mday'] + '/' + date['year'][2:4] + " " + date['hour'] + ':' + date['min']
            line += ' ' + str(unixtime) + '\t' + observations[i]['tempi'] + '\t' + observations[i]['hum'] + '%\n'
            f.write(line)
        time.sleep(6)   # 10 call/minute limit

f.close()
