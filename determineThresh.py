#!/usr/local/bin/python

#reads thermostatProgram.txt to output a threshold temperature and
#room to read temp from, based on current day/time

def determineThreshRoom():
    import time
    import requests
    import json

    programFile = "./thermostatProgram.txt"
    dateTime = time.ctime()
    dateTimeSplit = dateTime.split()

    # Determine time and day of week
    day = dateTimeSplit[0]
    currentTime = dateTimeSplit[3]

    if day in ["Sat", "Sun"]:
        dayType = 'end'
    else:
        dayType = 'week'

    # Load thermostat program into nested dict
    programDict = {}
    with open(programFile) as f:
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


    # If it's a chag, revert to weekend day type
    # TODO: try/except api request
    # TODO: cache result of API response processing for rest of day
    output = requests.get('http://www.hebcal.com/hebcal/?v=1&cfg=json&maj=off&min=off&mod=off&nx=on&year=now&month=x&ss=off&mf=on&c=on&geo=zip&zip=02143&b=18&m=50&s=on')
    dictionary = json.loads(output.text)
    currentDate = time.strftime("%Y-%m-%d", time.gmtime())
    # TODO: deal with first day of month
    prevDay = str(int(currentDate[8:10])-1)
    if len(prevDay) < 2:
        temp = '0'
        temp += prevDay
        prevDay = temp
    yesterday = currentDate[0:8]
    yesterday += prevDay

    # make dict of this year's holiday dates and candle lighting times
    holidays = {}
    key = 0
    while key < len(dictionary['items']):
        key += 1
        if dictionary['items'][key-1]['title'][0:6] == 'Candle':
            holidays[dictionary['items'][key-1]['date'][0:10]] = dictionary['items'][key-1]['title'][17:22]
        else:
            continue

    # check if there was candle lighting yesterday
    holidayDates = holidays.keys()
    if yesterday in holidayDates:
        dayType = 'end'








    # use dict to access day/time to get thresh and room
    dayTimes = programDict[dayType].keys()

    # list all time keys less than the current time, sort then select biggest
    # to find most recent time
    list = [x for x in dayTimes if x < currentTime]
    list.sort()
    timeType = list[-1]

    # access the threshold temp and room to read from
    thresh = programDict[dayType][timeType][0]
    readRoom = programDict[dayType][timeType][1]

    # return threshold temp and room to read from
    return float(thresh), readRoom
