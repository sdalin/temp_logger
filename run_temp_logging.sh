#!/bin/sh
nohup python -u outdoorWeb.py &
nohup sudo python -u temp_logger_inside.py &
nohup sudo rpi-listen &
