"""
4사분면: TBD (To Be Developed)
- 향후 기능 확장을 위한 빈 공간
- 예시: 게임별 통계, 최근 매치 기록, 설정 등
"""

import streamlit as st


def render_quadrant_4():
    """4사분면 렌더링: TBD"""
    
    st.markdown('<p class="section-title">🚧 Coming Soon</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="tbd-section">
        <div style="text-align: center;">
            <p style="font-size: 4rem; margin-bottom: 1rem;">🔮</p>
            <p style="font-size: 1.5rem; font-weight: 300;">TBD</p>
            <p style="font-size: 0.9rem; color: rgba(255,255,255,0.4); margin-top: 1rem;">
                향후 기능이 추가될 예정입니다
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 향후 추가 가능 기능 힌트
    with st.expander("💡 예정된 기능"):
        st.markdown("""
        - 📊 게임별 통계 분석
        - 📈 승률 추이 그래프
        - 🎯 상대별 추천 전략
        - ⚙️ 설정 (크롤링 옵션, 테마 등)
        - 📋 대전 기록 내보내기
        - 🔔 알림 설정
        """)


# =============================================================================
# 향후 확장용 플레이스홀더 함수들
# =============================================================================

def render_game_stats():
    """게임별 통계 (미구현)"""
    pass


def render_win_rate_chart():
    """승률 추이 차트 (미구현)"""
    pass


def render_settings():
    """설정 페이지 (미구현)"""
    pass


def render_export_options():
    """데이터 내보내기 (미구현)"""
    pass
