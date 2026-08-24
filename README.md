여러 학교를 방문해야 하는 상황에서 효율적인 방문 순서를 계산하기 위해 만든 경로 최적화 프로그램입니다.

Excel에 저장된 학교 목록과 주소를 불러온 뒤 Kakao Local API를 이용하여 각 학교의 좌표를 조회하고, Greedy(Nearest Neighbor) + 2-opt 알고리즘​을 이용하여 이동 거리가 짧은 방문 순서를 계산합니다.

주요 기능
Excel 파일에서 지역별 학교 목록 및 주소 조회
Kakao Local API를 이용한 주소 → 위도/경도 변환
주소 검색 실패 시 학교명 기반 키워드 검색
Nearest Neighbor 방식으로 초기 방문 경로 생성
2-opt 알고리즘을 이용한 경로 개선
지역별 출발지 설정
주소 검색 실패 항목 별도 저장
최종 방문 순서를 Excel / TXT 파일로 저장
경로 계산 방식
1. 좌표 변환

Excel에 저장된 학교 주소를 Kakao Local API로 검색하여 위도와 경도를 가져옵니다.

주소 검색에 실패한 경우 학교명을 이용한 키워드 검색을 추가로 수행합니다.

2. 초기 경로 생성

현재 위치에서 가장 가까운 학교를 다음 방문지로 선택하는 Nearest Neighbor 방식을 사용합니다.

출발지
  ↓
가장 가까운 학교
  ↓
남은 학교 중 가장 가까운 학교
  ↓
...
3. 2-opt 경로 개선

Nearest Neighbor로 생성한 초기 경로에서 두 구간의 방문 순서를 반복적으로 변경하며 전체 이동 거리가 감소하는 경우 경로를 갱신합니다.

Nearest Neighbor 경로
        ↓
     2-opt
        ↓
개선된 방문 순서
기술 스택
Python
Pandas
Requests
Geopy
Kakao Local REST API
python-dotenv
Excel (openpyxl)
프로젝트 구조
project/
├── main.py
├── .env
├── .gitignore
├── requirements.txt
└── output/
    ├── 전체_방문순서.xlsx
    ├── 전체_방문순서.txt
    ├── 지역별_방문순서.xlsx
    └── 지역별_주소좌표목록.xlsx

.env 파일은 API Key를 포함하므로 GitHub에 업로드하지 않습니다.

환경 설정
1. 저장소 Clone
git clone https://github.com/lllOwOlll/map_search.git
cd map_search
2. 패키지 설치
pip install -r requirements.txt
3. Kakao REST API Key 설정

프로젝트 루트에 .env 파일을 생성합니다.

KAKAO_REST_API_KEY=YOUR_KAKAO_REST_API_KEY
4. 실행
python main.py
입력 데이터

Excel 파일에서 다음 정보를 읽어옵니다.

항목	설명
학교명	방문할 학교 이름
학교주소	학교 주소
무인함 위치	학교 내부 설치 위치
구 / 자치구	학교가 위치한 지역

지역별 Sheet를 읽어 각각 방문 순서를 계산합니다.

출력 결과

프로그램 실행 후 output 폴더에 결과가 저장됩니다.

[강북구]
0. TGS강북센터
1. 학교 A
2. 학교 B
3. 학교 C
...

각 지역별로 다음 파일을 생성합니다.

주소 및 좌표 조회 결과
지역별 방문 순서
전체 지역 방문 순서 Excel
전체 지역 방문 순서 TXT
주소 검색 실패 목록
알고리즘

이 프로젝트는 정확한 도로 주행시간 기반 TSP 최적화가 아닌, 학교의 위도·경도 간 직선거리를 기준으로 방문 순서를 휴리스틱하게 최적화합니다.

초기 경로는 Nearest Neighbor 방식으로 생성하고, 이후 2-opt 알고리즘을 적용하여 초기 경로보다 이동 거리가 짧아지도록 개선합니다.

따라서 실제 차량 이동 경로와 결과에는 차이가 발생할 수 있습니다.

개선 계획
Kakao Mobility Directions API 등을 활용한 실제 도로 이동거리 기반 계산
지도 위 방문 경로 시각화
출발지/도착지 설정 기능 개선
FastAPI를 이용한 경로 계산 API 구현
웹에서 Excel 업로드 및 결과 확인 기능 구현
