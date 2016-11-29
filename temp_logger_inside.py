#!/usr/bin/python
from logger import Logger
import time
import os
from sensors import *

#Record the temperature from our raspberry pi
try:
    sensor = DS18B20()
except IndexError:     # list index out of range, i.e. no DS18B20 plugged in
    sensor = DHT()


tempLog = Logger('log/inside_temp.txt')
while True:
    startTime = time.time()
    data = sensor.read()
    if type(data) is tuple:
        temperature = data[0]
        humidity = data[1]
    elif type(data) is float:
        temperature = data
        humidity = None
    if temperature != None:
        temperature = float(temperature)*1.8+32
    if humidity != None:
        tempLog.write('%.1f %.1f%%' % (temperature, humidity))
    elif temperature != None:
        tempLog.write('%.1f' % temperature)
    else:
        print(time.asctime() + ": temp_logger_inside.py sensor read failed.")
    endTime = time.time()
    elapsedTime = endTime - startTime
    print time.asctime() + ": temp_logger_inside.py elapsed time: " + str(elapsedTime)
    time.sleep(max(1*60 - elapsedTime, 0))
