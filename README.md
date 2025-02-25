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
#### 1) Simple Diagram
![Image](https://github.com/user-attachments/assets/e1c22b09-117d-44b7-bf4d-6ef9c9801795)
#### 2) State Diagram 
#### 3) Sequencial Diagram

### Architecture  
#### 1) SW
![Image](https://github.com/user-attachments/assets/b98fc788-4aed-4bea-b0fc-99615b5b7f76)
#### 2) HW
![Image](https://github.com/user-attachments/assets/5ea9f2f4-b5dd-4a12-a072-1b8e093264f8)

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

#### Client 
![Image](https://github.com/user-attachments/assets/5c8b4340-f920-48ad-b42c-772034872c96)

|  기능  | 설명 | 결과 |
|--------|------|------| 
| 인증 | 사용자 인증을 통해 출입이 가능한가? | Pass |
| 재고오류 | 재고가 주문한 수량보다 적을시, 주문이 실패하는가? | fail |  
| 제품검색 | 제품명, 금액, 유형을 통해 제품을 찾을 수 있는가? | Pass |
|| 매장의 물품 재고를 확인할 수 있는가? | pass |
| 장바구니 | 장바구니를 통해 물품을 담거나 주문한 내역을 확인이 가능한가 ?| Pass | 


#### Admin  로봇 수동제어, 재고수정및 관리  
![Image](https://github.com/user-attachments/assets/6fc59766-d309-4134-a80d-dd29f08eb7dc)

|  기능  | 설명 | 결과 |
|--------|------|------| 
| 재고관리 | 관리자는 재고를 확인 할 수 있는가? | Pass |
|| 관리자가 재고를 업데이트시, 반영이 되는가? | Fail |
| 수동제어 | 로봇의 정지, 전진, 좌회전, 우회전이 가능한가? | Fail |
|| 각 staation(pickup, home) 이동이 가능한가? | Fail |
|| 특정 물품으로 이동이 가능한가? | Fail |

#### Controller    
#####  진열대

|  기능  | 설명 | 결과 |
|------|------|------| 
| 통신 | Server와 통신이 원할한가? | Pass |  
| 물품적재 | Client가 주문한 수량과 물품이 정확하게 카트에 적재되는가? | Pass |  

#####  로봇 
|  기능  | 설명 | 결과 |
|--------|------|------| 
| 로봇이동 | 장애물 감지시, 알람을 울리는가? | fail |    
|| 요청한 상품 section ID로 정확하게 이동하는가?  | fail | 
|| pickup station과 home station 이동이 원활한가? | fail |
|| client가 주문한 물품을 찾아갈 떄까지 pickup station에서 대기 하는가? | fail |
| 장애물감지 | 경로 상에 장애물을 감지하는가? | fail |
|| 장애물 감지시 시각적 청각적으로 알람을 울리는가? | fail |
| 태그인식 | RFID를 정확하게 인식하는가? | fail | 
|| 읽어온 태그 정보를 바탕으로 주문한 물품인지 판단이 가능한가? | fail |

 
## Project Schedule
Project Period: 2025.02.19~2025.02.26
