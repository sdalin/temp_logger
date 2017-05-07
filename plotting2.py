from pandas import *
from matplotlib.pyplot import *

column_names = ["Date","Time","UnixTime","NodeID","MessageIndex","Temperature","Humidity","Temperature2","Humdidty2"]
bedroom = read_table('logs/temp_hum.txt', sep='[ \t]', header=None, names=column_names[2:7], usecols=range(2,7))
bedroom = bedroom[bedroom.NodeID=='E2']

bedroom = bedroom.dropna()
bedroom.Temperature = bedroom.Temperature.apply(float)

bedroom['DateTime'] = to_datetime(bedroom.UnixTime, unit='s')



column_names2 = ["Date","Time","UnixTime","Temperature","Humidity"]
diningroom = read_table('logs/inside_temp.txt', sep='[ \t]', header=None, names = column_names2)
diningroom = diningroom.dropna()
diningroom.Temperature = diningroom.Temperature.apply(float)
diningroom['DateTime'] = to_datetime(diningroom.UnixTime, unit='s')



print True