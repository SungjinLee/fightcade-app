"""
3사분면: 비매너 리스트 관리
- Add/Delete로 비매너 유저 관리
- JSON 파일로 저장
- 검색 기능
"""

import streamlit as st
from data_manager import (
    load_badmanner_list, add_badmanner, remove_badmanner,
    search_badmanner, is_badmanner, get_all_reasons
)


def render_quadrant_3():
    """3사분면 렌더링: 비매너 리스트 관리"""
    
    st.markdown('<p class="section-title">🚫 비매너 리스트</p>', unsafe_allow_html=True)
    
    # 검색 섹션
    _render_search_section()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.5rem 0;'>", 
                unsafe_allow_html=True)
    
    # Add/Delete 섹션
    _render_add_delete_section()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.5rem 0;'>", 
                unsafe_allow_html=True)
    
    # 비매너 리스트 표시
    _render_badmanner_list()


def _render_search_section():
    """검색 섹션"""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 비매너 유저 검색",
            key="badmanner_search_input",
            placeholder="유저 ID 검색...",
            label_visibility="collapsed"
        )
    
    with col2:
        search_clicked = st.button("검색", key="btn_search_badmanner", use_container_width=True)
    
    if search_clicked and search_query:
        found = search_badmanner(search_query)
        
        if found:
            st.session_state.highlighted_badmanner = found.get("user_id", "")
            st.warning(f"⚠️ '{found['user_id']}' - 비매너 유저입니다!")
            if found.get("reason"):
                st.caption(f"사유: {found['reason']}")
        else:
            st.session_state.highlighted_badmanner = None
            st.success(f"✅ '{search_query}'는 비매너 리스트에 없습니다.")


def _render_add_delete_section():
    """Add/Delete 섹션"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**➕ 추가**", unsafe_allow_html=True)
        
        new_user_id = st.text_input(
            "유저 ID",
            key="new_badmanner_input",
            placeholder="추가할 ID",
            label_visibility="collapsed"
        )
        
        # 기존 사유 목록 가져오기
        existing_reasons = get_all_reasons()
        reason_options = ["직접 입력"] + existing_reasons
        
        # 사유 선택 드롭다운
        selected_reason = st.selectbox(
            "사유 선택",
            options=reason_options,
            key="reason_select",
            label_visibility="collapsed"
        )
        
        # 직접 입력 선택 시 텍스트 입력 표시
        if selected_reason == "직접 입력":
            reason = st.text_input(
                "사유",
                key="badmanner_reason_input",
                placeholder="새 사유 입력 (선택)",
                label_visibility="collapsed"
            )
        else:
            reason = selected_reason
        
        if st.button("➕ 추가", key="btn_add_badmanner", use_container_width=True):
            if new_user_id:
                if add_badmanner(new_user_id, reason):
                    st.success(f"🚫 '{new_user_id}' 추가됨")
                    st.rerun()
                else:
                    st.warning(f"'{new_user_id}'는 이미 등록되어 있습니다.")
            else:
                st.warning("유저 ID를 입력해주세요.")
    
    with col2:
        st.markdown("**➖ 삭제**", unsafe_allow_html=True)
        
        # 삭제할 유저 선택
        badmanner_list = load_badmanner_list()
        user_ids = [entry.get("user_id", "") for entry in badmanner_list]
        
        delete_user_id = st.selectbox(
            "삭제할 유저",
            options=[""] + user_ids,
            key="delete_badmanner_select",
            label_visibility="collapsed",
            format_func=lambda x: "삭제할 유저 선택..." if x == "" else x
        )
        
        # 선택된 유저의 사유 표시
        if delete_user_id:
            for entry in badmanner_list:
                if entry.get("user_id") == delete_user_id:
                    reason_text = entry.get("reason", "")
                    if reason_text:
                        st.caption(f"사유: {reason_text}")
                    break
        
        if st.button("➖ 삭제", key="btn_delete_badmanner", use_container_width=True):
            if delete_user_id:
                if remove_badmanner(delete_user_id):
                    st.success(f"✅ '{delete_user_id}' 삭제됨")
                    if st.session_state.get("highlighted_badmanner") == delete_user_id:
                        st.session_state.highlighted_badmanner = None
                    st.rerun()
                else:
                    st.error("삭제 실패")
            else:
                st.warning("삭제할 유저를 선택해주세요.")


def _render_badmanner_list():
    """비매너 리스트 표시"""
    
    badmanner_list = load_badmanner_list()
    highlighted = st.session_state.get("highlighted_badmanner")
    
    if not badmanner_list:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; color: rgba(255,255,255,0.4);">
            <p style="font-size: 2rem;">✨</p>
            <p>등록된 비매너 유저가 없습니다.</p>
            <p style="font-size: 0.8rem;">비매너 유저를 만나면 위에서 추가해주세요.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown(f"""
    <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.3rem;">
        총 {len(badmanner_list)}명
    </p>
    """, unsafe_allow_html=True)
    
    # 리스트 표시
    for entry in badmanner_list:
        user_id = entry.get("user_id", "")
        reason = entry.get("reason", "")
        added_date = entry.get("added_date", "")
        
        is_highlighted = highlighted and user_id.lower() == highlighted.lower()
        
        if is_highlighted:
            bg_color = "rgba(255, 107, 107, 0.2)"
            border = "1px solid #ff6b6b"
        else:
            bg_color = "rgba(255, 255, 255, 0.03)"
            border = "1px solid transparent"
        
        # 사유 툴팁
        reason_text = f" - {reason}" if reason else ""
        date_text = added_date.split(" ")[0] if added_date else ""
        
        st.markdown(f"""
        <div style="padding: 0.5rem 0.8rem; background: {bg_color}; 
                    border: {border}; border-radius: 6px; margin: 0.25rem 0;
                    display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #ff6b6b; font-weight: 600;">🚫 {user_id}</span>
            <span style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">{reason_text}</span>
        </div>
        """, unsafe_allow_html=True)


def highlight_badmanner(user_id: str):
    """하이라이트 설정"""
    st.session_state.highlighted_badmanner = user_id


def clear_highlight():
    """하이라이트 해제"""
    st.session_state.highlighted_badmanner = None
