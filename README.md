# 🎮 Fightcade 승률 분석기 v2.0

Fightcade 대전 기록을 텍스트 파싱으로 분석하고 랭킹을 관리하는 웹 애플리케이션입니다.

## ✨ v2.0 변경사항

- **크롤링 제거** → **텍스트 붙여넣기 방식**으로 전환
- Fightcade 봇 차단 문제 해결
- 의존성 대폭 감소 (Selenium 제거)
- 더 빠르고 안정적인 분석

## 📋 사용법

### 1사분면: 승률 조회 (텍스트 파싱)

1. **Fightcade** 웹사이트에서 유저 프로필 → Replays 탭으로 이동
2. 리플레이 목록을 **드래그하여 복사** (Ctrl+C)
3. 앱의 텍스트 입력창에 **붙여넣기** (Ctrl+V)
4. **🎯 승률 추출** 버튼 클릭
5. Fancy한 승률 결과 확인! 🎉

### 입력 데이터 형식 예시

```
2025. 12. 3. 오후 11:51:07
kof98	testgame38	
3
FT3
1
wowjin	
00:11:22
0
0
```

### 2사분면: 랭킹 시스템
- 조회된 유저들의 랭킹 표시
- 현재 기준: 총 승리 횟수

### 3사분면: 유저 리스트 관리
- Add/Delete로 유저 관리
- 검색 기능

### 4사분면: TBD
- 향후 기능 확장 예정

## 🚀 로컬 실행

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 실행
streamlit run app.py

# 3. 브라우저에서 http://localhost:8501 접속
```

## 🌐 Streamlit Cloud 배포

### Step 1: GitHub에 코드 올리기
1. GitHub에서 새 Repository 생성
2. 모든 파일 업로드

### Step 2: Streamlit Cloud 배포
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub로 로그인
3. New app → Repository 선택
4. Main file: `app.py`
5. Deploy!

## 📁 프로젝트 구조

```
fightcade_v2/
├── app.py                    # 메인 앱
├── config.py                 # 설정값
├── data_manager.py           # JSON 데이터 관리
├── ranking.py                # 랭킹 룰
├── quadrant_1_winrate.py     # 1사분면: 텍스트 파싱 승률
├── quadrant_2_ranking.py     # 2사분면: 랭킹
├── quadrant_3_userlist.py    # 3사분면: 유저 리스트
├── quadrant_4_tbd.py         # 4사분면: TBD
├── requirements.txt          # 의존성 (streamlit만!)
└── README.md
```

## 🔧 기술 스택

- **Frontend**: Streamlit
- **Data**: JSON 파일 기반
- **Parsing**: Python regex

## 📝 라이센스

MIT License
