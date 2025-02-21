
#include <SoftwareSerial.h>
#include <SparkFunESP8266WiFi.h>
#include <Stepper.h>

#define lap 2048

const char mySSID[] = "AIE_509_2.4G";
const char myPSK[] = "addinedu_class1";
const char server[] = "192.168.0.41";
const int serverPort = 8888;  // 서버 포트

ESP8266Client client;

unsigned long lastReceiveTime = 0; // 마지막 데이터 수신 시간
const unsigned long receiveInterval = 2000; // 2초마다 서버 체크
bool serverOk = false;  

Stepper stepperMotors[4] = {  
  Stepper(lap, 10, 11, 12, 13),
  Stepper(lap, 4, 5, 6, 7),
  Stepper(lap, A0,A1,2,3),
  Stepper(lap, A2, A3, A4, A5) 
}; 

void connectWifi(){
  while (esp8266.begin() != true)
  {
    Serial.print("Error connecting to ESP8266.");
	  delay(1000);
  }
  
  if (esp8266.status() <= 0)
  {
    while (esp8266.connect(mySSID, myPSK) < 0)
      delay(1000);
  }
  delay(1000);
  Serial.println("WiFi 연결 완료!\n"); 
}

void connectServer()
{
  while (client.connect(server, serverPort) <= 0)
  {
    Serial.println(F("Failed to connect to server.\n"));
    delay(1000);
  }
  Serial.println(F("Connected.\n")); 

  const uint8_t message[] = { 'A', 'T', 1 };  
  client.write(message, sizeof(message));
}

void receiveFromServer()
{
  int recv_size = 0;
  char recv_buffer[64];
  memset(recv_buffer, 0, sizeof(recv_buffer));
  
  // data 받기  
  if (client.available() > 0){
    recv_size = client.readBytesUntil('\n', recv_buffer, sizeof(recv_buffer) - 1);
    
    Serial.print("Raw received data:");
    Serial.println(recv_buffer);

    //  Filter: TCP 수신 정보 (e.g. +IPD ~ :)제외 
    char* realData = strstr(recv_buffer, ":");
    if(realData != nullptr){
      realData++;
      Serial.print("Extracted data: ");
      Serial.println(realData);
      parse(realData);
    } else {
      Serial.println("No valid data found");
      return;
    }
  
    
  }  
}

void parse(char* data){
  if (data == nullptr) return; 
  
  char cmd[2]; 
  memset(cmd, 0x00, sizeof(cmd)); 
  memcpy(cmd, data, 2);
  Serial.println(cmd);

  uint8_t status =(uint8_t)data[2];
  
  if (strncmp(cmd, "AT", 2) == 0 && status == 2 ){    // staus 0x02은 연결성공 
    serverOk = true; 
    Serial.println("이제부터 명령을 처리합니다.");
  }

  if (serverOk){ 
    if (strncmp(cmd, "PC", 2) == 0){
      uint8_t motorID = static_cast<uint8_t>(data[3]);
      uint8_t quantity = static_cast<uint8_t>(data[4]);

      
      Serial.print("Status: ");
      Serial.println(status);
      Serial.print("Motor ID: ");
      Serial.println(motorID);
      Serial.print("Quantity: ");
      Serial.println(quantity);

      if (motorID >= 1 && motorID <= 4 && status == 0) {
        rotateMotor(motorID, quantity);
      } 
      else {
        Serial.println("Invalid motor ID!");
      }
      
    }
  }
}

void rotateMotor(uint8_t id_, uint8_t quantity_)
{
  const char* motorNames[] = { "1st", "2nd", "3rd", "4th" };

  if (quantity_ == 0) {
    Serial.println("Error: Quantity cannot be negative!");
    return;
  }
  int motorIndex = id_ - 1;  // 배열 인덱스로 변환 (1~4 → 0~3)
  Serial.print(motorNames[motorIndex]);
  Serial.println(" motor's rotated!");

  stepperMotors[motorIndex].setSpeed(10);  // 속도를 10 RPM으로 설정

  // 모터 회전 실행 (너무 크지 않게 조정)
  stepperMotors[motorIndex].step(lap * quantity_ );
 
  const uint8_t message[] = { 'P', 'C', 1 };  
  client.write(message, sizeof(message));
}
void setup() 
{
  Serial.begin(9600);
  connectWifi();

  connectServer();
}

void loop() 
{
 
  unsigned long currentMillis = millis();
  if (currentMillis - lastReceiveTime >= receiveInterval) {
    lastReceiveTime = currentMillis;
    receiveFromServer();
  }
}