#!/bin/sh
nohup python -u outdoorWeb.py 2>>logs/outside_temp.txt &
nohup python -u temp_logger_inside.py 2>>logs/inside_temp.txt &
nohup sudo ./rpi-listen &
