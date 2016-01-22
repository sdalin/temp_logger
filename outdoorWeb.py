#!/usr/bin/python
import requests
import json
from logger import Logger
import time


tempLog = Logger('outside_temp_log.txt')
while True:
    output = requests.get('http://api.wunderground.com/api/62875508aeaaee2d/conditions/q/pws:KMASOMER13.json')
    dictionary = json.loads(output.text)
    temperature = dictionary['current_observation']['temp_f']
    tempLog.write(str(temperature))
    time.sleep(5*60)



