"""
설정값 모음
- 크롤링 관련 상수
- 파일 경로
- UI 설정
"""

# =============================================================================
# 사이트 설정
# =============================================================================
BASE_URL = "https://www.fightcade.com"
USER_PAGE_URL = f"{BASE_URL}/id/{{user_id}}"

# =============================================================================
# 크롤링 설정
# =============================================================================
MAX_PAGES_TO_CRAWL = 5  # 최대 크롤링 페이지 수
ROWS_PER_PAGE = 15      # 페이지당 라인 수
CRAWL_TIMEOUT = 30000   # 타임아웃 (ms)

# =============================================================================
# XPath 설정 (견고성을 위해 CSS Selector도 병행 사용 권장)
# =============================================================================
XPATH = {
    # 네비게이션
    "replay_tab": "/html/body/div/div/div/div/div/div/nav/ul/li[2]/a/h2",
    "search_input": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[1]/div/input",
    "next_page": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[2]/div[2]/div/nav/a[2]/span/i",
    "prev_page": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[2]/div[2]/div/nav/a[1]/span/i",
    
    # 테이블 행 템플릿 (row_index는 1부터 시작)
    "row_id1": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[1]/table/tbody/tr[{row}]/td[3]/a",
    "row_id2": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[1]/table/tbody/tr[{row}]/td[7]/a",
    "row_score1": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[1]/table/tbody/tr[{row}]/td[4]/p/strong",
    "row_score2": "/html/body/div/div/div/div/div/div/section/div[2]/div/div[2]/div[1]/table/tbody/tr[{row}]/td[6]/p/strong",
}

# CSS Selectors (XPath 백업용)
CSS_SELECTORS = {
    "replay_tab": "nav ul li:nth-child(2) a h2",
    "table_rows": "table tbody tr",
    "search_input": "section input[type='text']",
}

# =============================================================================
# 데이터 저장 경로
# =============================================================================
DATA_DIR = "data"
USER_LIST_FILE = f"{DATA_DIR}/user_list.json"
MATCH_HISTORY_FILE = f"{DATA_DIR}/match_history.json"
RANKING_FILE = f"{DATA_DIR}/ranking.json"

# =============================================================================
# UI 설정
# =============================================================================
PAGE_TITLE = "Fightcade 승률 분석기"
PAGE_ICON = "🎮"
