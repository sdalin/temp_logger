#!/usr/bin/python
from logger import Logger
import time
import os

#Record the temperature from our raspberry pi
directory = '/sys/bus/w1/devices/'
dirlist = os.listdir(directory)
devices = [s for s in dirlist if s.startswith(hex(0x28)[2:])]
tfile = open(directory + devices[0] + "/w1_slave")
tempLog = Logger('inside_temp_log.txt')

while True:
    startTime = time.clock()
    text = tfile.read()
    while not text:
        print time.asctime() + ': couldn''t read from "' + directory + devices[0] + '/w1_slave". Trying again. '
        time.sleep(1)
        text = tfile.read()
    secondline = text.split("\n")[1]
    temperaturedata = secondline.split("=")[1]
    temperature = float(temperaturedata)/1000*1.8+32
    tempLog.write(str(temperature))
    endTime = time.clock()
    elapsedTime = endTime - startTime
    print "temp_logger_inside.py elapsed time: " + str(elapsedTime)
    time.sleep(max(5*60 - elapsedTime, 0))

tfile.close()
