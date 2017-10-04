#!/bin/bash

if pidof -x thermostat.py >/dev/null; then
    echo "Thermostat script is running!"
fi