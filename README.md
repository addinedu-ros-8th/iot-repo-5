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
    <a href="https://youtu.be/7Mb05Vj0SKM">Video Demo</a>\\
    <a href="https://docs.google.com/presentation/d/1n8OKg7oh0bRsqkLMaaVnA1ZmXNhJMc0XTnG6pmG48TI/edit#slide=id.g33a6f54bd96_5_1141">Presentation</a>
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
| leader | 이태민 |  로봇 SW (통신, 주행)|   
| worker | 강주빈 |  로봇 SW (액추에이터, 센서), 기구 및 트랙 설계 |   
| worker | 신동철 |  사용자/관리자 GUI, DB 구축, 로봇 및 진열대 설계|    
| worker | 황한문 |  진열대-서버 통신, github 관리, 서포트|    

## Instructions
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


## 설계
### 시나리오
#### 1) Simple Diagram
![Image](https://github.com/user-attachments/assets/16a47ce1-faac-43d8-9173-9a00472122a5)
#### 2) State Diagram 
![Image](https://github.com/user-attachments/assets/08dd3445-5a55-44e2-a649-a6bde1d3b854)
#### 3) Sequencial Diagram
#### 3-1) 로봇 컨트롤 서버와 로봇, 진열대 연결
![Image](https://github.com/user-attachments/assets/703e6585-a9ae-41af-836e-557fa765292b)
#### 3-2) 주문
- 주문 성공
<br />

![Image](https://github.com/user-attachments/assets/c256f96b-be14-4c8f-a79d-3c5e688e27b1)

- 주문 실패
<br />

![Image](https://github.com/user-attachments/assets/8a7f0017-a248-45a8-a75e-a6beacbc1951)
#### 3-3) 상품 수령
![Image](https://github.com/user-attachments/assets/856504b6-d61d-43d5-8dc4-7052969bbe57)

### Architecture  
#### 1) SW
![Image](https://github.com/user-attachments/assets/155bbad3-be80-4613-a1be-860b536d4a0a)
#### 2) HW
![Image](https://github.com/user-attachments/assets/48a34ad7-a2c9-4912-a794-00ece34caac0)
#### 3) ERD 
![Image](https://github.com/user-attachments/assets/2496272e-e078-4145-b846-1a1755a04ef5)

## 기능 
### 기능 리스트 
|  기능  | 설명 |
|:--------:|------| 
| Auth  | ID,PW 인증관리 |    
| Stock | 재고확인, 재고업데이트 |     
| Order | 제품검색, 제품수량선택, 재고없는 제품은 주문 불가능 |      
| Move | 로봇이 홈 스테이션에서 각 상품 위치로 이동, 픽업 스테이션으로 이동 |     
| Detect| 로봇의 장애물 감지시 경고 알림(LED, Buzzer), RFID Tag를 통한 상품 위치 인식|
| Load | 진열대에서 물품 개수만큼 카트에 투하, 올바른 적재 확인 |
| Control | 관리자는 로봇을 자동/수동 제어 | 

### 주문자 
![Image](https://github.com/user-attachments/assets/5c8b4340-f920-48ad-b42c-772034872c96)

|  기능  | 설명 | 결과 |
|:--------:|------|:------:| 
| 인증 | 사용자 인증이 가능한가? | Pass |
| 상품검색 | 상품명, 금액, 유형을 통해 제품을 찾을 수 있는가? | Fail |
|| 매장의 상품 재고를 확인할 수 있는가? | Pass |
| 장바구니 | 장바구니를 통해 상품을 담거나 주문한 내역을 확인이 가능한가 ?| Pass | 
| 주문 | 재고가 있을떄 주문이 가능한가 | Pass |
|| 수량을 정할수 있는가? | Pass |
|| 장바구니에 담긴걸 일괄로 주문이 가능한가? | Pass |
| 재고오류 | 재고가 주문한 수량보다 적을시, 주문이 실패하는가? | Pass |  


### 관리자
![Image](https://github.com/user-attachments/assets/6fc59766-d309-4134-a80d-dd29f08eb7dc)

|  기능  | 설명 | 결과 |
|:--------:|------|:------:| 
| 재고관리 | 관리자는 재고를 확인 할 수 있는가? | Pass |
|| 관리자가 재고를 업데이트시, 반영이 되는가? | Pass |
| 수동제어 | 로봇의 정지, 전진, 좌회전, 우회전이 가능한가? | Fail |
|| 각 스테이션(픽업, 홈) 이동이 가능한가? | Pass |
|| 특정 상품위치로 이동이 가능한가? | Pass |

### 제어기    
####  진열대
![Image](https://github.com/user-attachments/assets/69f04f5b-e3d6-4b89-aa45-9b9d738fd866)
<br >
|  기능  | 설명 | 결과 |
|:------:|------|:------:| 
| 통신 | 서버와 통신이 원할한가? | Pass |  
| 상품적재 | 주문자가 주문한 수량과 상품이 정확하게 카트에 적재되는가? | Pass |  

####  로봇 
![Image](https://github.com/user-attachments/assets/7121af5a-6aab-47bc-a883-a3509a3b573c)
<br >
|  기능  | 설명 | 결과 |
|:--------:|------|:------:| 
| 로봇이동 | 요청한 상품 ID로 정확하게 이동하는가?  | Pass |    
|| 픽업 스테이션과 홈 스테이션 이동이 원활한가? | Pass |
|| 주문자가 주문한 상품을 찾아갈 때 까지 픽업 스테이션에서 대기 하는가? | Pass |
| 장애물감지 | 경로 상에 장애물을 감지하는가? | Fail |
|| 장애물 감지시 시각적 청각적으로 알람을 울리는가? | Fail |
| 물품구분 | 주문한 상품을 정확히 구분하는가? | Pass | 
|| 읽어온 태그 정보를 바탕으로 주문한 상품인지 판단이 가능한가? | Pass |
|상품적재확인 | 로봇카트에 상품이 정상적으로 적재되었는지 확인이 가능한가? | Fail |
 
## Project Schesule
Project Period: 2025.02.19~2025.02.26
<br >
![Image](https://github.com/user-attachments/assets/c255a370-4493-4f03-9428-93109bf50585)
