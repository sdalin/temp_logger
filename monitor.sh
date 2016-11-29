#!/bin/bash
date
printf "  "; tail -1 logs/temp_hum.txt
printf "  "; tail -1 logs/inside_temp.txt
printf "  "; tail -1 logs/outside_temp.txt
tail nohup.out
