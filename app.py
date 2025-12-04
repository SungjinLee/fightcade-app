"""
Fightcade 승률 분석기 - 메인 앱
4분면 레이아웃:
- 1사분면: 텍스트 파싱 기반 승률 조회
- 2사분면: 랭킹 시스템 (직접대결 > 총승수)
- 3사분면: 비매너 리스트
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
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .main .block-container {
        padding: 1rem 2rem;
        max-width: 100%;
    }
    
    .quadrant-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        min-height: 350px;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #e94560;
        margin-bottom: 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e94560;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.4rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(233, 69, 96, 0.4);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        color: #000000 !important;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        color: #000000 !important;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.8rem;
    }
    
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.95);
        color: #000000 !important;
    }
    
    .tbd-section {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
        color: rgba(255, 255, 255, 0.3);
        font-size: 1.5rem;
        font-weight: 300;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 세션 상태 초기화
# =============================================================================
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "result_image" not in st.session_state:
    st.session_state.result_image = None
if "highlighted_badmanner" not in st.session_state:
    st.session_state.highlighted_badmanner = None

# =============================================================================
# 모듈 임포트
# =============================================================================
from quadrant_1_winrate import render_quadrant_1
from quadrant_2_ranking import render_quadrant_2
from quadrant_3_badmanner import render_quadrant_3
from quadrant_4_tbd import render_quadrant_4

# =============================================================================
# 메인 레이아웃
# =============================================================================
st.markdown(f"<h1 style='text-align: center; color: #e94560; font-size: 1.8rem;'>{PAGE_ICON} {PAGE_TITLE}</h1>", 
            unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); font-size: 0.85rem; margin-bottom: 1rem;'>Fightcade 대전 기록 분석 · 텍스트 파싱 방식</p>", 
            unsafe_allow_html=True)

# 2x2 그리드
top_left, top_right = st.columns(2, gap="medium")
bottom_left, bottom_right = st.columns(2, gap="medium")

with top_left:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_1()
    st.markdown('</div>', unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_2()
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_left:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_3()
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="quadrant-card">', unsafe_allow_html=True)
    render_quadrant_4()
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# 푸터
# =============================================================================
st.markdown(
    "<p style='text-align: center; color: rgba(255,255,255,0.2); font-size: 0.75rem; margin-top: 1rem;'>"
    "Fightcade 승률 분석기 v2.0"
    "</p>",
    unsafe_allow_html=True
)
