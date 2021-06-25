/* --------------------------------------------------
    Switcher2 Dosentest Smart Switch
           
    for proof of concept Switcher 2 MQTT
    schaltet led ein und aus je nach empfangenre payload

    Pin 12/14 werden für Dosen-Select verwendet

    0/0  -> Dose 1
    0/1  -> Dose 1
    1/0  -> Dose 3
    1/1  -> Dose 4
    
    Pin 13 hat LED, welche Dose simuliert

    Script subskribiert Topic cmnd/diyN/POWER 

    kann als Beispiel für eigene Weuterentwicklung dienen.
    Ideen von hier (mit Dank)
    http://esp8266-server.de/EEPROM.html

    Peter K. Boxler, September 2018
/* --------------------------------------------------*/

#define ESP8266

/* select ESP8266 or ESP32 mittels define */

#if defined ESP8266
#include <ESP8266WiFi.h>
const int led = 13;   // use 13 für Huzzah 6288 
const int pin1 = 12;   // Dosenselect 1          
const int pin2 = 14;   // Dosenselect 2   
const int interruptPin = 2; //    für taster
#else
#include <WiFi.h>
const int led = 13;   // andere Werte für esp32 ! 
const int pin1 = 12;   // Dosenselect 1          
const int pin2 = 14;   // Dosenselect 2  
const int interruptPin = 0; //Flash button on board     für  
#endif

#include <PubSubClient.h>
#include <EEPROM.h>

/* diese Werte anpassen   <<--------- */
const char* ssid = "P-NETGEAR";           // WLAN SSID
const char* password = "hermannelsa";    // WLAN Passwort
// const char* ip_adr_broker = "192.168.1.153";
const char* ip_adr_broker = "192.168.1.121";
const char* sub_topic1 = "cmnd/dose1/POWER";
const char* sub_topic2 = "cmnd/dose2/POWER";
const char* sub_topic3 = "cmnd/dose3/POWER";
const char* sub_topic4 = "cmnd/dose4/POWER";
const char* pub_topic1 = "stat/dose1/POWER";
const char* pub_topic2 = "stat/dose2/POWER";
const char* pub_topic3 = "stat/dose3/POWER";
const char* pub_topic4 = "stat/dose4/POWER";

const char* lwt_topic = "switcher2/switch/lw";


String last_will_msg = "Verbindung verloren zu mqtt dose: ";

const char*   publish_topic;
/* diese Werte anpassen   <<--------- */

const char* user_id="switcher2";
const char* password_mqtt =  "itscool";


int stat_pin1;
int stat_pin2;
int dosennummer;
int dosenstatus;        // variable für den aktuellen Status der Dose 1=ein, 0= aus
long time_lastMsg = 0;

// IP-Adr des MQTT Brokers  
const char* mqtt_server = ip_adr_broker;        // IP-AD MQTT Broker

WiFiClient espClient;
PubSubClient client(espClient);

char msg[50];
int value = 0;

struct Dose_struct {
  unsigned long id;
  int dosennummer;
  int einaus;
};
int nekst_free;
String the_sketchname;

//------------------------------------------------
// displays at startup the Sketch running in the Arduino
void display_Running_Sketch (void){
  String the_path = __FILE__;
  int slash_loc = the_path.lastIndexOf('/');
  String the_cpp_name = the_path.substring(slash_loc+1);
  int dot_loc = the_cpp_name.lastIndexOf('.');
  the_sketchname = the_cpp_name.substring(0, dot_loc);

  Serial.print("\nRunning Sketch: ");
  Serial.println(the_sketchname);
  Serial.print("Compiled on: ");
  Serial.print(__DATE__);
  Serial.print(" at ");
  Serial.print(__TIME__);
  Serial.print("\n");
}


//------------------------------------------------ 
// Write any data structure or variable to EEPROM
int EEPROMAnythingWrite(int pos, char *zeichen, int lenge)
{
  for (int i = 0; i < lenge; i++)
  {
    EEPROM.write(pos + i, *zeichen);
    zeichen++;
  }
  return pos + lenge;
}

 //------------------------------------------------
// Read any data structure or variable from EEPROM
int EEPROMAnythingRead(int pos, char *zeichen, int lenge)
{
  for (int i = 0; i < lenge; i++)
  {
    *zeichen = EEPROM.read(pos + i);
    zeichen++;
  }
  return pos + lenge;
}

//------------------------------------------------
void setup_wifi() {
   delay(100);

    Serial.println("Conneting to WiFi --------");
  // We start by connecting to a WiFi network
    Serial.print("Connecting to ");
    Serial.println(ssid);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) 
    {
      delay(500);
      Serial.print(".");
    }
  randomSeed(micros());
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("My IP address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Broker IP address: ");
  Serial.println(ip_adr_broker); 
  Serial.println("Done Conneting to WiFi --------");
  
}
//------------------------------------------------

void schalten ( unsigned int how)
{
  Dose_struct dose;       /* Struct zum Schreiben nach EEPROM  */
  Dose_struct dose2;      /* Struct zum Lesen aus EEPROM  */
  
 switch (how)
 { 
  
  case 0:
    Serial.println("Muss Led ausschalten");
    digitalWrite(led, LOW); 
    dosenstatus = 0;
    client.publish(publish_topic, "OFF", true);
    Serial.print("published topic: ");   
    Serial.println(publish_topic);       
    break;
  
  case 1:
    Serial.println("Muss Led einschalten");
    digitalWrite(led, HIGH);   // LED on
    dosenstatus = 1;
    client.publish(publish_topic, "ON", true);
    Serial.print("published topic: ");   
    Serial.println(publish_topic);   
    // Store structure (struct) to EEPROM 
    break;
    
  default:
    Serial.println("Error: Ist weder ein noch aus");
   // nothing to do
  break;
  
 } 
  Serial.println("Schreibe Zustand nach EEProm");
    dose.id=123456;
    dose.dosennummer = dosennummer;
    dose.einaus=how;
    nekst_free =  EEPROMAnythingWrite(100, reinterpret_cast<char*>(&dose), sizeof(dose)); 

  EEPROM.commit();
  
  Serial.println("Check Read struct dose");
  // Read structure (struct) from EEPROM
  nekst_free = EEPROMAnythingRead(100, reinterpret_cast<char*>(&dose2), sizeof(dose2));
  Serial.println("DoseID = " + String (dose2.id) + " Dosennumer = " + String(dose2.dosennummer) +  " , einaus = " + String(dose2.einaus));
  Serial.println("");
    
}
//------------------------------------------------
//This partgram get executed when interrupt is occures i.e.change of input state
void handleInterrupt() { 
    Serial.println("Interrupt Detected"); 
    if (dosenstatus == 0)  schalten ( 1);
    else schalten (0);
}

//------------------------------------------------
void callback(char *topic, byte *payload, unsigned int length) {
  Serial.println  ("Message eingetroffen-------------");
  Serial.print    ("Topic ist : [");
  Serial.print    (topic);
  Serial.println  ("]");

  Serial.print    ("Payload ist : [");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println("]");
  Serial.println("Publish Topic: ");
  Serial.println (publish_topic);
    
        if (!strncmp((char *)payload, "ON", length)) {
           schalten (1);

        } else if (!strncmp((char *)payload, "OFF", length)) {
          schalten(0); 

        }
  
}

//--- End Callback ---------------------------------------------


//------------------------------------------------
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) 
  {
     Serial.print("Attempting MQTT connection...Client-ID: ");
    client.setServer(mqtt_server, 1883);
    // Create a random client ID
    String clientId = the_sketchname;
    clientId += String(random(0xffff), HEX);
    Serial.println (clientId);
    // Attempt to connect
    char last_will[45];
    last_will_msg.toCharArray(last_will,45);

    
//  if (client.connect(clientId.c_str()))
    if (client.connect(clientId.c_str(), user_id,password_mqtt, lwt_topic ,0 , false,last_will))
    {
      Serial.println("connected to broker");
     //once connected to MQTT broker, subscribe command if any
     if (dosennummer == 3) {
        client.subscribe(sub_topic3);
        Serial.print ("Subscribe Topic: ");
        Serial.println(sub_topic3);
     }
     else {
        client.subscribe(sub_topic4);
        Serial.print ("Subscribe Topic: ");
        Serial.println(sub_topic4);
     }
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      Serial.println("Ist IP-Adr des brokers richtig ?");
      // Wait 6 seconds before retrying
      delay(6000);
    }
  }
} //end reconnect()
//------------------------------------------------

void setup() {

  Dose_struct dose2;

  Serial.begin(115200);
  delay(3000);
    EEPROM.begin(255);
   Serial.println();
  Serial.println("Starting Setup --------");
   display_Running_Sketch();
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  pinMode(led, OUTPUT);
  pinMode(pin1, INPUT);
  pinMode(pin2, INPUT);
  pinMode(interruptPin, INPUT_PULLUP);
  stat_pin1 = digitalRead(pin1);
  stat_pin2 = digitalRead(pin2);
  digitalWrite(led, LOW);         // led aus bei start

    Serial.print ("Pin1: ");   Serial.println(stat_pin1);
    Serial.print ("Pin2: ");   Serial.println(stat_pin2);
     
  delay(2000);
  attachInterrupt(digitalPinToInterrupt(interruptPin), handleInterrupt, FALLING);

  if (stat_pin1 == LOW and stat_pin2 == LOW)
   {
    dosennummer = 1;
    publish_topic = pub_topic1;
  }
    
  if (stat_pin1 == LOW and stat_pin2 == HIGH)
   {
    dosennummer = 2;
    publish_topic = pub_topic2;
  }
  
  if (stat_pin1 == HIGH and stat_pin2 == LOW)
  {
    dosennummer = 3;
    publish_topic = pub_topic3;
  }
  if (stat_pin1 == HIGH and stat_pin2 == HIGH)
  {
    dosennummer = 4;
    publish_topic = pub_topic4;
  }
   
   Serial.print ("Ich bin Dose: ");
   Serial.println (dosennummer);
   
   last_will_msg = last_will_msg + "";

   Serial.println("Read struct dose");
  // Read structure (struct) from EEPROM
  nekst_free = EEPROMAnythingRead(100, reinterpret_cast<char*>(&dose2), sizeof(dose2));
  Serial.println("DoseID = " + String (dose2.id) + " Dosennumer = " + String(dose2.dosennummer) +  " , einaus = " + String(dose2.einaus));
   if (dose2.id != 123456) {
    Serial.println("id nicht passend, also nichts machen");
    }
  else {
    Serial.println("alte Werte gefunden, also entsprechend schalten");
    dosennummer = dose2.dosennummer;
    schalten(dose2.einaus);
    
  }
   
   Serial.println("Done Setup --------");
}

//------------------------------------------------
void loop() {
  if (!client.connected()) {
    reconnect();
    }
  client.loop();

  long now = millis();
  
  if (now - time_lastMsg > 24000) {
  	Serial.println("waiting for work...");
     time_lastMsg = now;
  
  }
}

/* ---------------------------------------------*/
