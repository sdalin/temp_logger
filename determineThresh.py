#!/usr/local/bin/python

#reads appropriate .json file (in variable configFile) to output a threshold temperature and
#room to read temp from, based on current day/time
import datetime
import requests
import json
import codecs


def makeJSONDict(jsonOutput):
    # make dict of this year's holiday dates and candle lighting times
    holidays = {}
    key = 0
    while key < len(jsonOutput['items']):
        key += 1
        if jsonOutput['items'][key - 1]['title'][0:6] == 'Candle':
            holidays[jsonOutput['items'][key - 1]['date'][0:10]] = jsonOutput['items'][key - 1]['title'][17:22]
        else:
            continue
    return holidays

def determineDayTypeAndTime():
    # Determine time and day of week
    currentDateTime = datetime.datetime.now()
    currentTime = currentDateTime.strftime("%H:%M:%S")
    day = currentDateTime.strftime("%a")

    if day in ["Sat", "Sun"]:
        dayType = 'end'
    else:
        dayType = 'week'

    # If it's a chag, revert to weekend day type

    # Determine Date
    Today = datetime.datetime.today()
    yesterday = datetime.datetime.today() - datetime.timedelta(1)
    prevDay = yesterday.strftime("%Y-%m-%d")
    todayYMD = Today.strftime("%Y-%m-%d")
    yesterday = prevDay

    try:
        # Read the chag days JSON already stored
        f = codecs.open('chagDays.json', 'r', 'utf-8')
        output = f.read()
        dictionary = json.loads(output)
        f.close()

        # make dict of the stored year's holiday dates and candle lighting times
        holidays = makeJSONDict(dictionary)

        # check if there was candle lighting in the past week in the stored data
        holidayDates = holidays.keys()
        dataCurrent = False
        for day in range(7):
            testDay = datetime.datetime.today() - datetime.timedelta(day)
            testDayYMD = testDay.strftime("%Y-%m-%d")
            if testDayYMD in holidayDates:
                dataCurrent = True
    except (IOError, ValueError):
        dataCurrent = False

    # If there wasn't candle lighting in the past week in the stored data, we need new data
    # TODO: try to pre-emptively download data before its urgent
    if not dataCurrent:
        urlparams = 'v=1&cfg=json&maj=off&min=off&mod=off&nx=on&year=now&month=x&ss=off&mf=on&c=on&geo=zip&zip=02143&b=18&m=50&s=on'
        output = requests.get('http://www.hebcal.com/hebcal/?' + urlparams)
        # Write new data and load into variable to create dict
        f = codecs.open('chagDays.json', 'w', 'utf-8')
        f.write(json.dumps(json.loads(output.text), indent=2))
        f.close()

        dictionary = json.loads(output.text)

        # make dict of the stored year's holiday dates and candle lighting times
        holidays = makeJSONDict(dictionary)

    # check if there was candle lighting yesterday
    holidayDates = holidays.keys()
    if yesterday in holidayDates:
        dayType = 'end'
    elif todayYMD in holidayDates and currentDateTime.hour > 14:
        # start weekend program at 2pm on days with candle lighting
        dayType = 'end'

    return currentTime, dayType


def readThreshFromConfigFile(configFile):
    # Determine if weekend or weekday and current time
    [currentTime,dayType] = determineDayTypeAndTime()

    # Load thermostat program into nested dict
    with open(configFile) as json_file:
        programDict = json.load(json_file)

    # use dict to access day/time to get thresh and room
    dayTimes = programDict[dayType].keys()

    # list all time keys less than the current time, sort then select biggest
    # to find most recent time
    lst = [x for x in dayTimes if x < currentTime]
    lst.sort()
    timeType = lst[-1]

    # return threshold temp and room to read from
    return programDict[dayType][timeType]


def determineThreshRoom(configFile):
    # if controlType == 'cooling':
    #     programFile = "./fanProgram.txt"
    # elif controlType == 'heating':
    #     programFile = "./heatProgram.txt"

    # Determine if weekend or weekday and current time
    [currentTime, dayType] = determineDayTypeAndTime()

    # Load thermostat program into nested dict
    programDict = {}
    with open(configFile) as f:
        for line in f:
            lineArray = line.split()
            if line[0] == '#':
                continue
            if lineArray[0] in programDict:
                programDict[lineArray[0]][lineArray[1]] = [lineArray[2]]
                programDict[lineArray[0]][lineArray[1]].append(lineArray[3])
            else:
                programDict[lineArray[0]] = {}
                programDict[lineArray[0]][lineArray[1]] = [lineArray[2]]
                programDict[lineArray[0]][lineArray[1]].append(lineArray[3])

    # use dict to access day/time to get thresh and room
    dayTimes = programDict[dayType].keys()

    # list all time keys less than the current time, sort then select biggest
    # to find most recent time
    lst = [x for x in dayTimes if x < currentTime]
    lst.sort()
    timeType = lst[-1]

    # access the threshold temp and room to read from
    thresh = programDict[dayType][timeType][0]
    readRoom = programDict[dayType][timeType][1]

    # return threshold temp and room to read from
    return float(thresh), readRoom

