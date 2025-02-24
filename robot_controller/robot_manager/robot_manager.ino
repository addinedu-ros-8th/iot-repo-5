#include <Wire.h>
#include <MPU6050.h>

// === 핀 설정 ===
// IR 센서 핀 설정
const int IR_L = 2;  // 왼쪽 IR 센서
const int IR_C = 3;  // 가운데 IR 센서
const int IR_R = 4;  // 오른쪽 IR 센서

// 모터 드라이버 핀 설정 (L9110S 기준)
const int MOTOR_R_IN1 = 5;   // 오른쪽 모터 방향 1 HIGH 시 전진
const int MOTOR_R_IN2 = 6;   // 오른쪽 모터 방향 2 HIGH 시 후진

const int MOTOR_L_IN3 = 10;  // 왼쪽 모터 방향 1 HIGH 시 후진
const int MOTOR_L_IN4 = 11;  // 왼쪽 모터 방향 2 HIGH 시 전진

// 초음파 센서 핀
const int TRIG_PIN = 8;
const int ECHO_PIN = 12;

// 장애물 감지 거리 (단위: cm)
const int OBSTACLE_DISTANCE = 10;

// LED와 Fuzzer 핀
const int GREEN_LED = 9;  // 주행 중 초록 LED
const int RED_LED = 7;    // 장애물 감지 시 빨간 LED
const int BUZZER_PIN = A0; // Fuzzer

const int MPU_UPDATE_INTERVAL = 10; // 센서 데이터 10ms 주기로 갱신
const int ERROR_MARGIN = 20; // 20도 이내 오차 허용

MPU6050 mpu;

float targetYaw = 0;  // 목표 방향 (처음 시작 방향)
float gyroZ_offset = 0; // 자이로 Z축 오프셋 (드리프트 보정)
float yaw = 0;

float previousError = 0;
float integral = 0;
unsigned long lastTime = 0;

// 초기 모터 속도 (0~255)
int motorSpeed = 150;

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

void setup()
{
  Serial.begin(115200);
  Wire.begin();
  mpu.initialize();
  Serial.println("MPU6050 초기화 중...");

  // 자이로 센서 초기화 확인
  if (!mpu.testConnection())
  {
    Serial.println("MPU6050 연결 실패!");
    while (1);
  }
  Serial.println("MPU6050 연결 성공");

  // 초기 오프셋 측정 (센서를 고정한 상태에서 실행)
  Serial.println("자이로 센서 오프셋 보정 중... 3초간 가만히 두세요.");
  delay(3000);
  calibrateGyroZ();
  Serial.println("자이로 센서 오프셋 보정 완료!");

  lastTime = millis(); // 시간 초기화

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
  pinMode(BUZZER_PIN, OUTPUT);

  // LED 및 Fuzzer 초기화
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER_PIN, LOW);
}

void loop()
{

  
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
  digitalWrite(GREEN_LED, HIGH);
}

void moveBackward()
{
  setMotorSpeed(-motorSpeed, -motorSpeed);  // 음수 전달하여 후진
  digitalWrite(GREEN_LED, HIGH);
}

void turnLeft()
{
  
  // setMotorSpeed(0, motorSpeed);
  digitalWrite(GREEN_LED, HIGH);
}

void turnRight()
{
  setMotorSpeed(motorSpeed, 0);
  digitalWrite(GREEN_LED, HIGH);
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
  digitalWrite(GREEN_LED, LOW);
}

void lineTrace() {
  int leftSensor = digitalRead(IR_L);
  int centerSensor = digitalRead(IR_C);
  int rightSensor = digitalRead(IR_R);

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
  static unsigned long lastTime = millis();
  unsigned long currentTime = millis();
  float deltaTime = (currentTime - lastTime) / 1000.0;  // 초 단위 시간 변화량
  lastTime = currentTime;

  float yawRate = getYawRate();  // 자이로 센서에서 Z축 회전 속도 가져오기
  yaw -= yawRate * deltaTime;    // Yaw 값 적분하여 업데이트
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
    Serial.println(targetAngle);

    delay(10);
  }
}

void rotate(float angle)
{
  targetYaw += angle; // 목표 각도 갱신
  rotateToAngle(targetYaw); // rotateToAngle 함수를 사용하여 목표 각도로 회전
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

