#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "DHT.h"
#include "printf.h"

#include <avr/sleep.h>
#include <avr/power.h>
#include <avr/wdt.h>
 
//DHTSENSOR
#define DHTPIN 2     // what digital pin we're connected to
#define LEDPIN 3	 // digital pin with an LED
#define DHTPIN2 4     // what digital pin we're connected to

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
// Note that older versions of this library took an optional third parameter to
// tweak the timings for faster processors.  This parameter is no longer needed
// as the current DHT reading algorithm adjusts itself to work on faster procs.
DHT dht(DHTPIN, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);

float temperature;
float humidity;
float temperature2;
float humidity2;
 
// NRF24L01
// Set up nRF24L01 radio on SPI pin for CE, CSN
RF24 radio(9,10);
// Example below using pipe5 for writing
const uint64_t pipes[2] = { 0xF0F0F0F0E1LL, 0xF0F0F0F0D2LL };
 
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
    Serial.println("WDT Overrun!!!");
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
 
  Serial.begin(57600);
  Serial.println("DHT Read and Send!");
  printf_begin();
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
  dht2.begin();
 
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
  radio.openWritingPipe(pipes[0]);
  radio.openReadingPipe(1,pipes[1]);
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
  uint16_t nodeID = pipes[0] & 0xff;
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
  strcat(outBuffer,",");
  strcat(outBuffer,dtostrf(temperature2, 4,2, buffer));
  strcat(outBuffer,",");
  strcat(outBuffer,dtostrf(humidity2, 4,2, buffer)); 
  // Stop listening and write to radio
  radio.stopListening();
 
  // Send to hub
  Serial.print("Sending: '");
  Serial.print(outBuffer);
  Serial.println("'");
  if ( radio.write( outBuffer, strlen(outBuffer)) ) {
    Serial.println("Send successful");
  } else {
    Serial.println("Send failed");
  }
 
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
          Serial.println("inBuffer --> rtt:");
          Serial.println(rtt);
      }
 
      // Check for timeout and exit the while loop
      if ( millis() - send_time > 1000 ) {
          Serial.println("Timeout!!!");
          timeout = 1;
      }
 
      delay(10);
  } // End whilevcfr
}
 
void readSensor() {
  digitalWrite(LEDPIN, HIGH);
  delay(200);
  bool farenheit = true;
  bool force = true;
  temperature = dht.readTemperature(farenheit, force);
  humidity = dht.readHumidity();
  temperature2 = dht2.readTemperature(farenheit, force);
  humidity2 = dht2.readHumidity();
  
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
  }
  
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print(" %\t");
  Serial.print("Temperature: ");
  Serial.print(temperature);
  if (farenheit) {
  	Serial.print(" *F ");
  } else {  
  	Serial.print(" *C ");
  }
  Serial.print("\n");
  digitalWrite(LEDPIN, LOW);
}