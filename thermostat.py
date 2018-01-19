#!/usr/local/bin/python
from determineThresh import readThreshFromConfigFile
from functions import *

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  "
          "You can achieve this by using 'sudo' to run your script")
import time
from sensors import *
import rfsniffer
from logger import Logger

import sys
import subprocess
import traceback


def cleanUp():
    boiler.turnOff()
    lrHeater.turnOff()
    GPIO.cleanup()


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
        return temp, hum
    else:
        sendEmail('From Thermostat', 'No recent temperature data coming in over radio. Last line:\n' + text)
        return None, None


# list of data sources:  bedroom temp, bedroom hum, living room temp, dining room temp, dining room hum
# list of actuators:  boiler, bedroom fan/ac, bedroom humidifier, living room space heater
# list of setpoints:  dining room temp, bedroom temp, bedroom hum, living room temp

# DRT links boiler to DRT, BRT links boiler to BRT, BRH links BRH to BRH, LRT links LRSH and boiler to LRT


######## Inputs/Process Values ########

class BRTemperature:
    def __init__(self):
        self.room = 'bed'
        self.unit = 'F'
        self.type = 'temperature'

    def read(self):
        temp, hum = readBed()
        return temp


class BRHumidity:
    def __init__(self):
        self.room = 'bed'
        self.unit = '%'
        self.type = 'humidity'

    def read(self):
        temp, hum = readBed()
        return hum


class LRTemperature:
    def __init__(self):
        self.room = 'living'
        self.unit = 'F'
        self.type = 'temperature'
        self.sensor = DS18B20()

    def read(self):
        return self.sensor.read(self.unit)


class DRTemperature:
    def __init__(self):
        self.room = 'dining'
        self.unit = 'F'
        self.type = 'temperature'
        self.sensor = DHT()

    def read(self):
        data = self.sensor.read(self.unit)
        temp = data[0]
        hum = data[1]
        return temp



######## Actuators #########

class Boiler:
    def __init__(self):
        self.name = 'boiler'
        self.Name = 'Boiler'
        self.readPin = 24
        self.onPin = 23
        GPIO.setup(self.readPin, GPIO.IN)
        GPIO.setup(self.onPin, GPIO.OUT, initial=False)

    def turnOn(self):
        # turns heat on
        GPIO.output(self.onPin, True)

    def turnOff(self):
        # turns heat off
        GPIO.output(self.onPin, False)

    def isOn(self):
        # checks if heat is on
        return GPIO.input(self.readPin)


class WoodsOutlet:
    # functions through Woods 13569 remote outlet switch
    # by switching a relay attached to the remote itself.
    def __init__(self, onPin, offPin):
        self.onPin = onPin
        self.offPin = offPin
        GPIO.setup(self.onPin, GPIO.OUT, initial=False)
        GPIO.setup(self.offPin, GPIO.OUT, initial=False)

    def turnOn(self):
        GPIO.output(self.onPin, False)
        GPIO.output(self.offPin, False)
        GPIO.output(self.onPin, True)
        time.sleep(1)
        GPIO.output(self.onPin, False)

    def turnOff(self):
        GPIO.output(self.offPin, False)
        GPIO.output(self.onPin, False)
        GPIO.output(self.offPin, True)
        time.sleep(1)
        GPIO.output(self.offPin, False)


class RFOutlet:
    # uses rfsniffer to play codes captured with 315 or 433 MHz radios attached to RPi
    def __init__(self, outletID):
        self.txPin = 11     # in GPIO.BOARD numbering; =17 in BCM numbering
        self.buttondb = './buttons.db'
        self.outletID = outletID

    def turnOn(self):
        rfsniffer.play(self.txPin, self.outletID + 'on', self.buttondb)

    def turnOff(self):
        rfsniffer.play(self.txPin, self.outletID + 'off', self.buttondb)


class BRCooler(RFOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'br'
        thing = 'Cooler'
        self.name = room + thing
        self.Name = room.upper() + thing
        self.outletID = 'F1'    # i.e. CH F, channel 1
        RFOutlet.__init__(self, self.outletID)


class BRHumidifier(RFOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'br'
        thing = 'Humidifier'
        self.name = room + thing
        self.Name = room.upper() + thing
        self.outletID = 'F1'    # i.e. CH F, channel 1
        RFOutlet.__init__(self, self.outletID)


class LRHeater(RFOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'lr'
        thing = 'Heater'
        self.name = room + thing
        self.Name = room.upper() + thing
        self.outletID = 'F2'    # i.e. CH F, channel 2
        RFOutlet.__init__(self, self.outletID)




######## Controllers #########

def increaseController(setpoint, inputObj, actuator, hysteresis=1):
    # setpoint should be desired value
    # input should have a read() method that returns a value of the same type as setpoint
    # actuator should be object not class
    # hysteresis should be amount of acceptable variation from setpoint
    sensorValue = inputObj.read()
    textList = [actuator.Name, sensorValue, inputObj.unit, inputObj.room, setpoint, inputObj.type]
    failed = False
    if sensorValue is not None:
        if sensorValue < setpoint - hysteresis:
            actuator.turnOn()
            log.write('{0} on: {1:.1f}{2} in {3} room < setpoint of {4}{2}'.format(*textList))
        elif sensorValue > setpoint + hysteresis:
            actuator.turnOff()
            log.write('{0} off: {1:.1f}{2} in {3} room > setpoint of {4}{2}'.format(*textList))
        else:
            log.write('No {0} change: {1:.1f}{2} in {3} room is near setpoint of {4}{2}'.format(*textList))
    else:
        log.write(time.asctime() + ": {3} room {5} read failed.".format(*textList))
        failed = True
    try:
        if actuator.isOn():
            log.write('Magic 8 ball says heater is probably on.')
        else:
            log.write('Magic 8 ball says heater is probably off.')
    except AttributeError:      # this actuator has no isOn()
        pass
    if failed:
        return False
    else:
        return True


def decreaseController(setpoint, inputObj, actuator, hysteresis=1):
    # setpoint should be desired value
    # input should have a read() method that returns a value of the same type as setpoint
    # actuator should be object not class
    # hysteresis should be amount of acceptable variation from setpoint
    sensorValue = inputObj.read()
    textList = [actuator.Name, sensorValue, inputObj.unit, inputObj.room, setpoint, inputObj.type]
    failed = False
    if sensorValue is not None:
        if sensorValue > setpoint + hysteresis:
            actuator.turnOn()
            log.write('{0} on: {1:.1f}{2} in {3} room > setpoint of {4}{2}'.format(*textList))
        elif sensorValue < setpoint - hysteresis:
            actuator.turnOff()
            log.write('{0} off: {1:.1f}{2} in {3} room < setpoint of {4}{2}'.format(*textList))
        else:
            log.write('No {0} change: {1:.1f}{2} in {3} room is near setpoint of {4}{2}'.format(*textList))
    else:
        log.write(time.asctime() + ": {3} room {5} read failed.".format(*textList))
        failed = True
    try:
        # so far only heater has way to check if it's on or off
        if actuator.isOn():
            log.write('Magic 8 ball says heater is probably on.')
        else:
            log.write('Magic 8 ball says heater is probably off.')
    except AttributeError:  # this actuator has no isOn()
        pass
    if failed:
        return False
    else:
        return True


######## Main loop #########

implemented = True
nFailures = 0
log = Logger('logs/thermostat.txt')

configFile = 'config.json'

boiler = Boiler()
brTemperature = BRTemperature()
brCooler = BRCooler()
brHumidity = BRHumidity()
brHumidifier = BRHumidifier()
drTemperature = DRTemperature()
lrTemperature = LRTemperature()
lrHeater = LRHeater()
# controllers[room-type]['v' or 'a'].  'v' is input/process value, 'a' is actuator
controls = {'bedHeat': {'v': brTemperature, 'a': boiler, 'c': increaseController},
            'bedCool': {'v': brTemperature, 'a': boiler, 'c': decreaseController},
            'bedHum': {'v': brHumidity, 'a': brHumidifier, 'c': increaseController},
            'diningHeat': {'v': drTemperature, 'a': boiler, 'c': increaseController},
            'livingHeat': {'v': lrTemperature, 'a': lrHeater, 'c': increaseController},
            }
while implemented and __name__ == "__main__":
    lastOptimizees = {}
    try:
        startTime = time.time()
        optimizees = readThreshFromConfigFile(configFile)
        for optimizee in optimizees:
            success = controls[optimizee]['c'](optimizees[optimizee], controls[optimizee]['v'], controls[optimizee]['a'])
            if not success:
                text = 'Failure in control of {0}'.format(optimizee)
                raise Exception(text)
        orphans = [lo for lo in lastOptimizees if lo not in optimizees]
        for optimizee in orphans:
            lastOptimizees[optimizee]['a'].turnOff()
        lastOptimizees = optimizees
        endTime = time.time()
        elapsedTime = endTime - startTime
        print(time.asctime() + ": thermostat.py elapsed time: " + str(elapsedTime))
        time.sleep(max(1 * 60 - elapsedTime, 0))
    except Exception:
        nFailures += 1
        text = 'Failure ' + str(nFailures) + '\n' + traceback.format_exc()
        log.write(text)
        if nFailures >= 3:
            sendEmail('Thermostat Shutdown', text)
            cleanUp()
            raise
        else:
            sendEmail('Thermostat Error', text)
