#
# Simple Arduino Makefile
#
# http://arduino.stackexchange.com/questions/21492/will-a-ino-arduino-sketch-compile-directly-on-gcc-avr
# Author: Nick Gammon
# Date: 18th March 2015

# where you installed the Arduino app
ARDUINO_DIR = /Users/hsanders/Documents/projects/avr/Arduino-1.5.6/

# various programs
CC = avr-gcc
CXX = avr-g++
AR = avr-ar
OBJ_COPY = avr-objcopy

MAIN_SKETCH = dht22readandsend.ino

# Archive flags
ARFLAGS = rcs

# may need to change these
F_CPU = 16000000
MCU = atmega328p

# compile flags
GENERAL_FLAGS = -c -g -Os -Wall -ffunction-sections -fdata-sections \
				-mmcu=$(MCU) -DF_CPU=$(F_CPU)L -MMD -DUSB_VID=null -DUSB_PID=null -DARDUINO=106
CXXFLAGS = $(GENERAL_FLAGS) -fno-exceptions $(INCLUDE_FILES) $(patsubst %,-I%,$(EXTRA_DIRS))
CFLAGS  = $(GENERAL_FLAGS) $(INCLUDE_FILES) $(patsubst %,-I%,$(EXTRA_DIRS))

# location of include files
INCLUDE_FILES = "-I$(ARDUINO_DIR)hardware/arduino/avr/cores/arduino" \
			    "-I$(ARDUINO_DIR)hardware/arduino/avr/variants/standard" 


# library sources
LIBRARY_DIR = $(ARDUINO_DIR)hardware/arduino/avr/variants/standard

BUILD_NAME = $(MCU)-$$(($(F_CPU)/1000000))MHz
LIBNAME = libinocore$(BUILD_NAME).a


EXTRA_DIRS = $(ARDUINO_DIR)/hardware/arduino/avr/libraries/SPI \
			 ../libraries/RF24 \
			 ../libraries/DHT-sensor-library

OBJDIR = $(LIBRARY_DIR)/$(BUILD_NAME)objs

_CXX_OBJS = RF24.o DHT.o SPI.o
CXX_OBJS = $(patsubst %,$(OBJDIR)/%,$(_CXX_OBJS))
HEADERS = SPI.h DHT.h RF24.h nRF24L01.h

VPATH = $(LIBRARY_DIR) $(EXTRA_DIRS)

build: $(HEADERS)
	$(MAKE) build_library
	#$(CPP) $(CPP_FLAGS) $(INCLUDE_FILES) $(MAIN_SKETCH) -o $(MAIN_SKETCH).o
	$(CXX) $(CXXFLAGS) $(INCLUDE_FILES) -x c++ -include Arduino.h $(MAIN_SKETCH) -o $(MAIN_SKETCH).o
	$(CC) -Os -Wl,--gc-sections -mmcu=$(MCU) -o $(MAIN_SKETCH).elf $(MAIN_SKETCH).o $(LIBRARY_DIR)/$(LIBNAME) -lm 
	$(OBJ_COPY) -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --no-change-warnings --change-section-lma .eeprom=0 $(MAIN_SKETCH).elf $(MAIN_SKETCH).eep 
	$(OBJ_COPY) -O ihex -R .eeprom $(MAIN_SKETCH).elf $(MAIN_SKETCH).hex
	rm *.d *.o

build_library: $(CXX_OBJS)
	$(AR) $(ARFLAGS) $(LIBRARY_DIR)/$(LIBNAME) $^

$(OBJDIR)/%.o: %.cpp
	$(CXX) $(CXXFLAGS) $^ -o $@




