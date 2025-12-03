"""
2사분면: 랭킹 시스템
- 조회된 유저들의 승률 기반 랭킹 표시
- 랭킹 룰은 ranking.py에서 관리
"""

import streamlit as st
from ranking import get_sorted_ranking, get_ranking_label


def render_quadrant_2():
    """2사분면 렌더링: 랭킹 시스템"""
    
    st.markdown('<p class="section-title">🏆 랭킹</p>', unsafe_allow_html=True)
    
    # 현재 랭킹 기준 표시
    st.markdown(f"""
    <p style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-bottom: 1rem;">
        현재 기준: <strong style="color: #ffd369;">{get_ranking_label()}</strong>
    </p>
    """, unsafe_allow_html=True)
    
    # 랭킹 데이터 로드
    ranking_data = get_sorted_ranking()
    
    if not ranking_data:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: rgba(255,255,255,0.4);">
            <p style="font-size: 2.5rem;">📊</p>
            <p>아직 랭킹 데이터가 없습니다.</p>
            <p style="font-size: 0.85rem;">1사분면에서 승률을 조회하면<br>자동으로 랭킹에 반영됩니다.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 새로고침 버튼
    if st.button("🔄 랭킹 새로고침", key="btn_refresh_ranking"):
        st.rerun()
    
    # 랭킹 리스트 표시
    st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
    
    for entry in ranking_data[:10]:  # 상위 10명만 표시
        rank = entry["rank"]
        user_id = entry["user_id"]
        total_wins = entry["total_wins"]
        total_matches = entry["total_matches"]
        win_rate = entry["win_rate"]
        
        # 순위별 색상
        rank_class = f"rank-{rank}" if rank <= 3 else ""
        medal = _get_rank_medal(rank)
        
        st.markdown(f"""
        <div class="ranking-item">
            <span class="rank-number {rank_class}">{medal} {rank}</span>
            <div style="flex: 1; margin-left: 1rem;">
                <p style="font-size: 1.1rem; font-weight: 600; margin: 0; color: white;">
                    {user_id}
                </p>
                <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin: 0;">
                    {total_wins}승 / {total_matches}전 ({win_rate})
                </p>
            </div>
            <span style="font-size: 1.5rem; font-weight: 700; color: #4ecca3;">
                {total_wins}
            </span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 더 많은 데이터가 있으면 표시
    if len(ranking_data) > 10:
        st.markdown(f"""
        <p style="text-align: center; color: rgba(255,255,255,0.4); 
                  font-size: 0.85rem; margin-top: 1rem;">
            +{len(ranking_data) - 10}명 더 있음
        </p>
        """, unsafe_allow_html=True)


def _get_rank_medal(rank: int) -> str:
    """순위별 메달 이모지 반환"""
    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }
    return medals.get(rank, "")


def render_ranking_card(entry: dict) -> str:
    """
    단일 랭킹 카드 HTML 생성
    (추후 커스터마이징 용이하도록 분리)
    """
    rank = entry["rank"]
    user_id = entry["user_id"]
    total_wins = entry["total_wins"]
    total_matches = entry["total_matches"]
    win_rate = entry["win_rate"]
    
    rank_class = f"rank-{rank}" if rank <= 3 else ""
    medal = _get_rank_medal(rank)
    
    return f"""
    <div class="ranking-item">
        <span class="rank-number {rank_class}">{medal} {rank}</span>
        <div style="flex: 1; margin-left: 1rem;">
            <p style="font-size: 1.1rem; font-weight: 600; margin: 0; color: white;">
                {user_id}
            </p>
            <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin: 0;">
                {total_wins}승 / {total_matches}전 ({win_rate})
            </p>
        </div>
        <span style="font-size: 1.5rem; font-weight: 700; color: #4ecca3;">
            {total_wins}
        </span>
    </div>
    """
