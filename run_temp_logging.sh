#!/bin/sh
nohup python -u outdoorWeb.py &
nohup python -u temp_logger_inside.py &
nohup sudo ./rpi-listen &
