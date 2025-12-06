"""
Fightcade 승률 분석기 - 메인 앱
4분면 레이아웃:
- 1사분면: 텍스트 파싱 기반 승률 조회
- 2사분면: 랭킹 시스템 (직접대결 > 총승수)
- 3사분면: 비매너 리스트
- 4사분면: TBD (예약)
"""

import streamlit as st
from datetime import datetime
from config import PAGE_TITLE, PAGE_ICON
from data_manager import (
    export_all_data, import_all_data, load_match_history, load_badmanner_list,
    increment_visit_count, get_visit_count
)

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
    
    /* 컬럼 간격 조정 */
    [data-testid="column"] {
        padding: 0.3rem;
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

# 방문수 카운트 (세션당 1회만)
if "visit_counted" not in st.session_state:
    st.session_state.visit_counted = True
    increment_visit_count()

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

# 상단: 타이틀 + 방문수/데이터 상태
header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown(f"<h1 style='color: #e94560; font-size: 1.8rem; margin: 0;'>{PAGE_ICON} {PAGE_TITLE}</h1>", 
                unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.85rem; margin: 0;'>Fightcade 대전 기록 분석 · 텍스트 파싱 방식</p>", 
                unsafe_allow_html=True)

with header_right:
    # 오늘 방문수
    today_visits = get_visit_count()
    st.markdown(
        f"<p style='color: #ffd369; font-size: 1rem; text-align: right; margin: 0; font-weight: 600;'>"
        f"👥 오늘 방문: {today_visits}</p>",
        unsafe_allow_html=True
    )
    
    # 현재 데이터 상태 표시
    match_count = len(load_match_history())
    badmanner_count = len(load_badmanner_list())
    st.markdown(
        f"<p style='color: rgba(255,255,255,0.5); font-size: 0.85rem; text-align: right; margin: 0;'>"
        f"📊 매치: {match_count} | 🚫 비매너: {badmanner_count}</p>",
        unsafe_allow_html=True
    )

st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.5rem 0 1rem 0;'>", unsafe_allow_html=True)

# 2x2 그리드 - 사분면 구분 개선
top_left, top_right = st.columns(2, gap="large")
bottom_left, bottom_right = st.columns(2, gap="large")

with top_left:
    with st.container(border=True):
        render_quadrant_1()

with top_right:
    with st.container(border=True):
        render_quadrant_2()

with bottom_left:
    with st.container(border=True):
        render_quadrant_3()

with bottom_right:
    with st.container(border=True):
        render_quadrant_4()

# =============================================================================
# 하단: 백업/복원 버튼
# =============================================================================
st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1rem 0 0.5rem 0;'>", unsafe_allow_html=True)

footer_left, footer_center, footer_right = st.columns([2, 2, 1])

with footer_right:
    backup_col, restore_col = st.columns(2)
    
    with backup_col:
        # 다운로드 버튼
        backup_data = export_all_data()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="💾 백업",
            data=backup_data,
            file_name=f"fightcade_backup_{timestamp}.json",
            mime="application/json",
            use_container_width=True,
            key="backup_btn"
        )
    
    with restore_col:
        # 복원 팝오버
        with st.popover("📂 복원", use_container_width=True):
            uploaded_file = st.file_uploader(
                "백업 파일 선택",
                type=["json"],
                key="restore_file",
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                if st.button("✅ 복원 실행", key="restore_confirm", use_container_width=True):
                    try:
                        json_str = uploaded_file.read().decode("utf-8")
                        success, message = import_all_data(json_str)
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    except Exception as e:
                        st.error(f"파일 읽기 오류: {str(e)}")

# =============================================================================
# 푸터
# =============================================================================
st.markdown(
    "<p style='text-align: center; color: rgba(255,255,255,0.2); font-size: 0.75rem; margin-top: 0.5rem;'>"
    "Fightcade 승률 분석기 v2.0"
    "</p>",
    unsafe_allow_html=True
)
