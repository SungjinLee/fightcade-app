# 🎮 Fightcade 승률 분석기

Fightcade 대전 기록을 분석하고 랭킹을 관리하는 웹 애플리케이션입니다.

## 📋 기능

### 1사분면: 승률 조회
- 두 유저 ID 입력 후 대전 기록 조회
- 최근 5페이지 (최대 75경기) 분석
- 승률을 시각적으로 표시

### 2사분면: 랭킹 시스템
- 조회된 유저들의 랭킹 표시
- 현재 기준: 총 승리 횟수
- 랭킹 룰은 `ranking.py`에서 쉽게 수정 가능

### 3사분면: 유저 리스트 관리
- Add/Delete로 유저 관리
- 검색 기능 (부분 매칭)
- 검색 시 하이라이트 + 1사분면 자동 입력

### 4사분면: TBD
- 향후 기능 확장 예정

## 🚀 로컬 실행 (개발/테스트용)

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 실행
```bash
streamlit run app.py
```

### 3. 접속
브라우저에서 `http://localhost:8501` 접속

> **참고**: Chrome/Chromium이 설치되어 있어야 합니다. 
> 드라이버는 자동으로 설치됩니다.

## 📁 프로젝트 구조

```
fightcade_app/
├── app.py                    # 메인 앱 (진입점)
├── config.py                 # 설정값
├── crawler.py                # Playwright 크롤러
├── data_manager.py           # JSON 데이터 관리
├── ranking.py                # 랭킹 룰 (★ 수정 포인트)
├── quadrant_1_winrate.py     # 1사분면: 승률 조회
├── quadrant_2_ranking.py     # 2사분면: 랭킹
├── quadrant_3_userlist.py    # 3사분면: 유저 리스트
├── quadrant_4_tbd.py         # 4사분면: TBD
├── requirements.txt          # 의존성
├── README.md                 # 이 파일
└── data/                     # 데이터 저장 (자동 생성)
    ├── user_list.json
    ├── match_history.json
    └── ranking.json
```

## ⚙️ 랭킹 룰 수정 방법

`ranking.py`의 `calculate_score()` 함수를 수정하면 됩니다:

```python
def calculate_score(user_data: Dict[str, Any]) -> float:
    """
    [현재]: 총 승리 횟수
    return float(user_data.get("total_wins", 0))
    
    [예시 1]: 승률 기반
    total = max(user_data["total_matches"], 1)
    return user_data["total_wins"] / total
    
    [예시 2]: 가중치 적용
    return user_data["total_wins"] * 1.5 + user_data["total_matches"] * 0.5
    """
    return float(user_data.get("total_wins", 0))
```

## 🌐 배포 방법 (Streamlit Cloud - 무료)

배포하면 사용자들은 **링크 클릭만으로** 앱을 사용할 수 있습니다!

### 방법 1: GitHub 계정이 있는 경우 (권장)

#### Step 1: GitHub에 코드 올리기
1. [GitHub](https://github.com) 로그인
2. 우측 상단 `+` → `New repository` 클릭
3. Repository name: `fightcade-app` 입력
4. `Create repository` 클릭
5. 다운받은 파일들을 업로드 (Add file → Upload files)

#### Step 2: Streamlit Cloud에 배포
1. [Streamlit Cloud](https://share.streamlit.io) 접속
2. `Sign in with GitHub` 클릭
3. `New app` 클릭
4. 방금 만든 레포지토리 선택
5. Main file path: `app.py` 입력
6. `Deploy!` 클릭

#### Step 3: 완료!
약 2-3분 후 이런 URL이 생성됩니다:
```
https://your-username-fightcade-app.streamlit.app
```
이 링크를 사용자들에게 공유하면 끝!

---

### 방법 2: GitHub 없이 (더 쉬움)

1. [Streamlit Cloud](https://share.streamlit.io) 접속
2. `Sign in with GitHub` (GitHub 계정 없으면 생성)
3. `New app` → `Paste GitHub URL` 대신 `From a template` 선택
4. 파일들을 직접 붙여넣기

---

### 문제 해결

**Q: 배포 후 에러가 나요**
- `packages.txt` 파일이 포함되어 있는지 확인
- Streamlit Cloud 로그에서 에러 메시지 확인

**Q: 크롤링이 안 돼요**
- Fightcade 사이트가 차단했을 수 있음
- 클라우드 IP가 막혔을 경우 다른 배포 서비스 시도

## 📝 라이센스

MIT License
