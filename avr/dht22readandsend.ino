#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "DHT.h"

#include <avr/sleep.h>
#include <avr/power.h>
#include <avr/wdt.h>
 
//DHTSENSOR
#define DHTPIN 3     // what digital pin we're connected to
#define LEDPIN 2	 // digital pin with an LED

// Uncomment whatever type you're using!
//#define DHTTYPE DHT11   // DHT 11
#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
//#define DHTTYPE DHT21   // DHT 21 (AM2301)

// Connect pin 1 (on the left) of the sensor to +5V
// NOTE: If using a board with 3.3V logic like an Arduino Due connect pin 1
// to 3.3V instead of 5V!
// Connect pin 2 of the sensor to whatever your DHTPIN is
// Connect pin 4 (on the right) of the sensor to GROUND
// Connect a 10K resistor from pin 2 (data) to pin 1 (power) of the sensor

// Initialize DHT sensor.
DHT dht(DHTPIN, DHTTYPE);

float temperature;
float humidity;
 
// NRF24L01
// Set up nRF24L01 radio on SPI pin for CE, CSN
RF24 radio(9,10);
// pipes = { base station addr, 1Node addr, 2Node addr };
uint64_t pipes[3] = { 0xF0F0F0F0D2LL, 0xF0F0F0F0E1LL, 0xF0F0F0F0E2LL};

//*********** CHANGE THIS NODE_INDEX for each sensor (>=1) *************
int nodeIndex = 2;

void readSensor();
void sendOverRadio();
 
char receivePayload[32];
uint8_t counter=0;
 
//count number of entering into main loop
uint8_t loopCounter=109;  
 
//WATCHDOG
volatile int f_wdt=1;
 
ISR(WDT_vect) {
  if(f_wdt == 0) {
    f_wdt=1;
  } else {
    //Serial.println("WDT Overrun!!!");
  }
}
 
void enterSleep(void) {
  radio.powerDown();
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);   /* EDIT: could also use SLEEP_MODE_PWR_DOWN for lowest power consumption. */
  sleep_enable();
 
  /* Now enter sleep mode. */
  sleep_mode();
 
  /* The program will continue from here after the WDT timeout*/
  sleep_disable(); /* First thing to do is disable sleep. */
 
  /* Re-enable the peripherals. */
  power_all_enable();
}
 
 
void setup() {
  //WATCHDOG
  /* Clear the reset flag. */
  MCUSR &= ~(1<<WDRF);
  /* In order to change WDE or the prescaler, we need to
   * set WDCE (This will allow updates for 4 clock cycles).
   */
  WDTCSR |= (1<<WDCE) | (1<<WDE);
  /* set new watchdog timeout prescaler value */
  WDTCSR = 1<<WDP0 | 1<<WDP3; /* 8.0 seconds */
  /* Enable the WD interrupt (note no reset). */
  WDTCSR |= _BV(WDIE);
 
  //CONFIGURE DHT
  pinMode(LEDPIN, OUTPUT);
  //make it blink at startup
  digitalWrite(LEDPIN, HIGH);
  delay(500);
  digitalWrite(LEDPIN, LOW);
  dht.begin();
 
  //CONFIGURE RADIO
  radio.begin();
  // Enable this seems to work better
  radio.enableDynamicPayloads();
  radio.setAutoAck(1);
  radio.setDataRate(RF24_250KBPS);
  radio.setPALevel(RF24_PA_MAX);
  radio.setChannel(76);
  radio.setRetries(15,15);
  radio.setCRCLength(RF24_CRC_8);
  radio.openWritingPipe(pipes[nodeIndex]);
  radio.openReadingPipe(1,pipes[0]);
  radio.startListening();
  radio.printDetails();
}
 
void loop() {
  if(f_wdt == 1) {
    loopCounter ++;
    if (loopCounter > 6) {
      // 110 *8 = 880s = 14.6min @ 16mhtz
      readSensor();
      sendOverRadio();
      loopCounter = 0;
    }
    f_wdt = 0;
    enterSleep();
  } else {
    //nothing
  }
}
 
void sendOverRadio() {
  radio.powerUp();
  //prepare 
  uint8_t data1 = 0;
  char temp[5];
  bool timeout=0;
  uint16_t nodeID = pipes[nodeIndex] & 0xff;
  char buffer[12];
  char outBuffer[32]="";
  unsigned long send_time, rtt = 0;
 
  //data1 is a counter
  data1 = counter++;
  if ( counter > 999 ) counter = 0;
 
  // Append the hex nodeID to the beginning of the payload
  sprintf(outBuffer,"%2X",nodeID);
  strcat(outBuffer,",");
  sprintf(temp,"%03d",data1);
  strcat(outBuffer,temp);
  strcat(outBuffer,",");
 
  //read sensor
  strcat(outBuffer,dtostrf(temperature, 4,2, buffer));
  strcat(outBuffer,",");
  strcat(outBuffer,dtostrf(humidity, 4,2, buffer));
 
  // Stop listening and write to radio
  radio.stopListening();
 
  // Send to hub
  radio.write( outBuffer, strlen(outBuffer));
  send_time = millis();
 
  //wait response
  radio.startListening();
  delay(20);
  while ( radio.available() && !timeout ) {
      uint8_t len = radio.getDynamicPayloadSize();
      radio.read( receivePayload, len);
 
      receivePayload[len] = 0;
      // Compare receive payload with outBuffer
      if ( ! strcmp(outBuffer, receivePayload) ) {
          rtt = millis() - send_time;
      }
 
      // Check for timeout and exit the while loop
      if ( millis() - send_time > 1000 ) {
          timeout = 1;
      }
 
      delay(10);
  } // End whilevcfr
}
 
void readSensor() {
  digitalWrite(LEDPIN, HIGH);
  delay(200);
  bool farenheit = true;
  temperature = dht.readTemperature(farenheit);
  humidity = dht.readHumidity();
  
  digitalWrite(LEDPIN, LOW);
}
