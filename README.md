# iot-repo-5
IOT 프로젝트 5조 저장소. 팀 통신보안
<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/addinedu-ros-8th/iot-repo-5">
    <img src="https://github.com/addinedu-ros-8th/eda-repo-3/blob/main/flowermen.jpg" alt="Logo" width="500px">
  </a>

  <h3 align="center">무인매장 자동화 시스템(Unmanned Store Automation System)</h3>

  <p align="center">
    <a href="https://youtube.com/">Video Demos</a>
  </p>
</p>

<hr>



<!-- ABOUT THE PROJECT -->
## Preview
이 프로젝트는 무인 마트 자동화 시스템을 구축하는 것으로, 로봇과 IoT 기술을 활용하여 상품을 자동으로 배송하는 시스템을 구현합니다. **서버(PC)**는 전체 시스템의 핵심으로, **데이터베이스(DB)**와 연결되어 주문 정보를 관리하며, **클라이언트(PC)**와 통신하여 사용자가 주문을 요청할 수 있도록 합니다. **아두이노(Arduino UNO)**는 로봇의 컨트롤러 역할을 하며, IR 센서, 초음파 센서, RFID 리더, 모터 드라이버, 와이파이 모듈, IMU 센서 등을 통해 로봇이 상품을 인식하고, 장애물을 피하며 목적지까지 이동할 수 있도록 돕습니다. 또한, ESP8266 모듈을 활용하여 상품 보관 시스템을 관리하며, RFID 태그와 서보 모터를 통해 자동으로 상품을 꺼내어 배송할 수 있도록 설계되었습니다. 서버와 로봇, 그리고 재고 관리 시스템은 TCP/IP 통신을 기반으로 실시간으로 데이터를 주고받으며, 이를 통해 사용자는 주문을 요청하면 로봇이 상품을 가져다주는 완전 자동화된 쇼핑 경험을 할 수 있습니다.



https://user-images.githubusercontent.com/44033302/177024517-57cbd3e1-1326-4765-aeb8-fbca25eab88e.mp4

<br>

|        | name | job |
|--------|------|-----|
| leader | 이태민 |  Line Following, 관리자간/진열대간 통신|   
| worker | 강주빈 |  기구 설계, pickUp/Home position 분기|   
| worker | 신동철 |  사용자/관리자 GUI, DB 구축, 로봇 및 진열대 설계|    
| worker | 황한문 |  진열대-로봇 통신, github 관리, 서포트|    

## Insructions
### Environment   
- Dev: Arduino - C/C++, PyQt/Qt 5 Designer - python,  
- DB: AWS RDS - MySQL
- Collab: Jira, Confluence and Slack   

### Installation 
#### Linux/Ios/Window 
```bash 
    git clone ~ 
    code iot-repo-5  
```

#### python env 
```bash 
    mkdir <venv> 
    cd <venv>
    python -m venv <env>
    source ~/<venv>/<env>/bin/activate
```
#### PyQt5
- Linux 
```bash 
    pip install pyqt5
    sudo apt-get install pyqt5-dev-tools
```
- macOS (Homebrew)
```bash 
    source <env>/bin/activate
    pip install pyqt5
```
#### Qt Designer 
- Linux  
```bash 
    sudo apt install qttools5-dev-tools
    sudo apt install qttools5-dev
```
- macOS (Homebrew)
```bash 
    brew install qt@5
    export PATH="/opt/homebrew/opt/qt@5/bin:$PATH"
```

## User Requirement 
1. 사용자는 스마트폰 앱을 실행하고, 회원가입 또는 로그인을 할 수 있다.
2. 사용자는 상품 목록에서 원하는 상품을 선택하여 장바구니에 담을 수 있다.
- 상품이 품절되었을 경우, 장바구니에 추가할 수 없다.
3. 사용자는 장바구니에서 수량을 확인하고 결제할 수 있다.
- 결제 수단은 ○○○을 지원한다.
- 결제가 완료되면 주문이 확정된다.
4. 주문이 확정되면 로봇이 대기 장소에서 출발하여 지정된 픽업 위치로 이동한다.
- 로봇이 이동할 수 없는 경우(예: 장애물 감지) 관리자에게 알림이 전송된다.
5. 사용자가 상품을 수령하면 로봇은 원래 위치로 돌아간다.

## Design 

## Supplies 

## System Requirement 
![alt text](image.png) 
## System Architecture
### HW/SW structure  
### DB   


 

## Project Schedule
Project Period: 2025.02.19~2025.02.26
