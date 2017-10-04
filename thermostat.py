#!/usr/local/bin/python
from determineThresh import determineThreshRoom

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  "
          "You can achieve this by using 'sudo' to run your script")
import time
from sensors import *
from logger import Logger

import sys
import subprocess

try:
    sensor = DS18B20()
except IndexError:     # list index out of range, i.e. no DS18B20 plugged in
    sensor = DHT()


def readDining():
    data = sensor.read()
    temp = None
    hum = None
    if type(data) is tuple:
        temp = data[0]
        hum = data[1]
    elif type(data) is float:
        temp = data
        hum = None
    if temp is not None:
        temp = float(temp)*1.8+32
    return temp


def readBed():
    if sys.platform == 'linux2':
        text = subprocess.Popen('tac logs/temp_hum.txt | grep -m1 "E2"', shell=True,
                                stdout=subprocess.PIPE).stdout.read()
    elif sys.platform == 'darwin':
        text = subprocess.Popen('tail -r logs/temp_hum.txt | grep -m1 "E2"', shell=True,
                                stdout=subprocess.PIPE).stdout.read()
    textList = text.split()
    # TODO: make some assertions about integrity of text in that line
    if time.time() - int(textList[2]) < 5*60:
        temp = float(textList[5])
        hum = float(textList[6])
        # TODO: deal with lack of data, i.e. set up email alerts
    return temp


def readRoom(room='dining'):
    if room.lower() == 'dining':
        return readDining()
    elif room.lower() == 'bed':
        return readBed()
    else:
        raise ValueError


log = Logger('logs/thermostat.txt')

GPIO.setmode(GPIO.BCM)
readPin = 24
writePin = 23
GPIO.setup(writePin, GPIO.OUT, initial=False)
GPIO.setup(readPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
while True:
    startTime = time.time()
    # temperature setting in F and room to read temp from
    [thresh, room] = determineThreshRoom()
    temperature = readRoom(room)
    if temperature is not None:
        if temperature < thresh:
            #GPIO.output(writePin, True)
            log.write('Heat on: %.1f degrees in %s is below %i degree threshold.' % (temperature, room, thresh))
        else:
            #GPIO.output(writePin, False)
            log.write('Heat off: %.1f degrees in %s is above %i degree threshold.' % (temperature, room, thresh))
    else:
        log.write(time.asctime() + ": thermostat.py sensor read failed.")
    if GPIO.input(readPin):
        log.write('Magic 8 ball says heater is probably on.')
    else:
        log.write('Magic 8 ball says heater is probably off.')
    endTime = time.time()
    elapsedTime = endTime - startTime
    print(time.asctime() + ": thermostat.py elapsed time: " + str(elapsedTime))
    time.sleep(max(1*60 - elapsedTime, 0))

GPIO.cleanup()
