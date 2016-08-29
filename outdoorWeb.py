#!/usr/bin/python
import requests
import json
from logger import Logger
import time


tempLog = Logger('outside_temp_log.txt')
while True:
    startTime = time.time()
    try:
        output = requests.get('http://api.wunderground.com/api/62875508aeaaee2d/conditions/q/pws:KMASOMER13.json')
        dictionary = json.loads(output.text)
        temperature = dictionary['current_observation']['temp_f']
        humidity = dictionary['current_observation']['relative_humidity']
    except Exception as e:
        print str(e)
        continue

    tempLog.write(str(temperature) + ' ' + str(humidity))
    endTime = time.time()
    elapsedTime = endTime - startTime
    print "outdoorWeb.py elapsed time: " + str(elapsedTime)
    time.sleep(max(5*60 - elapsedTime, 0))


