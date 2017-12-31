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
        return temp, hum
    else:
        sendEmail('From Thermostat', 'No recent temperature data coming in over radio. Last line:\n' + text)
        return None, None


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
        return self.sensor.read(self.unit)




######## Actuators #########

class Boiler:
    def __init__(self):
        self.name = 'boiler'
        self.Name = 'Boiler'
        self.readPin = 24
        self.onPin = 23

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


class BRCooler(WoodsOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'br'
        thing = 'Cooler'
        self.name = room + thing
        self.Name = room.upper() + thing
        onPin = 5
        offPin = 6
        WoodsOutlet.__init__(self, onPin, offPin)


class BRHumidifier(WoodsOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'br'
        thing = 'Humidifier'
        self.name = room + thing
        self.Name = room.upper() + thing
        onPin =
        offPin =
        WoodsOutlet.__init__(self, onPin, offPin)


class LRHeater(WoodsOutlet):
    # functions through Woods 13569 remote outlet switch
    def __init__(self):
        room = 'lr'
        thing = 'Heater'
        self.name = room + thing
        self.Name = room.upper() + thing
        onPin =
        offPin =
        WoodsOutlet.__init__(self, onPin, offPin)




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



######## Main loop #########

implemented = False
nFailures = 0
log = Logger('logs/thermostat.txt')

boiler = Boiler()
brTemperature = BRTemperature()
brHumidity = BRHumidity()
brHumidifier = BRHumidifier()
drTemperature = DRTemperature()
lrTemperature = LRTemperature()
lrHeater = LRHeater()
# controllers[room][type]['v' or 'a'].  'v' is input/process value, 'a' is actuator
controls = {'bed': {'temp': {'v': brTemperature, 'a': boiler},
                    'hum': {'v': brHumidity, 'a': brHumidifier}},
           'dining': {'temp': {'v': drTemperature, 'a': boiler}},
           'living': {'temp': {'v': lrTemperature, 'a': lrHeater}}}
while implemented and __name__ == "__main__":
    try:
        startTime = time.time()
        [thresh, room] = determineThreshRoom('heating')
        success = increaseController(thresh, controls[room]['temp']['v'], controls[room]['temp']['a'])



        if not success:
            nFailures += 1
            if nFailures >= 3:
                text = 'Failure in control of {0} room'.format(room)
                sendEmail('Thermostat Shutdown', text)
                raise Exception(text)
            else:
                pass

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
            raise
        else:
            sendEmail('Thermostat Error', text)


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
configFile = './thermostatProgram.txt'

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
            [thresh, room] = readThreshFromConfigFile(configFile)
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
