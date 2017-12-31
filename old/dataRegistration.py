import numpy as np

_, _, insideUnixTime, insideTemp = np.genfromtxt("inside_temp_log.txt", unpack=True)
_, _, outsideUnixTime, outsideTemp = np.genfromtxt("outside_data.txt", unpack=True)
# generate outside_data.txt with the following bash command:
# sort -k 3,3 -m outside_temp_history.txt outside_temp_log.txt > outside_data.txt

# smallest unix time 1453472278.51 (Jan 22)
# largest unix time 1462238112.49 (May 2)
minTime = 1453472280
maxTime = 1462238100

dt = 30     # timestep (sec)

timestamps = np.arange(minTime, maxTime+1, dt)
insideDataClean = np.empty_like(timestamps, dtype=float)
outsideDataClean = np.empty_like(timestamps, dtype=float)
insideDataInterp = np.empty_like(timestamps, dtype=float)
outsideDataInterp = np.empty_like(timestamps, dtype=float)

iInd = 0    # index of inside data
oInd = 0    # index of outside data
for i in xrange(len(timestamps)):
    t = timestamps[i]
    while iInd < len(insideUnixTime)-1 and insideUnixTime[iInd] < t - dt/2:
        iInd += 1
    if insideUnixTime[iInd] < t + dt/2:
        insideDataClean[i] = insideTemp[iInd]
    else:
        insideDataClean[i] = np.nan
    while oInd < len(outsideUnixTime)-1 and outsideUnixTime[oInd] < t - dt/2:
        oInd += 1
    if outsideUnixTime[oInd] < t + dt/2:
        outsideDataClean[i] = outsideTemp[oInd]
    else:
        outsideDataClean[i] = np.nan

insideDataInterp = np.interp(timestamps, insideUnixTime, insideTemp)
outsideDataInterp = np.interp(timestamps, outsideUnixTime, outsideTemp)

tol = 20*60     # time (sec) after which we don't trust interpolation
for i in xrange(tol/dt/2, len(timestamps)-tol/dt/2):
    if np.all(np.isnan(insideDataClean[i-tol/dt/2:i+tol/dt/2])):
        insideDataInterp[i] = np.nan
    if np.all(np.isnan(outsideDataClean[i-tol/dt/2:i+tol/dt/2])):
        outsideDataInterp[i] = np.nan

dataDict = {'timestamps': timestamps,
            'insideDataClean': insideDataClean,
            'outsideDataClean': outsideDataClean,
            'insideDataInterp': insideDataInterp,
            'outsideDataInterp': outsideDataInterp
            }
import pickle
pickle.dump(dataDict, open('dataPickle.pkl', 'w'))
print True