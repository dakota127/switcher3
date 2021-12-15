
/* **************************************************************************
    Switcher  Temp Sensor Sketch fuer BME280
    mit Deep Sleep

    topic für switcher wetter ist : 'switcher/wetter/data'
    payload :   indoor/battstatus/sensorstatus/elapsed_time_ms/TEMP/HUM
    oder
    payload :   outdoor/battstatus/sensorstatus/elapsed_time_ms/TEMP/HUM

    Input pin 14 wird benutzt, um indoor oder outdoor zu setzen
    pin14 low:    outdoor
    pin14 high:   indoor

    Programmierung gemäss dieser Quelle im Netz
    https://github.com/z2amiller/sensorboard/blob/master/PowerSaving.md

    Also mit watchdog timer und wifi-Behandlung

    Debug-Output (auf Serial) mittels Preprocessor gemässe Adreas Spiess, siehe YouTube
    https://www.youtube.com/watch?v=1eL8dXL3Wow&t=513s
  
    Dazugehörige Library hier:
    https://youtu.be/1eL8dXL3Wow
    
    Weitere Inspiration zur Energiefrage;
    https://www.bakke.online/index.php/2017/05/21/reducing-wifi-power-consumption-on-esp8266-part-1/

    und auch vor allem von hier:
    https://blog.voneicken.com/2018/lp-wifi-esp8266-1/

    Mit Dank auch an Michel Deslierres
    https://www.sigmdel.ca/michel/program/esp8266/arduino/watchdogs_en.html
    
    Battery Level:
    Entweder wird direkt VCC gemessen (wenn ein LiFePo4 direkt angeschlossen ist) 
    oder
    es wird die Batteriespannung mittels einem abschaltbaren Spannungsteiler gemessen. Dies ist bei LiPo
    Accus nötig, da dort ein Voltage Regulator nötig ist (wegen deren max. 4.2 Volt wenn voll geladen).

 
  Januar 2019, by Peter B.
 *************************************************************************************/

// defines für verschiedene Programm-Varianten
//
//*************************************************
#define TEST     // uncomment für Testumgebung
//*************************************************
//

//  CONNECT MQTT --------
//The value of rc indicates success or not:
//0: Connection successful 
//1: Connection refused - incorrect protocol version 
//2: Connection refused - invalid client identifier 
//3: Connection refused - server unavailable 
//4: Connection refused - bad username or password 
//5: Connection refused - not authorised 6-255: Currently unused.
//
#if defined TEST
#define DEBUGLEVEL 1      // für Debug Output, für Produktion DEBUGLEVEL 0 setzen !
// Time to deepsleep (in seconds):
const int sleepTimeS = 60;        // 60 ist etwa 1 min 
#else
#define DEBUGLEVEL 1      // für Debug Output, für Produktion DEBUGLEVEL 0 setzen !
// Time to deepsleep (in seconds):
const int sleepTimeS = 2000;        // 2000 ist etwa 30 Minuten
#endif


// zum inkludieren der richtigen Lib (ESP32 oder ESP8266)
// select ESP8266 or ESP32 mittels define
#define ESP8266

// #define LAST_WILL      // auskommentieren macht keinen MQTT LastWill
#define MQTT_AUTH         // auskommentieren wenn MQTT connect ohne userid/password 

#if defined LAST_WILL      // beide geht nicht !
#undef MQTT_AUTH
#endif

#define HOSTNAME "mysensor"
#define STAIIC_IP

extern "C" {
#include "user_interface.h"
}

// ------------------------------------------------------
#define TICKER_TIME_MS     10000  // Zeit für Watchdog Interrrupt

#define   VCC_ADJ   0.975   // Korrekturfaktor bei VCC Messung (kalibriert mit Voltmeter)

// ---- includes -------------------------------------------
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Ticker.h>
#include <PubSubClient.h>
#include <DebugUtils.h>     // Library von Adreas Spiess
#include "sw_credentials.h"    // eigene crendentials

// esp8266 oder esp32 ----------------------
#if defined ESP8266
  #include <ESP8266WiFi.h>
  const int indoor_outdoor_pin = 14;      // um indoor/outdoor festzustellen
  const int adc_sensor_pin = 12;          // 1: sensor/spannungsteiler ein, 0: aus
#else
  #include <WiFi.h>
  const int indoor_outdoor_pin = 14;     // um indoor/outdoor festzustellen  
  const int ledpin = 27;      // not used
#endif

//Static IP address configuration
IPAddress staticIP  (192, 168, 1, 231); //ESP static ip
IPAddress gateway   (192, 168, 1, 1);   //IP Address of your WiFi Router (Gateway)
IPAddress subnet    (255, 255, 255, 0);  //Subnet mask
IPAddress dns    (8, 8, 8, 8);  //DNS

const int ipadr_indoor = 161;         // pos 3 der IPAdr, wird zur runtime gesetzt, 
const int ipadr_outdoor = 162;         // nachdem indoor oder outdoor bekannt ist

Ticker sleepTicker;
Adafruit_BME280 bme; // I2C
WiFiClient espClient;
PubSubClient client(espClient);


ADC_MODE(ADC_VCC);          // nötig bei VCC Messung


// werte kommen aus sw_credentials.h 
const char* wifi_ssid =       WAN_SSID ;
const char* wifi_password =   WAN_PW;
const char* mqtt_user_id =    MQTT_USER;
const char* mqtt_password =   MQTT_PW;
const char* mqtt_broker_ip =  BROKER_IP;



//Variables Sensor
int       chk;
float     hum;                    //Stores humidity value
float     temp;                   //Stores temperature value
bool      sensor_status;          // status sensor true/false
long      previousMillis = 0;     // will store last tim
long      interval = 500;        // interval  (milliseconds)
unsigned long start_time_ms;      
unsigned long elapsed_time_ms;
float     voltage_value_raw;      //Define variable to read ADC data
float     voltage_value;          //Define variable to read ADC data

char      battery_string[15];     // für Batterie Zustand
char      sensor_string[15];     // für Sensor Zustand
String    sens_status;    
long      lastMsg = 0;
char      msg[50];
int       value = 0;
String    batt_status;
const char*     topic =     "swi/wetter/data";
const char*     topic_lw =  "swi/wetter/lw";
int       inout_door ;       // HIGH: indoor, LOW: outdoor
String    last_will_msg = "Verbindung verloren zu Sensor: ";
String    the_sketchname;
unsigned long currentMillis;
bool      mqtt_status;
#define LED 2 //Define blinking LED pin
  
// The ESP8266 RTC memory is arranged into blocks of 4 bytes. The access methods read and write 4 bytes at a time,
// so the RTC data structure should be padded to a 4-byte multiple.
struct {
  uint32_t crc32;   // 4 bytes
  uint8_t channel;  // 1 byte,   5 in total
  uint8_t ap_mac[6]; // 6 bytes, 11 in total
  uint8_t padding;  // 1 byte,  12 in total
} rtcData;

// Function Prototypes -----------------------

uint32_t calculateCRC32(const uint8_t *data, size_t length);  // CRC function used to ensure data validity
void printMemory();                 // helper function to dump rtc memory contents as hex
void display_Running_Sketch ();     // anzeige der sketch info
void display_Esp_Info();            // Anzeige der ESP Info
void watchdog_sketch();             // Watchdog IR Routine
String batt_voltage () ;            // Messung Batt Voltage
void readSensor ();                 // read sensor
void waitForWifi();                 // wait for Wifi
void setup_wifi();                  // setup wifi
void mqtt_connect();                // connevt mqtt
int getBootDevice();

//-------- Functions ----------------------------------------
// -------------------------------------
void setup() {

   String   msg;
   char     message[50];
   char     elapsed_time_c[5];
   int      ret;
   bool     software_wachtdog = false;
   
   start_time_ms = millis();   // Loop Begin Zeit

  Serial.begin(115200);
  while (!Serial) { }
  DEBUGPRINTLN0 ("Starting Setup --------"); 
  display_Running_Sketch();
  
// dies von hier:
// https://www.sigmdel.ca/michel/program/esp8266/arduino/watchdogs2_en.html
//
  if ( getBootDevice() == 1 ) {
    
    Serial.println("\nWARNING");
    Serial.println("This sketch has just been uploaded over the UART.");
    Serial.println("The ESP8266 will freeze on the first restart.");
    Serial.println("Press the reset button or power cycle the ESP now");
    Serial.println("and operation will be resumed thereafter.");
    while (1) {
        pinMode(LED, OUTPUT); // Initialize the LED pin as an output
        digitalWrite(LED, LOW); // Turn the LED on (Note that LOW is the voltage level)
        delay(500); // Wait for half a second
        yield();
        digitalWrite(LED, HIGH); // Turn the LED off by making the voltage HIGH
        delay(500); // Wait for half a second
        yield();
      }
    }  
/*
  Use watchdog timers.
  Set a timer for the maximum amount of time your polling loop should run.
  This will prevent your device from sitting there for hours at a time with the WiFi 
  radio on trying to associte if your AP is down, for example. 
  The ESP8266 has a built-in Ticker that takes a timeout and a callback.
*/
  sleepTicker.attach_ms (TICKER_TIME_MS, &watchdog_sketch);

// folgender Code thanks to Michel Deslierres
// https://www.sigmdel.ca/michel/program/esp8266/arduino/watchdogs_en.html

 switch (ESP.getResetInfoPtr()->reason) {
    
    case REASON_DEFAULT_RST: 
      // do something at normal startup by power on
      strcpy_P(message, PSTR("Power on"));
      break;
      
    case REASON_WDT_RST:
      // do something at hardware watch dog reset
      strcpy_P(message, PSTR("Hardware Watchdog")); 
      
      break;
      
    case REASON_EXCEPTION_RST:
      // do something at exception reset
      strcpy_P(message, PSTR("Exception"));      
      break;
      
    case REASON_SOFT_WDT_RST:
      // do something at software watch dog reset
      strcpy_P(message, PSTR("Software Watchdog"));
      software_wachtdog = true;
      break;
      
    case REASON_SOFT_RESTART: 
      // do something at software restart ,system_restart 
      strcpy_P(message, PSTR("Software/System restart"));
      break;
      
    case REASON_DEEP_SLEEP_AWAKE:
      // do something at wake up from deep-sleep
      strcpy_P(message, PSTR("Deep-Sleep Wake"));
      break;
      
    case REASON_EXT_SYS_RST:
      // do something at external system reset (assertion of reset pin)
      strcpy_P(message, PSTR("External System"));
      break;
      
    default:  
      // do something when reset occured for unknown reason
      strcpy_P(message, PSTR("Unknown"));     
      break;
  }
  
 

#if defined TEST
  DEBUGPRINTLN1 ("TEST ist gesetzt <------------");
#endif    

  DEBUGPRINT1 ("deepsleep time: ");
  DEBUGPRINTLN1 (sleepTimeS);
  display_Esp_Info();

  if (software_wachtdog)  {
      DEBUGPRINTLN1     ("War Software Watchdog Reset, also mache deepsleep");
      deepsleep();
  }
  
  
  pinMode       (indoor_outdoor_pin, INPUT_PULLUP);   // defines indoor-outdoor
  pinMode       (adc_sensor_pin, OUTPUT);       // Spannungsteiler/Sensor ein/aus     
  DEBUGPRINTLN1 ("Sensor/ADC VCC einschalten");
  digitalWrite  (adc_sensor_pin, HIGH);          // Spannungsteiler/Sensor einschalten
  
  inout_door = digitalRead  (indoor_outdoor_pin);
  if (inout_door == HIGH) {
     DEBUGPRINTLN1 ("Bin Indoor");
     last_will_msg = last_will_msg + "indoor"; 
  }
  else {
     DEBUGPRINTLN1 ("Bin Outdoor");
     last_will_msg = last_will_msg + "outdoor";
  }
 

  DEBUGPRINTLN1 ("Mache WiFi Begin --------");
  // We start by connecting to a WiFi network
  DEBUGPRINT1 ("Connecting to: ");
  DEBUGPRINTLN1 (wifi_ssid);

// setzt static IP je nach indoor/outdoor
  if (inout_door == HIGH) {staticIP[3] = ipadr_indoor;}
  else {staticIP[3] = ipadr_outdoor;}
      
  WiFi.mode(WIFI_STA);
  WiFi.config( staticIP, gateway, subnet ,dns);  
  WiFi.begin( wifi_ssid, wifi_password ); 
  
  Serial.print("bis nach wifi setup msec: "); // time since program started
  Serial.println ( elapsed_time(start_time_ms) );
    
  // default settings for bme280 I2C
  sensor_status = bme.begin();  
  if (!sensor_status) {
     DEBUGPRINTLN0 ("Could not find a valid BME280 sensor, check wiring!");
 //    while (1);        
   }

   if (sensor_status) {
    sens_status = "OK";
   }
   else
   {
    sens_status = "Fehler";
   }
    // sens_stat wird später im MQTT payload verwendet
    
   DEBUGPRINT1  ("bis setup done msec: "); // time since program started
   DEBUGPRINTLN1 ( elapsed_time(start_time_ms));
   DEBUGPRINTLN1 ("\nSetup Done...");

//---------------------------
// nun Sensor lesen, warten auf wiFi und dann MQTT

   readSensor ();
   batt_status = batt_voltage ();
   delay(10);
  
   waitForWifi();           // connect to WiFi, kommt nicht zurück, falls NO connection

 
   DEBUGPRINT1  ("bis wifi da msec: "); // time since program started
   DEBUGPRINTLN1  ( elapsed_time(start_time_ms) );
   mqtt_connect();             // connect to MQTT broker

    DEBUGPRINT1  ("bis mqtt connect msec: "); // time since program started
    DEBUGPRINTLN1 ( elapsed_time(start_time_ms));

    elapsed_time_ms =  elapsed_time(start_time_ms);
    msg = "";
    int elapsed_time_int = (int)elapsed_time_ms;
    sprintf(elapsed_time_c, "%5d", elapsed_time_int);
    
    if (inout_door == HIGH) {
      msg = msg + "indoor/";
    }
    else{
      msg = msg + "outdoor/";
    }
    msg = msg + batt_status;
    msg = msg + "/" + sens_status;
    msg = msg + "/" + elapsed_time_c;
    msg = msg + "/";
    msg = msg + temp;
    msg = msg + "/";
    msg = msg + hum;
  msg.toCharArray(message,50);

  //   while (1) {};            // test, aktiviert den Software Watchdog (nach ca. 3.2 sek)
     
 //   publish sensor data to MQTT broker

    if (!mqtt_status)  {
     DEBUGPRINTLN1  ("Skip sending MQTT, no connection");       
    }
    else
    { 
      DEBUGPRINTLN1  ("Sending this message to MQTT Broker:");
      DEBUGPRINT1   ("topic:   ");
      DEBUGPRINTLN1  (topic);
      DEBUGPRINT1   ("payload: ");
      DEBUGPRINTLN1  (message);
      ret = client.publish (topic, message,1);            // QoS ist 1

      DEBUGPRINT1  ("mqtt publish returns: ");
      DEBUGPRINTLN1  (ret);
    
      currentMillis = millis();

      if(currentMillis - previousMillis > interval) {
    // save the last time 
        delay(1);
        previousMillis = currentMillis;   
        }

    }
    
   watchdog_sketch();
 
}


//------------------------------------------------
void loop() {
 
}


//------------------------------------------------
uint32_t calculateCRC32(const uint8_t *data, size_t length) {
  uint32_t crc = 0xffffffff;
  while (length--) {
    uint8_t c = *data++;
    for (uint32_t i = 0x80; i > 0; i >>= 1) {
      bool bit = crc & 0x80000000;
      if (c & i) {
        bit = !bit;
      }
      crc <<= 1;
      if (bit) {
        crc ^= 0x04c11db7;
      }
    }
  }
 //   DEBUGPRINT1  ("CRC: ");
 //   DEBUGPRINTLN1  (crc);
  return crc;
}
//---------------------------------------------
//prints all rtcData, including the leading crc32
void printMemory() {

   return;
  
  char buf[3];
  uint8_t *ptr = (uint8_t *)&rtcData;
  for (size_t i = 0; i < sizeof(rtcData); i++) {
    sprintf(buf, "%02X", ptr[i]);
    Serial.print(buf);
    if ((i + 1) % 32 == 0) {
      DEBUGPRINTLN1 ();
    } else {
      DEBUGPRINT1 (" ");
    }
  }
  DEBUGPRINTLN1 ();
}


//------------------------------------------------
// displays at startup the Sketch running in the Arduino
void display_Running_Sketch (void){
  String the_path = __FILE__;
  int slash_loc = the_path.lastIndexOf('/');
  String the_cpp_name = the_path.substring(slash_loc+1);
  int dot_loc = the_cpp_name.lastIndexOf('.');
//  String the_sketchname = the_cpp_name.substring(0, dot_loc);
  the_sketchname = the_cpp_name.substring(0, dot_loc);

  
  DEBUGPRINT1 ("\nRunning Sketch: ");
  DEBUGPRINTLN1 (the_sketchname);
  DEBUGPRINTLN1 ("Compiled on: ");
  DEBUGPRINT1 (__DATE__);
  DEBUGPRINT1 (" at ");
  DEBUGPRINT1 (__TIME__);
  DEBUGPRINT1 ("\n");
}

// ------------------------------------
void display_Esp_Info() {

  DEBUGPRINTLN1 ("\nESP Info------");
  DEBUGPRINT1 ("Sdk version: ");
  DEBUGPRINTLN1 (ESP.getSdkVersion());  
  DEBUGPRINT1 ("Core Version: ");
  DEBUGPRINTLN1 (ESP.getCoreVersion().c_str());
  DEBUGPRINT1 ("Boot Version: "); 
  DEBUGPRINTLN1 (ESP.getBootVersion());
  DEBUGPRINT1 ("Boot Mode: "); 
  DEBUGPRINTLN1 (ESP.getBootMode());
  DEBUGPRINT1 ("CPU Frequency MHz: "); 
  DEBUGPRINTLN1 (ESP.getCpuFreqMHz());
  DEBUGPRINT1 ("Reset reason: "); 
  DEBUGPRINTLN1 (ESP.getResetReason().c_str()); 
}
//-------------------------------------
void deepsleep() {

  DEBUGPRINTLN1 ("Sensor/ADC VCC ausschalten");
  digitalWrite  (adc_sensor_pin, LOW);          // Spannungsteiler/Sensor ausschalten 
  DEBUGPRINT1 ("Going into deep sleep for ");
  DEBUGPRINT1 (String(sleepTimeS));
  DEBUGPRINTLN1 (" seconds");

  sleepTicker.detach(); 
 
  ESP.deepSleep(sleepTimeS * 1000000, WAKE_RF_DEFAULT);
  // It can take a while for the ESP to actually go to sleep.
  // When it wakes up we start again in setup().

// wird nie ausgeführt...
  DEBUGPRINTLN1 ("Nach deep sleep...");
  yield();
}

//--- Watchdog Interrupt Routine ---------------------------------------------
void watchdog_sketch() {
  
  DEBUGPRINT1  ("\nwatchdog_sketch, arbeit fertig in: ");
  DEBUGPRINT1  ( elapsed_time(start_time_ms) );
  DEBUGPRINTLN1 (" ms");

  elapsed_time_ms = elapsed_time(start_time_ms);
  // Wenn Watchdog bellt, weill Operation zu lange dauerte
  // Clear Wifi state.
  yield();
  if (elapsed_time_ms <= TICKER_TIME_MS) {
      DEBUGPRINTLN1 ("elapsed_time_ms time ist KLEINER als Tickertime");
    }
  else {
      DEBUGPRINTLN1 ("elapsed_time_ms time ist GROESSER als Tickertime !");
      delay(1);
//    ESP.restart();
      DEBUGPRINT1 ("WiFi Connection status: ");
      DEBUGPRINTLN1  (WiFi.status());
    if (WiFi.status() == WL_CONNECTED) {
      DEBUGPRINTLN1 ("WiFi disconnect..");
      WiFi.disconnect( true );
      delay( 1 );
      WiFi.mode( WIFI_OFF );
      currentMillis = millis();

      if(currentMillis - previousMillis > interval) {
    // save the last time 
        delay(1);
        previousMillis = currentMillis;   
      }
    }
    else {
       DEBUGPRINTLN1 ("WiFi not connected");
    }
   
   }
   
   deepsleep();

}

//------------------------------------------------
String batt_voltage () {
  
  String bat_str;
  delay (10);

  voltage_value_raw = ESP.getVcc();
  voltage_value = (voltage_value_raw / 1024.0) * VCC_ADJ ;
//  voltage_value = analogRead(A0);       //Read ADC
 
  DEBUGPRINT1   ("ADC Value RAW: ");       //Print Message
  DEBUGPRINTLN1   (voltage_value_raw);             //Print ADC value
  DEBUGPRINT1   ("VCC: ");       //Print Message
  DEBUGPRINT1   (voltage_value);             //Print ADC value
  DEBUGPRINTLN1  (" Volt"); 
  delay(1);                             //

  dtostrf(voltage_value, 4, 2, battery_string);
    
  battery_string[4] = '\0';
  bat_str= String(battery_string);
    
  if (voltage_value > 3.0) {
    bat_str = bat_str + " - Perfekt";
    }
  else {
    if (voltage_value > 2.8) {
    bat_str = bat_str + " - Gut";
    }
    else
    {
     bat_str = bat_str + " - Achtung"; 
    }
  } 

 //  DEBUGPRINTLN1  (bat_str); 
      
  return (bat_str);
  
}

//------------------------------------------------
void readSensor () {

    if (!sensor_status) {
      DEBUGPRINT1 ("\n");
      DEBUGPRINTLN1 ("Sensorfehler, keine Messung ");
      temp = 11.1;
      hum  = 11.1;
      return;
    }

 // -------  aktiviere dies um den Software Watchdog des ESP8266 zu aktivieren ---------  
 //   simuliert fehler im sketch, endloser loop
 //   wird nach ca. 3 sec vom Software Watchdog des ESP unterbrochen, es erfolgt ein reset
 //   while (1) {};
 // -------------------------------------------------------------------------------------
     
    DEBUGPRINT1 ("\n");
    DEBUGPRINTLN1 ("Messung: ");
    temp = bme.readTemperature();
    hum = bme.readHumidity();
    hum = round(hum*10) / 10.0;
    temp = round(temp*10) / 10.0;
    DEBUGPRINT1  ("Temperature = ");
    DEBUGPRINT1 (temp);
    DEBUGPRINTLN1 (" *C");

    DEBUGPRINT1 ("Humidity = ");
    DEBUGPRINT1 (hum);
    DEBUGPRINTLN1 (" %");

}

//------------------------------------
void wifi_details()
{
   DEBUGPRINTLN1    ("");
   DEBUGPRINT1    ("WiFi connected to SSID: ");
   DEBUGPRINTLN1    (WiFi.SSID());
   DEBUGPRINT1    ("IP address: ");
   DEBUGPRINTLN1    (WiFi.localIP());
   DEBUGPRINTLN1    ("\nWiFi Details:");
   WiFi.printDiag(Serial);
}

//------------------------------------------------
void waitForWifi() {
  DEBUGPRINT1 ("\n");
  DEBUGPRINT1 ("Waiting for WiFi.");

int retries;

  delay (300);        // inital delay, weniger als 300 dauert es sowieso nicht...
 
   retries = 0;
   while (WiFi.status() != WL_CONNECTED)  { 
    retries++;
    if (retries > 30) break;      // max number retries
    delay(100);  
    DEBUGPRINT1  ("."); 
   }
    
  if (WiFi.status() == WL_CONNECTED) {
    wifi_details();
    return;
  }

  
  // no connection...
  DEBUGPRINTLN1  ("\nno wifi connection");
  // gehe mal schlafen, ev. ist es dann besser....
  deepsleep();
}


//------------------------------------------------
void mqtt_connect() {
  // Verbindung zum MQTT Broker
  // Mache 2 Versuche zu verbinden

  mqtt_status = false;
  for (int i=0; i < 2; i++) {

    DEBUGPRINT1 ("\nAttempting MQTT connection...Client-ID: ");
    client.setServer(mqtt_broker_ip, 1883);
    // Create a random client ID
    String clientId = the_sketchname;
    clientId += String(random(0xffff), HEX);
    DEBUGPRINTLN1 (clientId);

    char last_will[45];
    last_will_msg.toCharArray(last_will,45);

#if defined LAST_WILL
// connect mit Angabe eines last will
    DEBUGPRINTLN1 ("MQTT MIT userid/pw und lastwill message");
    // clientId.c_str()
   if (client.connect(clientId.c_str(), mqtt_user_id,mqtt_password, topic_lw ,0 , false,last_will))
    {
#else
 // connect OHNE Angabe eines last will
#if defined MQTT_AUTH 
    DEBUGPRINTLN1 ("MQTT MIT userid/pw");
    DEBUGPRINTLN1 (mqtt_user_id);
    DEBUGPRINTLN1 (mqtt_password);
    DEBUGPRINTLN1 (clientId.c_str());
    if (client.connect(clientId.c_str(), mqtt_user_id,mqtt_password ))
    {
#else
    DEBUGPRINTLN1 ("MQTT OHNE userid/pw");
   if (client.connect(clientId.c_str() ))
    {
#endif

#endif
      DEBUGPRINTLN1  ("MQTT connected");
      mqtt_status = true;
      break;
       }
    else 
    {
      DEBUGPRINT1 ("MQTT connect failed, rc=");
      DEBUGPRINT1 (client.state());
      DEBUGPRINTLN1 (" try again in 1 second");
 
    // Wait  1 seconds before retrying
      currentMillis = millis();
      if(currentMillis - previousMillis > interval * 2) {
        delay(1);
        previousMillis = currentMillis;   
      }
    }
}

    }//end mqtt_connect()


// ----------------------------------------------
int getBootDevice(void) {
  int bootmode;
  asm (
    "movi %0, 0x60000200\n\t"
    "l32i %0, %0, 0x118\n\t"
    : "+r" (bootmode) /* Output */
    : /* Inputs (none) */                
    : "memory" /* Clobbered */           
  );
  return ((bootmode >> 0x10) & 0x7); 
}
    
//------------------------------------------------

/*
 *  Returns the number of milliseconds elapsed_time_ms since  start_time_ms.
 */  
unsigned long elapsed_time (unsigned long start_time)
{
  return millis() - start_time;
}

//---------------------------------------------
