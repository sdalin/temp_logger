#!/usr/local/bin/python
from determineThresh import readThreshFromConfigFile
from functions import *

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except RuntimeError:
    raise("Error importing RPi.GPIO!  This is probably because you need superuser privileges.  "
          "You can achieve this by using 'sudo' to run your script")
from sensors import *
import rfsniffer
from logger import Logger

import traceback
import datetime
import time

import requests


class ThermostatSensorError(StandardError):
    """" raise this when there's an error reading a sensor """


def cleanUp():
    boiler.turnOff()
    lrHeater.turnOff()
    GPIO.cleanup()


def readBed():
    esp = True
    if esp:
        try:
            resp = requests.get('http://192.168.1.101:8081')
            time.sleep(1)
            d = resp.json()
            temp = float(d['temperature'])*9/5+32
            hum = float(d['humidity'])
            return temp, hum
        except requests.exceptions.ConnectionError:
            log.write('Failed to get reading from ESP.')

    filename = 'logs/temp_hum.txt'
    searchterm = 'E2'
    line = tailgrep(filename, searchterm)
    textList = line.split()
    # TODO: make some assertions about integrity of text in that line
    if time.time() - int(textList[2]) < 15*60:
        temp = float(textList[5])
        hum = float(textList[6])
        return temp, hum
    else:
        #sendEmail('From Thermostat', 'No recent temperature data coming in over radio. Last line:\n' + line)
        raise ThermostatSensorError('No recent temperature data coming in over radio. Last line:\n' + line)


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
        self.txPin = 17 #11     # in GPIO.BOARD numbering; =17 in BCM numbering
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
        raise ThermostatSensorError('{3} room {5} read failed.'.format(*textList))
    try:
        if actuator.isOn():
            log.write('Magic 8 ball says heater is probably on.')
        else:
            log.write('Magic 8 ball says heater is probably off.')
    except AttributeError:      # this actuator has no isOn()
        pass


def decreaseController(setpoint, inputObj, actuator, hysteresis=1):
    # setpoint should be desired value
    # input should have a read() method that returns a value of the same type as setpoint
    # actuator should be object not class
    # hysteresis should be amount of acceptable variation from setpoint
    sensorValue = inputObj.read()
    textList = [actuator.Name, sensorValue, inputObj.unit, inputObj.room, setpoint, inputObj.type]
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
        raise ThermostatSensorError('{3} room {5} read failed.'.format(*textList))
    try:
        # so far only heater has way to check if it's on or off
        if actuator.isOn():
            log.write('Magic 8 ball says heater is probably on.')
        else:
            log.write('Magic 8 ball says heater is probably off.')
    except AttributeError:  # this actuator has no isOn()
        pass


class ErrorHandler:
    def __init__(self):
        self.nFailures = 0
        self.lastException = ''
        self.runningText = ''
        self.lastEmailTime = 0

    def handle(self):
        self.nFailures += 1
        text = 'Failure ' + str(self.nFailures) + '\n' + traceback.format_exc()
        log.write(text)
        if self.lastException == traceback.format_exception_only(*sys.exc_info()[:2])[0]:
            if self.nFailures == 1:
                self.runningText += text + "\n"
            else:
                self.runningText += time.asctime() + 'Failure ' + str(self.nFailures) + ': Same error.' + "\n"
            if (datetime.datetime.now() - self.lastEmailTime).total_seconds() < 60 * 60 * 12:
                pass
            else:
                sendEmail('Thermostat Error', self.runningText)
                self.lastEmailTime = datetime.datetime.now()
                self.runningText = ''
        else:
            if self.runningText:
                sendEmail('Thermostat Error', self.runningText)
                self.runningText = ''
            sendEmail('Thermostat Error', text)
            self.lastEmailTime = datetime.datetime.now()
        self.lastException = traceback.format_exception_only(*sys.exc_info()[:2])[0]




######## Main loop #########

implemented = True
log = Logger('logs/thermostat.txt')

configFile = 'config.json'

boiler = Boiler()
brTemperature = BRTemperature()
#brCooler = BRCooler()
# brHumdifier and brCooler are identical
brHumidity = BRHumidity()
brHumidifier = BRHumidifier()
drTemperature = DRTemperature()
lrTemperature = LRTemperature()
lrHeater = LRHeater()
actuators = [boiler,
             brHumidifier,
             lrHeater,
             ]
sensors = [brTemperature,
           brHumidity,
           drTemperature,
           lrTemperature,
           ]
# controllers[room-type]['v' or 'a'].  'v' is input/process value, 'a' is actuator
controls = {'bedHeat': {'v': brTemperature, 'a': boiler, 'c': increaseController, 'h': 1},
            'bedCool': {'v': brTemperature, 'a': brHumidifier, 'c': decreaseController, 'h': 1},
            'bedHum': {'v': brHumidity, 'a': brHumidifier, 'c': increaseController, 'h': 3},
            'diningHeat': {'v': drTemperature, 'a': boiler, 'c': increaseController, 'h': 1},
            'livingHeat': {'v': lrTemperature, 'a': lrHeater, 'c': increaseController, 'h': 1},
            }
errorHandler = ErrorHandler()
while implemented and __name__ == "__main__":
    startTime = time.time()
    try:
        unusedActuators = list(actuators)
        optimizees = readThreshFromConfigFile(configFile)
        for optimizee in optimizees:
            try:
                if controls[optimizee]['a'] in unusedActuators:
                    unusedActuators.remove(controls[optimizee]['a'])
                controls[optimizee]['c'](optimizees[optimizee], controls[optimizee]['v'],
                                         controls[optimizee]['a'], controls[optimizee]['h'])
            except ThermostatSensorError:
                errorHandler.handle()
        log.write('Turning off unusedActuators: ' + str(unusedActuators))
        for actuator in unusedActuators:
            actuator.turnOff()
    except Exception:
        errorHandler.handle()
    endTime = time.time()
    elapsedTime = endTime - startTime
    print(time.asctime() + ": thermostat.py elapsed time: " + str(elapsedTime))
    sleepTime = max(5 * 60 - elapsedTime, 0)
    os.system('sleep ' + str(sleepTime))

