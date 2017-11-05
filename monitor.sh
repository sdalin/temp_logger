#!/bin/bash
date
printf "  "; tail -1 logs/inside_temp.txt
printf "  "; tail -1 logs/outside_temp.txt
printf "  "; tail -3 logs/temp_hum.txt
printf "  "; tail -2 logs/thermostat.txt
tail -7 nohup.out
