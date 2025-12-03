"""
1사분면: 두 유저 승률 조회
- 두 유저 ID 입력
- 확인 버튼 클릭 시 대전 기록 크롤링
- 승률을 시각적으로 표시
- 디버그 모드 지원
"""

import streamlit as st
from crawler import crawl_head_to_head_sync, test_api_connection
from data_manager import save_match_result
from ranking import update_ranking_from_match


def render_quadrant_1():
    """1사분면 렌더링: 승률 조회"""
    
    st.markdown('<p class="section-title">⚔️ 승률 조회</p>', unsafe_allow_html=True)
    
    # 입력 필드
    col1, col2 = st.columns(2)
    
    with col1:
        user_a = st.text_input(
            "User A",
            value=st.session_state.get("user_a_input", ""),
            key="input_user_a",
            placeholder="첫 번째 유저 ID"
        )
    
    with col2:
        user_b = st.text_input(
            "User B",
            value=st.session_state.get("user_b_input", ""),
            key="input_user_b",
            placeholder="두 번째 유저 ID"
        )
    
    # 세션 상태 업데이트
    st.session_state.user_a_input = user_a
    st.session_state.user_b_input = user_b
    
    # 버튼 영역
    col_btn1, col_btn2 = st.columns([3, 1])
    
    with col_btn1:
        search_clicked = st.button("🔍 승률 조회", key="btn_check_winrate", use_container_width=True)
    
    with col_btn2:
        debug_mode = st.checkbox("🐛 디버그", key="debug_mode", help="API 응답 상세 정보 표시")
    
    # 확인 버튼 클릭 시
    if search_clicked:
        if not user_a or not user_b:
            st.warning("두 유저 ID를 모두 입력해주세요.")
            return
        
        if user_a.lower() == user_b.lower():
            st.warning("서로 다른 유저 ID를 입력해주세요.")
            return
        
        # 크롤링 실행
        with st.spinner(f"🎮 {user_a} vs {user_b} 대전 기록 수집 중..."):
            progress_container = st.empty()
            
            def update_progress(msg):
                progress_container.info(msg)
            
            result = crawl_head_to_head_sync(user_a, user_b, progress_callback=update_progress)
            progress_container.empty()
        
        # 디버그 정보 표시
        if debug_mode and result.get("debug"):
            with st.expander("🐛 디버그 정보", expanded=True):
                st.json(result["debug"])
        
        if result["success"] and result["summary"]["total_matches"] > 0:
            st.session_state.search_result = result
            
            # 데이터 저장
            save_match_result(
                user_a, user_b,
                result["matches"],
                result["summary"]
            )
            
            # 랭킹 업데이트
            update_ranking_from_match(
                user_a, user_b,
                result["summary"]["user_a_wins"],
                result["summary"]["user_b_wins"]
            )
            
            st.success("✅ 조회 완료!")
        else:
            error_msg = result.get("error", "알 수 없는 오류")
            st.error(f"❌ {error_msg}")
            st.session_state.search_result = None
            
            # 디버그 모드가 아니어도 에러 시 상세 정보 표시
            if result.get("debug"):
                with st.expander("🔧 오류 상세 정보"):
                    st.json(result["debug"])
    
    # API 연결 테스트 버튼 (디버그 모드일 때만)
    if debug_mode:
        if st.button("🔌 API 연결 테스트", key="btn_test_api"):
            with st.spinner("API 연결 테스트 중..."):
                test_result = test_api_connection()
            st.json(test_result)
    
    # 결과 표시
    _display_result()


def _display_result():
    """승률 결과 표시"""
    
    result = st.session_state.get("search_result")
    if not result or not result.get("success"):
        # 기본 안내 메시지
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">
            <p style="font-size: 3rem;">👆</p>
            <p>두 유저의 ID를 입력하고<br>승률 조회 버튼을 눌러주세요</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    summary = result["summary"]
    total = summary["total_matches"]
    a_wins = summary["user_a_wins"]
    b_wins = summary["user_b_wins"]
    user_a = summary["user_a_id"]
    user_b = summary["user_b_id"]
    
    if total == 0:
        st.info("두 유저 간의 대전 기록이 없습니다.")
        return
    
    # 승률 계산
    a_rate = (a_wins / total) * 100 if total > 0 else 0
    b_rate = (b_wins / total) * 100 if total > 0 else 0
    
    # 승률 시각화
    st.markdown(f"""
    <div style="text-align: center; margin: 1rem 0;">
        <p style="font-size: 1rem; color: rgba(255,255,255,0.6);">총 {total}전</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 승률 바
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="font-size: 1.2rem; color: #4ecca3; font-weight: 600;">{user_a}</p>
            <p class="win-rate-display win-rate-a">{a_wins}승</p>
            <p style="font-size: 1.5rem; color: #4ecca3;">{a_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="vs-text" style="padding-top: 2rem;">VS</div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="font-size: 1.2rem; color: #ff6b6b; font-weight: 600;">{user_b}</p>
            <p class="win-rate-display win-rate-b">{b_wins}승</p>
            <p style="font-size: 1.5rem; color: #ff6b6b;">{b_rate:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 프로그레스 바
    st.markdown("<div style='margin: 1rem 0;'>", unsafe_allow_html=True)
    
    # Streamlit의 프로그레스 바 대신 커스텀 HTML 사용
    st.markdown(f"""
    <div style="display: flex; height: 30px; border-radius: 15px; overflow: hidden; margin: 1rem 0;">
        <div style="width: {a_rate}%; background: linear-gradient(90deg, #4ecca3, #45b393); 
                    display: flex; align-items: center; justify-content: center; 
                    font-weight: 600; color: white; font-size: 0.9rem;">
            {a_rate:.0f}%
        </div>
        <div style="width: {b_rate}%; background: linear-gradient(90deg, #ff6b6b, #ee5a5a); 
                    display: flex; align-items: center; justify-content: center; 
                    font-weight: 600; color: white; font-size: 0.9rem;">
            {b_rate:.0f}%
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 상세 기록 (확장 가능)
    with st.expander("📋 상세 대전 기록"):
        if result["matches"]:
            for idx, match in enumerate(result["matches"][:10], 1):  # 최근 10경기
                winner_color = "#4ecca3" if match["winner"].lower() == user_a.lower() else "#ff6b6b"
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.3rem 0; 
                            background: rgba(255,255,255,0.03); border-radius: 4px;">
                    <span style="color: rgba(255,255,255,0.5);">#{idx}</span>
                    <span style="margin-left: 1rem;">{match['id1']} <strong>{match['score1']}</strong></span>
                    <span style="color: #ffd369;"> : </span>
                    <span><strong>{match['score2']}</strong> {match['id2']}</span>
                    <span style="margin-left: 1rem; color: {winner_color};">🏆 {match['winner']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("대전 기록이 없습니다.")
