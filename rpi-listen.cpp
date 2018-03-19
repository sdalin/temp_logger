#include <cstdlib>
#include <iostream>
#include <fstream>
#include <time.h>
#include <unistd.h>
#include "RF24/RF24.h"

using namespace std;

/*
 radio 7 (miso) to gpio9/bcm21
 radio 6 (mosi) to gpio10/bcm19
 radio 5 (sck)  to gpio11/bcm23
 radio 4 (csn)  to gpio8/bcm24
 radio 3 (ce)   to gpio25/bcm22
 radio 2 (3.3v) to 3.3v
 radio 1 (gnd)  to gnd
 */

// spi device, spi speed, ce gpio pin
//RF24 radio("/dev/spidev0.0",8000000,25);
RF24 radio(RPI_V2_GPIO_P1_22, RPI_V2_GPIO_P1_24, BCM2835_SPI_SPEED_8MHZ);
// D2 is base station write, everyone else read
// E1-F2 are peripheral writes, base station read
//const uint64_t pipes[6] = { 0xF0F0F0F0D2LL, 0xF0F0F0F0E2LL,
//    0xF0F0F0F0E1LL, 0xF0F0F0F0E3LL,
//    0xF0F0F0F0F1, 0xF0F0F0F0F2 };
//uint8_t pipes[6][3] = { "0Base", "1Node", "2Node"};
uint64_t pipes[3] = { 0xF0F0F0F0D2LL, 0xF0F0F0F0E1LL,0xF0F0F0F0E2LL};

void timestring(time_t* rawtime, char* buffer, int slen)
{
    // get time - can be passed to time.localtime()
    struct tm * timeinfo;
    time(rawtime);
    timeinfo = localtime(rawtime);
    strftime(buffer,slen,"%m/%d/%y %H:%M:%S",timeinfo);
}

void getMessage(char* message, int len)
{
    char rxBuffer[len] = "";
    radio.read(&rxBuffer, len);
    int i;
    for (i=0; i<len; i++) {
        if (rxBuffer[i] == ',') {
            message[i] = '\t';
        } else {
            message[i] = rxBuffer[i];
        }
    }
}


void setup(void)
{
    // setup radio for listening
    radio.begin();
    radio.setAutoAck(1);
    radio.setRetries(15,15);
    radio.enableDynamicPayloads();
    radio.setDataRate(RF24_250KBPS);
    radio.setPALevel(RF24_PA_MAX);
    radio.setCRCLength(RF24_CRC_8);
    radio.setChannel(76);
    radio.openReadingPipe(1,pipes[1]);
    radio.openReadingPipe(2,pipes[2]);
    radio.startListening();
    radio.printDetails();
}

void loop(void)
{
    uint8_t pipe_num;
    while (radio.available(&pipe_num))
    {
        int slen = 32;
        char buffer[slen] = "";
        time_t rawtime;
        timestring(&rawtime, buffer, slen);
        printf("%s\tpipe #: %u\n", buffer, pipe_num);
        fflush(stdout);
        if (pipe_num == 0) {
            setup();
        } else {
            int len = radio.getDynamicPayloadSize();
            
            // read from radio
            char message[len] = "";
            getMessage(message, len);
            
            // write to file and close
            ofstream myfile;
            myfile.open ("/var/tmp/rf24weather.txt");
            myfile << buffer << ' ' << rawtime << '\t' << message << endl;
            myfile.close();
            myfile.open ("logs/temp_hum.txt",ofstream::app);
            myfile << buffer << ' ' << rawtime << '\t' << message << endl;
            //myfile << rxBuffer << ':' << rawtime << endl;
            myfile.close();
        }
    }
            
    // pause to reduce cpu load
    sleep(1);
}
            
int main(int argc, char** argv)
{
    setup();
    while(1)
    loop();
                
    return 0;
}
