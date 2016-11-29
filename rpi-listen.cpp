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
    radio.openReadingPipe(1,0xF0F0F0F0E1LL);
    radio.startListening();
	 radio.printDetails();
}
 
void loop(void)
{
    // clear char array
    char rxBuffer[32] = "";
 
    while (radio.available())
    {
        // read from radio
        int len = radio.getDynamicPayloadSize();
        radio.read(&rxBuffer, len);
 
        // get time - can be passed to time.localtime()
        time_t rawtime;
        struct tm * timeinfo;
		  int slen = 32;
        char buffer[slen] = "";
        time(&rawtime);
        timeinfo = localtime(&rawtime);
        strftime(buffer,slen,"%m/%d/%y %H:%M:%S",timeinfo);

        char message[len] = "";
        int i; 
        for (i=0; i<len; i++) {
           if (rxBuffer[i] == ',') {
              message[i] = '\t';
           } else {
              message[i] = rxBuffer[i];
           }
        }
 
        // write to file and close
        ofstream myfile;
        myfile.open ("/var/tmp/rf24weather.txt");
        myfile << buffer << ' ' << rawtime << ' ' << message << endl;
        myfile.close();
        myfile.open ("logs/temp_hum.txt",ofstream::app);
        myfile << buffer << ' ' << rawtime << ' ' << message << endl;
        //myfile << rxBuffer << ':' << rawtime << endl;
        myfile.close();
    }
 
    // pause to reduce cpu load
    sleep(5);
}
 
int main(int argc, char** argv)
{
    setup();
    while(1)
        loop();
 
    return 0;
}
