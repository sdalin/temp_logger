__author__ = 'Simona'
#Make plots of inside/outside data.  One with each data type vs. time, one with outside temp vs. 1st derivative of inside temp.

import numpy as np
import matplotlib.pyplot as plt
import datetime as dt


outsideDate,outsideTime,outsideUnixTime,outsideTemp = np.genfromtxt("outsidePlot.txt", unpack=True, skiprows=1)
insideDate,insideTime,insideUnixTime,insideTemp = np.genfromtxt("insidePlot.txt", unpack=True, skiprows=1)

#plt.plot(outsideUnixTime,outsideTemp,'r',insideUnixTime,insideTemp,'b')
#plt.show()

bothTemps = np.empty([len(outsideTemp),2])
insideOutsideDiff = np.empty([len(outsideTemp),1])

for line in range(0,len(outsideTemp)):
    bothTemps[line,0] = outsideTemp[line]
    tempOutsideTime = outsideUnixTime[line]
    timeIndex = np.argwhere(np.abs(insideUnixTime-tempOutsideTime)<300)

    if len(timeIndex)>1:
        timeIndex = np.max(timeIndex)

    if not timeIndex:
        bothTemps[line,:] = [np.nan,np.nan]
    else:
        bothTemps[line,1] = insideTemp[timeIndex]

    insideOutsideDiff[line] = bothTemps[line,0] - bothTemps[line,1]

insideFirstDeriv = np.diff(bothTemps[:,1])

plt.plot(insideOutsideDiff[:-1,0],insideFirstDeriv,'.')
plt.show()

print True