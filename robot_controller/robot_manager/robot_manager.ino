#include <Wire.h>
#include <MPU6050.h>
#include <MFRC522.h>
#include <SPI.h>

// Constant
// IR 센서 핀 설정
const int IR_L = A1;  // 왼쪽 IR 센서
const int IR_C = A2;  // 가운데 IR 센서
const int IR_R = A3;  // 오른쪽 IR 센서

// 모터 드라이버 핀 설정 (L9110S 기준)
const int MOTOR_R_IN1 = 6;   // 오른쪽 모터 방향 1 HIGH 시 전진
const int MOTOR_R_IN2 = 5;   // 오른쪽 모터 방향 2 HIGH 시 후진

const int MOTOR_L_IN3 = 10;  // 왼쪽 모터 방향 1 HIGH 시 후진
const int MOTOR_L_IN4 = 11;  // 왼쪽 모터 방향 2 HIGH 시 전진

// 초음파 센서 핀
const int TRIG_PIN = 8;
const int ECHO_PIN = 12;

// 장애물 감지 거리 (단위: cm)
const int OBSTACLE_DISTANCE = 10;

// LED와 Fuzzer 핀
const int GREEN_LED = 4;  // 주행 중 초록 LED
const int RED_LED = 7;    // 장애물 감지 시 빨간 LED
const int YELLOW_LED = 9;

const int BUZZER_PIN = A0; // Fuzzer

const int MPU_UPDATE_INTERVAL = 10; // 센서 데이터 10ms 주기로 갱신
const int ERROR_MARGIN = 10; // 20도 이내 오차 허용

const HardwareSerial* WifiSerial = &Serial1;

const int SS_PIN = 53;
const int RST_PIN = 54;

// Variables
MPU6050 mpu;
MFRC522 mfrc522(SS_PIN, RST_PIN);

float targetYaw = 0;  // 목표 방향 (처음 시작 방향)
float gyroZ_offset = 0; // 자이로 Z축 오프셋 (드리프트 보정)
float yaw = 0;

float previousError = 0;
float integral = 0;
unsigned long lastTime = 0;

// 초기 모터 속도 (0~255)
int motorSpeed = 160;

uint32_t* tagList;

int cntMask = 0;

bool prevDetected = false;

// Esp01 Status
enum EspStatus {
  STATUS_YES,
  STATUS_NO,
};

enum RobotStatus {
  HOME, WAIT, STOP, MOVING_TO_SEC,
  GETTING_PRODUCT, MOVING_TO_PP, MOVING_TO_HP
};

enum Command {
  NOTTING, GET_ORDER, RESUME,
  MOVE_TO_PP, MOVE_TO_HP
};

// status init
EspStatus espStatus;
RobotStatus robotStatus;
Command command;

// Fuctions
// === 속도 설정 함수 ===
void setMotorSpeed(int leftSpeed, int rightSpeed);
// === 모터 제어 함수 ===
void moveForward();
void moveBackward();
void turnLeft();
void turnRight();
void gyroturnRight();
void gyroturnLeft();
void stopMotors();
void lineTrace();
// === 초음파 센서 거리 측정 함수 ===
long getDistance();
// === 장애물 감지 및 경고 ===
bool checkObstacle();
void updateYaw();
// === 자이로 Z축 오프셋 보정 함수 ===
void calibrateGyroZ();
// Yaw 변화율 가져오기
float getYawRate();
// 현재 Yaw 가져오기
float getYaw();
// Robot 회전 함수
void rotateToAngle(float targetAngle);
void rotate(float angle);

EspStatus sendCommandToEsp(String command, String expected, int timeout);
void connectWifi(String ssid, String pwd);
void connectServer(String ip, int port);
EspStatus sendCommandToServer(char* cmd, int length, uint8_t status=255, uint32_t data=4294967295);
int getDataFromServer(char* buffer);
uint32_t* getTagList();
Command getCmd(uint8_t* data);
int getOrder(uint8_t* data, uint8_t* order);
bool isTagDetected();
bool isMaskAll();

void setup()
{
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
  Serial.begin(115200);
  WifiSerial->begin(115200);
  Wire.begin();
  mpu.initialize();
  Serial.println("MPU6050 초기화 중...");

  SPI.begin();			// Init SPI bus
	mfrc522.PCD_Init();		// Init MFRC522
  
  // 자이로 센서 초기화 확인
  if (!mpu.testConnection())
  {
    Serial.println("MPU6050 연결 실패!");
    while (1);
  }
  Serial.println("MPU6050 연결 성공");

  // 초기 오프셋 측정 (센서를 고정한 상태에서 실행)
  Serial.println("자이로 센서 오프셋 보정 중... 3초간 가만히 두세요.");
  delay(2000);
  calibrateGyroZ();
  Serial.println("자이로 센서 오프셋 보정 완료!");

  lastTime = millis(); // 시간 초기화
  
  String ssid = "AIE_509_2.4G";
  String pwd = "addinedu_class1";
  String ip = "192.168.0.41";
  int port = 8888;
  
  delay(1000);
  /*
  // Wait connecting Wifi
  connectWifi(ssid, pwd);
  // Wait connecting Server
  connectServer(ip, port);

  sendCommandToServer("TL", 3, 0);

  tagList = getTagList();
  for (int j = 0; j < 4; j++) {
    Serial.print(tagList[j], HEX);
    Serial.println();
  }
  */
  
  // IR 센서 핀 모드
  pinMode(IR_L, INPUT);
  pinMode(IR_C, INPUT);
  pinMode(IR_R, INPUT);

  // 모터 드라이버 핀 모드
  pinMode(MOTOR_R_IN1, OUTPUT);
  pinMode(MOTOR_R_IN2, OUTPUT);
  
  pinMode(MOTOR_L_IN3, OUTPUT);
  pinMode(MOTOR_L_IN4, OUTPUT);

  // 초음파 센서 핀 모드
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // LED와 Fuzzer 핀 모드
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // LED 및 Fuzzer 초기화
  digitalWrite(BUZZER_PIN, LOW);

  updateYaw();
      rotate(180);
      moveForward();
      delay(100);
      stopMotors();
}

void loop()
{
  static RobotStatus currentRobotStatus = MOVING_TO_HP;
  static RobotStatus prevRobotStatus = HOME;
  static Command cmd = NOTTING;
  static int cntProduct = 0;
  static int cntOrder = 0;
  static uint8_t data[16];
  static uint8_t order[5];
  static bool* recvOrder;
  
  updateYaw();
  //lineTrace();
  //moveForward();
  /*
  if (Serial.available() > 0) {
    String str = Serial.readStringUntil('\n');
    WifiSerial->println(str);
  }

  if (WifiSerial->available() > 0) {
    Serial.println(WifiSerial->readStringUntil('\n'));
  }
  */
  
  if (getDataFromServer(data) > 0) {
    cmd = getCmd(data);
  } else {
    cmd = NOTTING;
  }
  
  if (cmd == GET_ORDER) {
    cntOrder = getOrder(data, order);
    recvOrder = new bool[cntOrder];
    memset(recvOrder, false, cntOrder);
    prevRobotStatus = currentRobotStatus;
    currentRobotStatus = MOVING_TO_SEC;
    if (cntOrder > 0) {
      Serial.print("Order List: ");
      for (int i = 0; i < cntOrder; i++) {
        Serial.print(order[i]);
        Serial.print(" ");
      }
      Serial.println();
    }
    Serial.println("GO!!");
  } else if (cmd == RESUME) {
    Serial.println("RESUME");
    if (++cntProduct == cntOrder) {
      sendCommandToServer("PC", 3, 0x02);
    } else {
      RobotStatus temp = prevRobotStatus;
      prevRobotStatus = currentRobotStatus;
      currentRobotStatus = temp;
    }
  } else if (cmd == MOVE_TO_PP) {
    prevRobotStatus = currentRobotStatus;
    currentRobotStatus = MOVING_TO_PP;
    cntMask = 0;
  } else if (cmd == MOVE_TO_HP) {
      updateYaw();
      rotate(180);
      moveForward();
      delay(100);
      stopMotors();
    
    prevRobotStatus = currentRobotStatus;
    currentRobotStatus = MOVING_TO_HP;
    
    cntMask = 0;
  }

  switch (currentRobotStatus) {
    case STOP:
      stopMotors();
      break;
    case WAIT:
      stopMotors();
      break;
    case GETTING_PRODUCT:
      stopMotors();
      break;
    case MOVING_TO_SEC:
      if (isTagDetected()) {
        if (!prevDetected) {
          prevDetected = true;
          
          stopMotors();
          for (int i = 0; i < cntOrder; i++) {
            if (recvOrder[i] == true) continue;
            uint8_t temp[4] = {0};
            temp[3] = (tagList[order[i]] >> 24) & 0xFF;
            temp[2] = (tagList[order[i]] >> 16) & 0xFF;
            temp[1] = (tagList[order[i]] >> 8) & 0xFF;
            temp[0] = tagList[order[i]] & 0xFF;
            bool isValid = true;
            for (int j = 0; j < 4; j++) {
              if (temp[j] != mfrc522.uid.uidByte[j]) {
                isValid = false;
                moveForward();
                return;
              }
            }
            if (isValid == true) {
              recvOrder[i] = true;
              Serial.println("Detected");
              Serial.print("Order Idx: ");
              Serial.println(order[i]);
              prevRobotStatus = currentRobotStatus;
              currentRobotStatus = GETTING_PRODUCT;
              while (sendCommandToServer("PC", 4, 0x00, order[i]) == STATUS_NO);
              break;
            }
          }
        }
      } else {
        prevDetected = false;
        lineTrace();
      }
      break;
    case MOVING_TO_PP:
      if (isMaskAll()) {
        Serial.print("cntMask: ");
        Serial.println(++cntMask);
        if (cntMask == 2) {
          stopMotors();
          sendCommandToServer("MV", 3, 0x01);
          cntMask = 0;
          currentRobotStatus = WAIT;
        }
      } else {
        lineTrace();
      }
      break;
    case MOVING_TO_HP:
      if (isMaskAll()) {
        Serial.print("cntMask: ");
        Serial.println(++cntMask);
        if (cntMask == 1) {
          stopMotors();
          rotate(-90);
          moveForward();
          delay(100);
          stopMotors();
        } else if (cntMask == 2) {
          stopMotors();
          rotate(90);
          moveForward();
          delay(100);
          stopMotors();
          sendCommandToServer("MV", 3, 0x03);
          cntMask = 0;
          delete [] recvOrder;
          prevRobotStatus = currentRobotStatus;
          currentRobotStatus = STOP;
        }
      } else {
        lineTrace();
      }
      break;
  }
  
  if (currentRobotStatus == HOME || currentRobotStatus == GETTING_PRODUCT) {
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
  } else if (
    currentRobotStatus == MOVING_TO_SEC ||
    currentRobotStatus == MOVING_TO_PP ||
    currentRobotStatus == MOVING_TO_HP
  ) {
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
  } else if (currentRobotStatus == WAIT) {
    digitalWrite(RED_LED, LOW);
    digitalWrite(YELLOW_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
  }
  
 
  /*
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    for (int i = 0; i < mfrc522.uid.size; i++) {
      Serial.print(mfrc522.uid.uidByte[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  }
  */
}


// === 속도 설정 함수 ===
void setMotorSpeed(int leftSpeed, int rightSpeed)
{
  // 왼쪽 모터
  if (leftSpeed > 0)
  {
    analogWrite(MOTOR_L_IN4, leftSpeed); // 전진
    analogWrite(MOTOR_L_IN3, 0);
  }
  else
  {
    analogWrite(MOTOR_L_IN4, 0);
    analogWrite(MOTOR_L_IN3, abs(leftSpeed)); // 후진
  }

  // 오른쪽 모터
  if (rightSpeed > 0)
  {
    analogWrite(MOTOR_R_IN1, rightSpeed); // 전진
    analogWrite(MOTOR_R_IN2, 0);
  }
  else
  {
    analogWrite(MOTOR_R_IN1, 0);
    analogWrite(MOTOR_R_IN2, abs(rightSpeed)); // 후진
  }
}

// === 모터 제어 함수 ===
void moveForward()
{
  setMotorSpeed(motorSpeed, motorSpeed);
}

void moveBackward()
{
  setMotorSpeed(-motorSpeed, -motorSpeed);  // 음수 전달하여 후진
}

void turnLeft()
{
  
  setMotorSpeed(-motorSpeed, motorSpeed);
}

void turnRight()
{
  setMotorSpeed(motorSpeed, -motorSpeed);
}

void gyroturnRight()
{
  analogWrite(MOTOR_L_IN4, motorSpeed); // 왼쪽 바퀴 앞으로
  analogWrite(MOTOR_R_IN2, motorSpeed); // 오른쪽 바퀴 뒤로
}

void gyroturnLeft()
{
  analogWrite(MOTOR_R_IN1, motorSpeed); // 오른쪽 바퀴 앞으로
  analogWrite(MOTOR_L_IN3, motorSpeed); // 왼쪽 바퀴 뒤로
}

void stopMotors()
{
  setMotorSpeed(0, 0); // 속도 0으로 설정하여 정지
}

void lineTrace() {
  int leftSensor = digitalRead(IR_L);
  int centerSensor = digitalRead(IR_C);
  int rightSensor = digitalRead(IR_R);
  if (isMaskAll()) {
    moveForward();
    delay(100);
  } else if (centerSensor && !rightSensor && !leftSensor) {
    moveForward();  // 중앙이 검은색이면 직진
  } else if (rightSensor && !leftSensor) {
    turnRight();
  } else if (leftSensor && !rightSensor) {
    turnLeft();
  } 
  
  
  
}

// === 초음파 센서 거리 측정 함수 ===
long getDistance()
{
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  long distance = duration * 0.034 / 2;
  return distance;
}

// === 장애물 감지 및 경고 ===
bool checkObstacle()
{
  static unsigned long previousMillis = 0;
  const long interval = 500; // 깜빡이는 주기 (500ms)
  static bool ledState = false; // LED 상태 저장

  long distance = getDistance();
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  if (distance > 0 && distance < OBSTACLE_DISTANCE)
  {
    stopMotors();

    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval)
    {
      previousMillis = currentMillis;

      ledState = !ledState; // LED 및 부저 상태 토글 (깜빡이기)
      digitalWrite(RED_LED, ledState);
      digitalWrite(BUZZER_PIN, ledState);
    }
    return true;
  } 
  else
  {
    digitalWrite(RED_LED, LOW);
    digitalWrite(BUZZER_PIN, LOW);
    return false;
  }
}

void updateYaw()
{
    static unsigned long long lastTime = millis(); // micros() 사용
    unsigned long long currentTime = millis();
    float deltaTime = (currentTime - lastTime) / 1000.0; // 초 단위 변환
    lastTime = currentTime;

    float yawRate = getYawRate();
    yaw -= yawRate * 0.013;
}

// === 자이로 Z축 오프셋 보정 함수 ===
void calibrateGyroZ()
{
  int numSamples = 500;
  long sum = 0;

  for (int i = 0; i < numSamples; i++)
  {
    int16_t gx, gy, gz;
    mpu.getRotation(&gx, &gy, &gz);
    sum += gz;
    delay(5);
  }
  
  gyroZ_offset = sum / (float)numSamples;
  Serial.print("보정된 GyroZ 오프셋: ");
  Serial.println(gyroZ_offset);
}

// Yaw 변화율 가져오기
float getYawRate()
{
  int16_t gx, gy, gz;
  mpu.getRotation(&gx, &gy, &gz);
  return (gz - gyroZ_offset) / 131.0;
}

// 현재 Yaw 가져오기
float getYaw()
{
  return yaw;
}

void rotateToAngle(float targetAngle)
{
  yaw = 0;
  float initialYaw = yaw; // 현재 yaw 값 저장
  unsigned long lastTime = millis();

  while (true)
  {
    updateYaw();

    if (abs(yaw - (initialYaw + targetAngle)) <= ERROR_MARGIN) // initialYaw 기준으로 목표 각도 계산
    { 
      stopMotors();
      Serial.println("회전 완료!");
      break;
    }

    if (yaw < (initialYaw + targetAngle))
    {
      gyroturnRight();
    }
    else
    {
      gyroturnLeft();
    }

    Serial.print("현재 Yaw: ");
    Serial.print(yaw);
    Serial.print(" | 목표 Yaw: ");
    Serial.println(initialYaw + targetAngle);

    delay(10);
  }
}

void rotate(float angle)
{
  targetYaw = angle; // 목표 각도 갱신
  rotateToAngle(targetYaw); // rotateToAngle 함수를 사용하여 목표 각도로 회전
}

void connectWifi(String ssid, String pwd) {
  while (1) {
      if (
        sendCommandToEsp("AT", "OK", 2000) == STATUS_YES &&
        sendCommandToEsp("AT+CWMODE=1", "OK", 2000) == STATUS_YES &&
        sendCommandToEsp("AT+CWJAP=\"" + ssid + "\",\"" + pwd + "\"", "OK", 10000) == STATUS_YES
      ) {
        Serial.println("Wifi connect success");
        return;
      } else {
        Serial.println("Wifi connect failed");
      }
  }
}

void connectServer(String ip, int port) {
  // Server와 연결이 가능한지 확인
  while (1) {
    if (sendCommandToEsp("AT+CIPSTART=\"TCP\",\"" + ip + "\"," + String(port), "OK", 5000) == STATUS_YES) {
      Serial.println("Server connect success");
      Serial.println();
      Serial.println("Checking communication available...");

      // 연결 성공 후 통신 가능한지 확인
      sendCommandToServer("AT", 3, 0);
    
      char recvBuffer[16];
      memset(recvBuffer, 0x00, 16);

      // Server로부터 AT2를 받았는지 확인
      while (1) {
        if (getDataFromServer(recvBuffer) > 0) {
          if (memcmp(recvBuffer, "AT", 2) == 0) {
            if (recvBuffer[2] == 2) {
              Serial.println("Can Start Communication With Server!!");
              return;
            }
          }
        }
      }
    } else {
      Serial.println("Server connect failed");
    }
  }
}

EspStatus sendCommandToEsp(String command, String expected, int timeout) {
  WifiSerial->println(command); // ESP01에게 명령어 전송
  long time = millis();
  while (millis() - time < timeout) { // time limit 설정
    String response = WifiSerial->readStringUntil('\n');
    if (response.indexOf(expected) != -1) { // ESP01로부터 수신된게 expected와 같은지 확인
      return STATUS_YES;
    }
  }
  return STATUS_NO;
}

EspStatus sendCommandToServer(char* cmd, int length, uint8_t status=255, uint32_t data=4294967295) {
  if (sendCommandToEsp("AT+CIPSTATUS", "STATUS:3", 2000) == STATUS_YES) {Serial.println("OK!!!");}
  else {connectServer("192.168.0.41", 8888);}
  if (sendCommandToEsp("AT+CIPSEND=" + String(length + 2), ">", 5000) == STATUS_YES) { // ESP01에게 CIPSEND 명령어 전송, ">" 가 회신되면 정상적으로 송신된 거임
    Serial.println("SEND");
    uint8_t sendBuffer[16];
    memset(sendBuffer, 0x00, sizeof(sendBuffer));
    memcpy(sendBuffer, cmd, 2);
    if (status != 255) { // status 값이 있으면 설정
      sendBuffer[2] = status;
    }
    if (data != 4294967295) { //data 값이 있으면 설정
      memset(sendBuffer + 3, data, 4);
    }
    WifiSerial->write(sendBuffer, length); // 서버에 보내기
    WifiSerial->println();
    return STATUS_YES;
  } else {
    return STATUS_NO;
  }
}

int getDataFromServer(char* buffer) {
  
  memset(buffer, 0x00, 32);
  if (WifiSerial->available() == 0) return 0;
  char recvBuffer[32];
  int length = 0;
  memset(recvBuffer, 0x00, 32);
  
  int recvSize = 0;
  // Server로 부터 깔끔하게 값이 수신되지 않아서 Parsing 진행
  
  char temp[32] = {0};
  recvSize = WifiSerial->readBytesUntil('\n', temp, 32); // '\n' 까지 데이터 읽고 size 전달
  if (recvSize && String(temp).indexOf("+IPD") != -1) { // 수신된 값에서 "+IPD"가 있으면
    length = recvSize - (String(temp).indexOf(':') + 1) + 1; // Server에서 정확히 송신한 값의 길이
    temp[recvSize++] = '\n';
    Serial.print(temp);
    memcpy(recvBuffer, temp + String(temp).indexOf(':') + 1, length); // 그 길이만큼 recvBuffer에 복사
  }
  
  memcpy(buffer, recvBuffer, length);
  return length;
}

uint32_t* getTagList() {
  int count = 0;
  uint32_t temp[10] = {0};

  char recvBuffer[32];
  int length = 0;
  
  while (1) {
    if (getDataFromServer(recvBuffer) ==0 ) continue;
    if (memcmp(recvBuffer, "TL", 2) == 0 && recvBuffer[2] == 0x01) {
      memcpy(&temp[count], recvBuffer + 3, 4);
      count++;
    } else if (memcmp(recvBuffer, "TL", 2) == 0 && recvBuffer[2] == 0x02) {
      sendCommandToServer("TL", 3, 3);
      break;
    }
  }
  Serial.println(count);
  
  uint32_t* tagList = new uint32_t[count];
  memcpy(tagList, temp, count*4);
  return tagList;
}

Command getCmd(uint8_t* data) {
  if (memcmp(data, "OD", 2) == 0) {
    return GET_ORDER;
  }
  if (memcmp(data, "PC", 2) == 0 && data[2] == 0x01) {
    return RESUME;
  }
  if (memcmp(data, "MV", 2) == 0) {
    if (data[2] == 0x00) return MOVE_TO_PP;
    if (data[2] == 0x02) return MOVE_TO_HP;
  }
}

int getOrder(uint8_t* data, uint8_t* order) {
  int size = 0;
  uint8_t temp[5] = {0};
  while (1) {
    if (memcmp(data, "OD", 2) == 0 && data[2] == 0x01) break;

    if (memcmp(data, "OD", 2) == 0 && data[2] == 0x00) {
      temp[size++] = data[3];
    }
    getDataFromServer(data);
    delay(500);
  }
  memcpy(order, temp, size);
  return size;
}

bool isTagDetected() {
  return mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial();
}

bool isMaskAll() {
  static bool prevMask = false;
  bool mask = ((digitalRead(IR_L) && digitalRead(IR_R) && digitalRead(IR_C)));
  if (!prevMask && mask) {
    prevMask = true;
    return true;
  } else if (!mask && prevMask) {
    prevMask = false;
  }
  return false;
}


// Test code
/*
  // === 좌측 우측 보정 테스트 ===
  unsigned long currentTime = millis();
  float deltaTime = (currentTime - lastTime) / 1000.0;  
  lastTime = currentTime;

  yaw += getYawRate() * deltaTime;

  float error = yaw - targetYaw; // 현재 방향과 목표 방향의 차이
  float correction = error * 5; // P제어 적용 (보정 값)

  int rightSpeed = motorSpeed - correction;
  int leftSpeed = motorSpeed + correction;

  rightSpeed = constrain(rightSpeed, 100, 255);  
  leftSpeed = constrain(leftSpeed, 100, 255);

  analogWrite(MOTOR_R_IN1, rightSpeed);
  analogWrite(MOTOR_L_IN4, leftSpeed);

  Serial.print("Yaw: ");
  Serial.print(yaw);
  Serial.print(" | 목표 Yaw: ");
  Serial.print(targetYaw);
  Serial.print(" | 보정: ");
  Serial.println(correction);
  
  delay(50);
  */

  // rotate(-90); // 90도 회전
  
  /* // === 자이로 센서 작동 테스트 ===
  unsigned long currentTime = millis();
  float deltaTime = (currentTime - lastTime) / 1000.0; // 초 단위 시간 변화량
  lastTime = currentTime;

  int16_t gyroX, gyroY, gyroZ;
  mpu.getRotation(&gyroX, &gyroY, &gyroZ);

  // 오프셋을 뺀 Yaw 값 계산 (deg/s → degree)
  float gyroZ_corrected = (gyroZ - gyroZ_offset) / 131.0; 
  yaw += gyroZ_corrected * deltaTime;  

  // 시리얼 모니터 출력
  Serial.print("Yaw 각도 : ");
  Serial.print(yaw);
  Serial.print("도 GyroZ 보정됨 : ");
  Serial.println(gyroZ_corrected);

  delay(50);  // 50ms마다 데이터 출력 (빠른 샘플링 방지)
  */
  /*
  // 데이터 출력
  Serial.print("Accel (X, Y, Z): ");
  Serial.print(ax); Serial.print(", ");
  Serial.print(ay); Serial.print(", ");
  Serial.println(az);

  Serial.print("Gyro (X, Y, Z): ");
  Serial.print(gx); Serial.print(", ");
  Serial.print(gy); Serial.print(", ");
  Serial.println(gz);
  */

  /*
  Serial.print("L:");
  Serial.print(leftSensor);
  Serial.print(" C:");
  Serial.print(centerSensor);
  Serial.print(" R:");
  Serial.println(rightSensor);

  
  // 장애물 감지
  if (checkObstacle())
  {
    return;
  }
  
  // 라인 감지 (검은색 라인은 LOW (0))
  if (centerSensor == 0) 
  {  
    moveForward();  // 중앙이 검은색이면 직진
  } 
  else if (leftSensor == 0)
  {  
    turnLeft();  // 왼쪽이 검은색이면 좌회전
  }
  else if (rightSensor == 0)
  {  
    turnRight();  // 오른쪽이 검은색이면 우회전
  }

  if (leftSensor == 0 && centerSensor == 0 && rightSensor == 0)
  {
    stopMotors(); // 모터 정지 후 RFID 체크하기
    return;
  }

  if (leftSensor == 1 && centerSensor == 0 && rightSensor == 0)
  {
    turnRight();
    return;
  }

  if (leftSensor == 0 && centerSensor == 0 && rightSensor == 1)
  {
    turnLeft();
    return;
  }
  
  delay(10); */

