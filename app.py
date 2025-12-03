"""
Fightcade 승률 분석기 - 메인 앱
4분면 레이아웃:
- 1사분면: 두 유저 승률 조회
- 2사분면: 랭킹 시스템
- 3사분면: User ID 리스트 관리
- 4사분면: TBD (예약)
"""

import streamlit as st
from config import PAGE_TITLE, PAGE_ICON

# =============================================================================
# 페이지 설정
# =============================================================================
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# 커스텀 CSS
# =============================================================================
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 100%;
    }
    
    /* 사분면 카드 스타일 */
    .quadrant-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        min-height: 400px;
    }
    
    /* 섹션 타이틀 */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #e94560;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e94560;
    }
    
    /* 승률 표시 */
    .win-rate-display {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
    }
    
    .win-rate-a {
        color: #4ecca3;
    }
    
    .win-rate-b {
        color: #ff6b6b;
    }
    
    /* 랭킹 아이템 */
    .ranking-item {
        display: flex;
        align-items: center;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        transition: all 0.2s;
    }
    
    .ranking-item:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateX(5px);
    }
    
    .rank-number {
        font-size: 1.5rem;
        font-weight: 800;
        color: #ffd369;
        width: 50px;
    }
    
    .rank-1 { color: #ffd700; }
    .rank-2 { color: #c0c0c0; }
    .rank-3 { color: #cd7f32; }
    
    /* 유저 리스트 아이템 */
    .user-list-item {
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .user-list-item.highlighted {
        background: rgba(78, 204, 163, 0.2);
        border: 1px solid #4ecca3;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(233, 69, 96, 0.4);
    }
    
    /* 입력 필드 */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        color: #000000 !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #888888;
    }
    
    /* 셀렉트박스 */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.95);
        color: #000000 !important;
    }
    
    /* TBD 섹션 */
    .tbd-section {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 300px;
        color: rgba(255, 255, 255, 0.3);
        font-size: 2rem;
        font-weight: 300;
    }
    
    /* VS 텍스트 */
    .vs-text {
        font-size: 2rem;
        font-weight: 800;
        color: #ffd369;
        text-align: center;
    }
    
    /* 상태 아이콘 */
    .status-icon {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 세션 상태 초기화
# =============================================================================
if "user_a_input" not in st.session_state:
    st.session_state.user_a_input = ""
if "user_b_input" not in st.session_state:
    st.session_state.user_b_input = ""
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "highlighted_user" not in st.session_state:
    st.session_state.highlighted_user = None

# =============================================================================
# 모듈 임포트 (지연 로딩)
# =============================================================================
from quadrant_1_winrate import render_quadrant_1
from quadrant_2_ranking import render_quadrant_2
from quadrant_3_userlist import render_quadrant_3
from quadrant_4_tbd import render_quadrant_4

# =============================================================================
# 메인 레이아웃
# =============================================================================
st.markdown(f"<h1 style='text-align: center; color: #e94560;'>{PAGE_ICON} {PAGE_TITLE}</h1>", 
            unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.6);'>Fightcade 대전 기록 분석 및 랭킹 시스템</p>", 
            unsafe_allow_html=True)

st.markdown("---")

# 2x2 그리드 레이아웃
top_left, top_right = st.columns(2, gap="large")
bottom_left, bottom_right = st.columns(2, gap="large")

# 1사분면: 승률 조회
with top_left:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_1()
    st.markdown('</div>', unsafe_allow_html=True)

# 2사분면: 랭킹 시스템
with top_right:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_2()
    st.markdown('</div>', unsafe_allow_html=True)

# 3사분면: 유저 리스트
with bottom_left:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_3()
    st.markdown('</div>', unsafe_allow_html=True)

# 4사분면: TBD
with bottom_right:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_4()
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# 푸터
# =============================================================================
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8rem;'>"
    "Fightcade 승률 분석기 v1.0 | Data from fightcade.com"
    "</p>",
    unsafe_allow_html=True
)
