"""
3사분면: User ID 리스트 관리
- Add/Delete 버튼으로 유저 관리
- 검색 기능
- 검색 시 하이라이트 + 1사분면 자동 입력
"""

import streamlit as st
from data_manager import (
    load_user_list, add_user, remove_user, 
    search_user, user_exists
)


def render_quadrant_3():
    """3사분면 렌더링: 유저 리스트 관리"""
    
    st.markdown('<p class="section-title">👥 유저 리스트</p>', unsafe_allow_html=True)
    
    # 검색 섹션
    _render_search_section()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1rem 0;'>", 
                unsafe_allow_html=True)
    
    # Add/Delete 섹션
    _render_add_delete_section()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 1rem 0;'>", 
                unsafe_allow_html=True)
    
    # 유저 리스트 표시
    _render_user_list()


def _render_search_section():
    """검색 섹션 렌더링"""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 유저 검색",
            key="user_search_input",
            placeholder="유저 ID 검색...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_clicked = st.button("검색", key="btn_search_user", use_container_width=True)
    
    if search_clicked and search_query:
        found_user = search_user(search_query)
        
        if found_user:
            st.session_state.highlighted_user = found_user
            # 1사분면에 자동 입력 (user_a에 입력)
            if not st.session_state.get("user_a_input"):
                st.session_state.user_a_input = found_user
            elif not st.session_state.get("user_b_input"):
                st.session_state.user_b_input = found_user
            else:
                # 둘 다 차있으면 user_a를 교체
                st.session_state.user_a_input = found_user
            
            st.success(f"✅ '{found_user}' 발견! 1사분면에 입력됨")
            st.rerun()
        else:
            st.session_state.highlighted_user = None
            st.warning(f"❌ '{search_query}'를 찾을 수 없습니다.")


def _render_add_delete_section():
    """Add/Delete 섹션 렌더링"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_user_id = st.text_input(
            "새 유저 ID",
            key="new_user_input",
            placeholder="추가할 ID",
            label_visibility="collapsed"
        )
        
        if st.button("➕ Add", key="btn_add_user", use_container_width=True):
            if new_user_id:
                if add_user(new_user_id):
                    st.success(f"✅ '{new_user_id}' 추가됨")
                    st.rerun()
                else:
                    st.warning(f"'{new_user_id}'는 이미 존재합니다.")
            else:
                st.warning("유저 ID를 입력해주세요.")
    
    with col2:
        # 삭제할 유저 선택
        user_list = load_user_list()
        delete_user_id = st.selectbox(
            "삭제할 유저",
            options=[""] + user_list,
            key="delete_user_select",
            label_visibility="collapsed"
        )
        
        if st.button("➖ Delete", key="btn_delete_user", use_container_width=True):
            if delete_user_id:
                if remove_user(delete_user_id):
                    st.success(f"🗑️ '{delete_user_id}' 삭제됨")
                    # 하이라이트 해제
                    if st.session_state.get("highlighted_user") == delete_user_id:
                        st.session_state.highlighted_user = None
                    st.rerun()
                else:
                    st.error("삭제 실패")
            else:
                st.warning("삭제할 유저를 선택해주세요.")


def _render_user_list():
    """유저 리스트 렌더링"""
    
    user_list = load_user_list()
    highlighted = st.session_state.get("highlighted_user")
    
    if not user_list:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);">
            <p style="font-size: 2rem;">📝</p>
            <p>등록된 유저가 없습니다.</p>
            <p style="font-size: 0.85rem;">위에서 유저를 추가해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <p style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin-bottom: 0.5rem;">
        총 {len(user_list)}명
    </p>
    """, unsafe_allow_html=True)
    
    # 스크롤 가능한 리스트 영역
    list_container = st.container()
    
    with list_container:
        for user_id in user_list:
            is_highlighted = highlighted and user_id.lower() == highlighted.lower()
            
            # 스타일 결정
            if is_highlighted:
                bg_color = "rgba(78, 204, 163, 0.2)"
                border = "1px solid #4ecca3"
                icon = "✅"
            else:
                bg_color = "rgba(255, 255, 255, 0.03)"
                border = "1px solid transparent"
                icon = ""
            
            # 클릭 가능한 유저 아이템
            col1, col2, col3 = st.columns([1, 6, 1])
            
            with col1:
                if st.button("👆", key=f"select_a_{user_id}", help=f"User A에 입력"):
                    st.session_state.user_a_input = user_id
                    st.session_state.highlighted_user = user_id
                    st.rerun()
            
            with col2:
                st.markdown(f"""
                <div style="padding: 0.5rem 1rem; background: {bg_color}; 
                            border: {border}; border-radius: 6px; margin: 0.2rem 0;">
                    <span style="color: white;">{icon} {user_id}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                if st.button("👆", key=f"select_b_{user_id}", help=f"User B에 입력"):
                    st.session_state.user_b_input = user_id
                    st.rerun()


def highlight_user(user_id: str):
    """외부에서 호출 가능한 하이라이트 설정 함수"""
    st.session_state.highlighted_user = user_id


def clear_highlight():
    """하이라이트 해제"""
    st.session_state.highlighted_user = None
