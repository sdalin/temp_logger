#!/usr/local/bin/python
from determineThresh import determineThreshRoom
from functions import *

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
import traceback

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
    filename = 'logs/temp_hum.txt'
    searchterm = 'E2'
    if sys.platform == 'linux2':
        p1 = subprocess.Popen(['tac', filename], stdout=subprocess.PIPE)
    elif sys.platform == 'darwin':
        p1 = subprocess.Popen(['tail', '-r', filename], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(['grep', '-m1', searchterm], stdin=p1.stdout, stdout=subprocess.PIPE)
    text = p2.communicate()[0]
    textList = text.split()
    # TODO: make some assertions about integrity of text in that line
    if time.time() - int(textList[2]) < 5*60:
        temp = float(textList[5])
        hum = float(textList[6])
    else:
        sendEmail('From Thermostat', 'No recent temperature data coming in over radio. Last line:\n' + text)
    return temp


def readRoom(room='dining'):
    if room.lower() == 'dining':
        return readDining()
    elif room.lower() == 'bed':
        return readBed()
    else:
        raise ValueError


class ActuatorsContextManager:
    def __init__(self):
        pass

    def __enter__(self):
        GPIO.setmode(GPIO.BCM)
        return Actuators()

    def __exit__(self, exc_type, exc_val, exc_tb):
        GPIO.cleanup()


class Actuators:
    def __init__(self):
        self.heatReadPin = 24
        self.heatOnPin = 23
        self.coolOnPin = 5
        self.coolOffPin = 6
        GPIO.setup(self.heatOnPin, GPIO.OUT, initial=False)
        GPIO.setup(self.coolOnPin, GPIO.OUT, initial=False)
        GPIO.setup(self.coolOffPin, GPIO.OUT, initial=False)
        GPIO.setup(self.heatReadPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def coolOn(self):
        # turns cooling on
        GPIO.output(self.coolOnPin, False)
        GPIO.output(self.coolOffPin, False)
        GPIO.output(self.coolOnPin, True)
        time.sleep(1)
        GPIO.output(self.coolOnPin, False)

    def coolOff(self):
        # turns cooling off
        GPIO.output(self.coolOnPin, False)
        GPIO.output(self.coolOffPin, False)
        GPIO.output(self.coolOffPin, True)
        time.sleep(1)
        GPIO.output(self.coolOffPin, False)

    def heatOn(self):
        # turns heat on
        GPIO.output(self.heatOnPin, True)

    def heatOff(self):
        # turns heat off
        GPIO.output(self.heatOnPin, False)

    def heatOnBool(self):
        # checks if heat is on
        return GPIO.input(self.heatReadPin)

#configFile = 'cooling'
configFile = 'WinterConfig.json'

if configFile.find('Winter') > -1:
    controlType = 'heating'
elif configFile.find('Summer') > -1:
    controlType = 'cooling'

log = Logger('logs/thermostat.txt')
hysteresis = 1      # amount that the temp can be off from set point before triggering actuator
nFailures = 0
with ActuatorsContextManager() as actuators:
    while True and __name__ == "__main__":
        try:
            startTime = time.time()
            # temperature setting in F and room to read temp from
            [thresh, room] = determineThreshRoom(configFile)
            temperature = readRoom(room)
            if temperature is not None:
                if controlType == 'heating':
                    if temperature < thresh - hysteresis:
                        #actuators.heatOn()
                        log.write('Heat on: %.1f F in %s < %i F setpoint.' % (temperature, room, thresh))
                    elif temperature > thresh + hysteresis:
                        #actuators.heatOff()
                        log.write('Heat off: %.1f F in %s > %i F.' % (temperature, room, thresh))
                    else:
                        log.write('No heating change: %.1f F in %s is near %i F setpoint.' % (temperature, room, thresh))
                elif controlType == 'cooling':
                    if temperature > thresh + hysteresis:
                        actuators.coolOn()
                        log.write('Cooling on: %.1f F in %s > %i F setpoint.' % (temperature, room, thresh))
                    elif temperature < thresh - hysteresis:
                        actuators.coolOff()
                        log.write('Cooling off: %.1f F in %s < %i F setpoint.' % (temperature, room, thresh))
                    else:
                        log.write('No cooling change: %.1f F in %s is near %i F setpoint.' % (temperature, room, thresh))
            else:
                log.write(time.asctime() + ": thermostat.py sensor read failed.")
            if actuators.heatOnBool():
                log.write('Magic 8 ball says heater is probably on.')
            else:
                log.write('Magic 8 ball says heater is probably off.')
            endTime = time.time()
            elapsedTime = endTime - startTime
            print(time.asctime() + ": thermostat.py elapsed time: " + str(elapsedTime))
            time.sleep(max(1*60 - elapsedTime, 0))
        except UnboundLocalError:
            nFailures += 1
            if nFailures >= 3:
                sendEmail('Thermostat Shutdown', 'No recent temperature data coming in over radio. ')
                raise
            else:
                pass
        except Exception:
            nFailures += 1
            text = 'Failure ' + str(nFailures) + '\n' + traceback.format_exc()
            log.write(text)
            if nFailures >= 3:
                sendEmail('Thermostat Shutdown', text)
                raise
            else:
                sendEmail('Thermostat Error', text)
