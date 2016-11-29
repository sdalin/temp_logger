
# Select Advanced and enable the SPI kernel module 
sudo raspbi-config

g++ -o rpi-listen -lrf24 rpi-listen.cpp; chmod +x rpi-listen
