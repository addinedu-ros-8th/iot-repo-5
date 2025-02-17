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
이 프로젝트는 무인 마트 자동화 시스템을 구축하는 것으로, 로봇과 IoT 기술을 활용하여 상품을 자동으로 배송하는 시스템을 구현합니다. 서버(PC)는 전체 시스템의 핵심으로, DB와 연결되어 주문 정보를 관리하며, 클라이언트(PC)와 통신하여 사용자가 주문을 요청할 수 있도록 합니다. Arduino UNO는 로봇의 컨트롤러 역할을 하며, IR 센서, 초음파 센서, RFID 리더, 모터 드라이버, 와이파이 모듈, IMU 센서 등을 통해 로봇이 상품을 인식하고, 장애물을 피하며 목적지까지 이동할 수 있도록 돕습니다.또한, ESP8266 모듈을 활용하여 상품 보관 시스템을 관리하며, RFID 태그와 서보 모터를 통해 자동으로 상품을 꺼내어 배송할 수 있도록 설계되었습니다 서버와 로봇, 그리고 재고 관리 시스템은 TCP/IP 통신을 기반으로 실시간으로 데이터를 주고받으며, 이를 통해 사용자는 주문을 요청하면 로봇이 상품을 가져다주는 완전 자동화된 쇼핑 경험을 할 수 있습니다.



mp4 - video

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

## Funtion list 
| ID     | Function  | Description  | 비고  |
|--------|-----------|---------------|------|
| SR_01  | 로봇 이동 | 어디에서 어디로 이동     |   |
|        |           | 주문한 모든 물품을 수령 후 픽업 장소로 이동 |   |
|        |           | 주문자가 픽업 장소에 대기중인 로봇에게서 물품을 수령시 로봇은 대기 위치로 이동 |   |
|        |           | 주문자가 물품 수령 태그를 하면 홈 포지션으로 이동 |   |
|        |           | 물품 수령과 이동 분류    |   |
|        |           | 이동 항목을 정해라      |   |
| SR_02  | 장애물 감지 | 로봇이 이동중인 경로에 장애물(벽)이 발견될 경우 다음 동작을 수행 |   |
|        |           | 현 위치에서 대기        |   |
|        |           | 장애물 감지 알람        |   |
|        |           | 주문자 또는 관리자에게 경고 알림  |   |
|        |           | Buzzer, LED         |   |
| SR_03  | 물품 구분   | RFID 리더기는 로봇, 태그는 각 상품 진열대에 부착 |   |
|        |           | 각 상품은 Unique ID를 부여 |   |
|        |           | 로봇이 각 물품 진열대 앞으로 이동하여 진열대에 부착된 태그를 인식 |   |
|        |           | 읽어온 태그 정보를 바탕으로 주문한 물품인지 판단 |   |
|        |           | 주문한 상품일 경우 진열대에서 주문한 물품 개수만큼 로봇카트에 투하 |   |
| SR_04  | 물품 수령   | 진열대가 투하해준 물품을 센서를 통해 정상적으로 카트에 투하됐는지 체크 |   |
|        |           | 물품 수령 확인         |   |
|        |           | 로봇카트 에 물품이 정상적으로 수령되었는지 확인 |   |
| SR_05  | 물품 전달   | 주문자가 물건을 찾아갈 때까지 픽업장소에서 대기 |   |
|        |           | 물품 전달 후 태그를 통해 전달 완료 |   |
|        |           | 주문자 인증           |   |
|        |           | 주문자는 매장에 들어오기 전 사용자 인증을 통해 출입할 수 있음 |   |
|        |           | 유저 이름은 통일       |   |
| SR_06  | 통신      | 로봇, 진열대, 관리자간 통신은 WiFi 모듈을 사용 |   |
| SR_07  | 관리자    | 주문 탭에서는 현재 보유중인 물품명, 재고수량을 확인할 수 있고 더블클릭 시 해당 물품의 수량을 입력해 주문 |   |
|        |           | 로그 탭에서는 물품 주문자/물품명/수량/시간, 로봇의 주문 수령 물품명/수량/시간, 로봇의 홈 포지션 이동 시간, 주문자의 물품 수령 시간을 확인 |   |
|        |           | 로그인, 제고 모니터링, 주문확인, 로봇제어(수동모드) |   |
|        |           | 관리자 인증           |   |
|        |           | 아이디, 패스워드로 관리자를 인증한다  |   |
|        |           | 재고관리             |   |
|        |           | 관리자는 재고를 확인할 수 있음 |   |
|        |           | 물품                |   |
|        |           | 수량                |   |
|        |           | 업데이트 날짜        |   |
|        |           | 관리자는 물품 정보를 업데이트할 수 있음 |   |
|        |           | 수량                |   |
|        |           | 물품                |   |
|        |           | 분리할지 분리를 안할지 고려 (수령, 입고) |   |
|        |           | 로봇 제어            |   |
|        |           | 관리자는 수동으로 제어 할 수 있음 |   |
|        |           | 정지, 전진, 좌회전, 우회전  |   |
|        |           | 특정 물품으로 이동    |   |
|        |           | 홈 포지션 이동       |   |
|        |           | 픽업장소 이동        |   |
| SR_08  | 주문자 인증 | 주문자는 아이디, 패스워드로 인증을 거친다 |   |
|        |           | 주문자는 로그인/인증을 해야만 주문가능 |   |
|        |           | 여러 물품을 장바구니에 담고 한번에 주문 가능 |   |
|        |           | 홈 화면에서 현재 매장의 물품 재고를 확인할 수 있음 |   |
|        |           | 과거 주문내역을 확인할 수 있음 |   |
|        |           | 주문자 주문         |   |
|        |           | 재고가 없는 제품은 주문할 수 없음 |   |
|        |           | 제품 수량을 선택할 수 있음 |   |
|        |           | 제품 검색          |   |
|        |           | 제품명             |   |
|        |           | 제품 금액           |   |
|        |           | 제품 유형           |   |
|        |           | 물품 요청 x        |   |


## Design

## Supplies 

## System Requirement 

## System Architecture
### HW/SW structure  
### DB   

## Project Schedule
Project Period: 2025.02.19~2025.02.26
