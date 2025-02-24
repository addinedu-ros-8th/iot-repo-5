# iot-repo-5
IOT 프로젝트 5조 저장소. 팀 통신보안
<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/addinedu-ros-8th/iot-repo-5">
    <img src="https://github.com/addinedu-ros-8th/iot-repo-5/blob/main/frontImg.webp" alt="Logo" width="500px">
  </a>

  <h3 align="center">무인매장 자동화 시스템(Unmanned Store Automation System)</h3>

  <p align="center">
    <a href="https://youtube.com/">Video Demos</a>
  </p>
</p>

<hr>



<!-- ABOUT THE PROJECT -->
## Preview
IoT 기술을 활용하여 주문만 하면 로봇이 알아서 물건을 가져다 주는 스마트 마트 시스템 개발
- **무인 마트 자동화 트렌드 반영** : 인건비 절감 및 효율적인 운영
- **소비자 편의성 극대화** :  주문 대기시간 단축, 상품 찾기의 불편함 해소.
- **실내 물류 시스템 확장** : 대규모(e.g. 물류센터 및 창고) -> 소규모(e.g. 마트) 


mp4 - video

<br>

|        | name | job |
|--------|------|-----|
| leader | 이태민 |  로봇 SW|   
| worker | 강주빈 |  로봇 SW, 기구 및 트랙 설계 |   
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


## Design

### Scenario
![Image](https://github.com/user-attachments/assets/e1c22b09-117d-44b7-bf4d-6ef9c9801795)
### Structure 

### Architecture  
#### 1) SW
![Image](https://github.com/user-attachments/assets/a2228d6d-e6c4-48aa-936c-80c851946586)

#### 2) HW
![Image](https://github.com/user-attachments/assets/6f38a9c4-d1d4-4ffb-ac80-f4be5c4e6796)

### DB 
![Image](https://github.com/user-attachments/assets/db91dcca-73be-405f-91e4-150dc0bc62d5)

### Fuction 
#### Function list 
|  기능  | 설명 |
|--------|------| 
| Auth  | ID,PW 인증관리 |    
| Stock | 재고확인, 재고업데이트 |     
| Order | 제품검색, 제품수량선택, 재고없는 제품은 주문 불가능 |      
| Move | 로봇이 Home station에서 각 상품 위치로 이동, Pickup station으로 이동 |     
| Detect| 로봇의 장애물 감지시 경고 알림(LED, Buzzer), RFID Tag를 통한 상품 위치 인식|
| Load | 진열대에서 물품 개수만큼 카트에 투하, 올바른 적재 확인 |
| Control | 관리자는 로봇을 자동/수동 제어 | 

#### Client 주문 
#### Admin  로봇 수동제어, 재고수정및 관리  
#### Controller 적재, 이동, 전달    
  #####  진열대 
  #####  로봇 


## Test Case
## Project Schedule
Project Period: 2025.02.19~2025.02.26
