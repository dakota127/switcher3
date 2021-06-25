
/*

   List all i2c devices
  
  http://www.raspibo.org/wiki/index.php?title=Arduino,_ESP_and_i2c_devices

 This project permits to list the Id-s of the devices conncted to the I2C bus.
 I have successfully tested this program on an ESP-12 (ESP8266) using the Arduino IDE.
   -> GP04 (SDA)
   -> GND
   -> +3V3
   -> GP05 (SCL)

---------------------------------------------------*/

#include <Wire.h>
 
void setup()
{
  Wire.begin();
 
  Serial.begin(115200);
  Serial.println("\nI2C Scanner");
}
 
void loop()
{
  byte error, address;
  int nDevices;
 
  Serial.println("Scanning...");
 
  nDevices = 0;
  for(address = 1; address < 127; address++ )
  {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
 
    if (error == 0)
    {
      Serial.print("I2C device found at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.print(address,HEX);
      Serial.println("  !");
 
      nDevices++;
    }
    else if (error==4)
    {
      Serial.print("Unknow error at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.println(address,HEX);
    }
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found\n");
  else
    Serial.println("done\n");
 
  delay(5000);           // wait 5 seconds for next scan
}
