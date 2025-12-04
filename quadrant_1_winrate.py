"""
1사분면: 텍스트 파싱 기반 승률 조회
- Fightcade 리플레이 목록 텍스트 붙여넣기
- 자동으로 유저 ID 추출 및 승률 계산
- Fancy한 결과 표시
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import streamlit as st


# =============================================================================
# 데이터 클래스
# =============================================================================
@dataclass
class MatchResult:
    """단일 경기 결과"""
    date: str
    game: str
    player1: str
    score1: int
    player2: str
    score2: int
    winner: str
    match_type: str  # FT3, FT5 등


@dataclass
class HeadToHeadSummary:
    """1:1 대전 요약"""
    player_a: str
    player_b: str
    total_matches: int
    player_a_wins: int
    player_b_wins: int
    matches: List[MatchResult]


# =============================================================================
# 텍스트 파싱 로직
# =============================================================================
def parse_replay_text(raw_text: str) -> Tuple[Optional[HeadToHeadSummary], Optional[str]]:
    """
    Fightcade 리플레이 텍스트를 파싱하여 승률 정보 추출
    
    Args:
        raw_text: 붙여넣은 리플레이 텍스트
    
    Returns:
        (HeadToHeadSummary 또는 None, 에러 메시지 또는 None)
    """
    if not raw_text or not raw_text.strip():
        return None, "텍스트를 입력해주세요."
    
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
    
    if len(lines) < 9:
        return None, "데이터가 너무 짧습니다. 최소 1경기 이상의 데이터를 붙여넣어주세요."
    
    matches: List[MatchResult] = []
    all_players: set = set()
    
    # 날짜 패턴으로 경기 시작점 찾기
    date_pattern = re.compile(r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.')
    
    i = 0
    while i < len(lines):
        # 날짜 라인 찾기
        if date_pattern.match(lines[i]):
            try:
                match_data = _parse_single_match(lines, i)
                if match_data:
                    matches.append(match_data)
                    all_players.add(match_data.player1.lower())
                    all_players.add(match_data.player2.lower())
                    i += 9  # 다음 경기로
                    continue
            except (IndexError, ValueError):
                pass
        i += 1
    
    if not matches:
        return None, "경기 데이터를 파싱할 수 없습니다. 올바른 형식인지 확인해주세요."
    
    # 유저가 정확히 2명인지 확인
    unique_players = list(all_players)
    if len(unique_players) != 2:
        player_list = ", ".join(sorted(all_players))
        return None, f"정확히 2명의 유저 데이터가 필요합니다. 감지된 유저: {player_list}"
    
    # 원본 대소문자 유지를 위해 첫 등장 기준으로 이름 찾기
    player_a_original = _find_original_case(matches, unique_players[0])
    player_b_original = _find_original_case(matches, unique_players[1])
    
    # 승리 횟수 계산
    player_a_wins = sum(
        1 for m in matches 
        if m.winner.lower() == unique_players[0]
    )
    player_b_wins = len(matches) - player_a_wins
    
    summary = HeadToHeadSummary(
        player_a=player_a_original,
        player_b=player_b_original,
        total_matches=len(matches),
        player_a_wins=player_a_wins,
        player_b_wins=player_b_wins,
        matches=matches
    )
    
    return summary, None


def _parse_single_match(lines: List[str], start_idx: int) -> Optional[MatchResult]:
    """
    단일 경기 파싱
    
    예상 구조 (start_idx부터):
    [0] 날짜/시간: 2025. 12. 3. 오후 11:51:07
    [1] 게임 + 유저1: kof98	testgame38
    [2] 유저1 점수: 3
    [3] 매치타입: FT3
    [4] 유저2 점수: 1
    [5] 유저2: wowjin
    [6] 경기시간: 00:11:22
    [7] 기타1: 0
    [8] 기타2: 0
    """
    if start_idx + 8 >= len(lines):
        return None
    
    date_str = lines[start_idx]
    
    # 게임명 + 유저1 (탭으로 구분)
    game_player1_line = lines[start_idx + 1]
    parts = re.split(r'\t+', game_player1_line)
    
    if len(parts) >= 2:
        game = parts[0].strip()
        player1 = parts[1].strip()
    else:
        # 탭이 없으면 공백으로 분리 시도
        parts = game_player1_line.split()
        if len(parts) >= 2:
            game = parts[0]
            player1 = parts[1]
        else:
            return None
    
    # 점수들
    try:
        score1 = int(lines[start_idx + 2])
        match_type = lines[start_idx + 3]  # FT3, FT5 등
        score2 = int(lines[start_idx + 4])
    except ValueError:
        return None
    
    # 유저2
    player2 = lines[start_idx + 5].strip()
    
    # 승자 결정
    winner = player1 if score1 > score2 else player2
    
    return MatchResult(
        date=date_str,
        game=game,
        player1=player1,
        score1=score1,
        player2=player2,
        score2=score2,
        winner=winner,
        match_type=match_type
    )


def _find_original_case(matches: List[MatchResult], player_lower: str) -> str:
    """매치 리스트에서 원본 대소문자 형태의 플레이어 이름 찾기"""
    for match in matches:
        if match.player1.lower() == player_lower:
            return match.player1
        if match.player2.lower() == player_lower:
            return match.player2
    return player_lower


# =============================================================================
# UI 렌더링
# =============================================================================
def render_quadrant_1():
    """1사분면 렌더링: 텍스트 파싱 기반 승률 조회"""
    
    st.markdown('<p class="section-title">⚔️ 승률 조회</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <p style="font-size: 0.85rem; color: rgba(255,255,255,0.6); margin-bottom: 1rem;">
        Fightcade 리플레이 목록을 복사하여 아래에 붙여넣기 하세요.
    </p>
    """, unsafe_allow_html=True)
    
    # 텍스트 입력 영역
    replay_text = st.text_area(
        "리플레이 데이터",
        height=200,
        placeholder="Fightcade 리플레이 화면에서 복사한 텍스트를 여기에 붙여넣기...",
        key="replay_text_input",
        label_visibility="collapsed"
    )
    
    # 추출 버튼
    if st.button("🎯 승률 추출", key="btn_extract", use_container_width=True):
        if replay_text:
            summary, error = parse_replay_text(replay_text)
            
            if error:
                st.error(f"❌ {error}")
                st.session_state.search_result = None
            else:
                st.session_state.search_result = summary
                st.success("✅ 파싱 완료!")
        else:
            st.warning("텍스트를 입력해주세요.")
    
    # 결과 표시
    _display_fancy_result()


def _display_fancy_result():
    """Fancy한 승률 결과 표시"""
    
    summary: Optional[HeadToHeadSummary] = st.session_state.get("search_result")
    
    if not summary:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.5);">
            <p style="font-size: 3rem;">📋</p>
            <p>리플레이 데이터를 붙여넣고<br>승률 추출 버튼을 눌러주세요</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    total = summary.total_matches
    a_wins = summary.player_a_wins
    b_wins = summary.player_b_wins
    player_a = summary.player_a
    player_b = summary.player_b
    
    # 승률 계산
    a_rate = (a_wins / total) * 100 if total > 0 else 0
    b_rate = (b_wins / total) * 100 if total > 0 else 0
    
    # 승자 하이라이트 결정
    if a_wins > b_wins:
        a_glow = "box-shadow: 0 0 20px rgba(78, 204, 163, 0.5);"
        b_glow = ""
        a_crown = "👑 "
        b_crown = ""
    elif b_wins > a_wins:
        a_glow = ""
        b_glow = "box-shadow: 0 0 20px rgba(255, 107, 107, 0.5);"
        a_crown = ""
        b_crown = "👑 "
    else:
        a_glow = ""
        b_glow = ""
        a_crown = ""
        b_crown = ""
    
    # 총 경기수 표시
    st.markdown(f"""
    <div style="text-align: center; margin: 1.5rem 0;">
        <span style="background: rgba(255, 211, 105, 0.2); padding: 0.5rem 1.5rem; 
                     border-radius: 20px; font-size: 1.1rem; color: #ffd369;">
            ⚔️ 총 {total}전
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # 대결 카드
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; 
                gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap;">
        
        <!-- Player A 카드 -->
        <div style="background: linear-gradient(135deg, rgba(78, 204, 163, 0.2), rgba(78, 204, 163, 0.05));
                    border: 2px solid #4ecca3; border-radius: 16px; padding: 1.5rem 2rem;
                    text-align: center; min-width: 180px; {a_glow}">
            <p style="font-size: 1.1rem; color: #4ecca3; margin: 0; font-weight: 600;">
                {a_crown}{player_a}
            </p>
            <p style="font-size: 3.5rem; font-weight: 800; color: #4ecca3; margin: 0.5rem 0;">
                {a_wins}
            </p>
            <p style="font-size: 1.5rem; color: #4ecca3; margin: 0;">
                {a_rate:.1f}%
            </p>
        </div>
        
        <!-- VS -->
        <div style="font-size: 2rem; font-weight: 800; color: #ffd369; padding: 0 0.5rem;">
            VS
        </div>
        
        <!-- Player B 카드 -->
        <div style="background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 107, 107, 0.05));
                    border: 2px solid #ff6b6b; border-radius: 16px; padding: 1.5rem 2rem;
                    text-align: center; min-width: 180px; {b_glow}">
            <p style="font-size: 1.1rem; color: #ff6b6b; margin: 0; font-weight: 600;">
                {b_crown}{player_b}
            </p>
            <p style="font-size: 3.5rem; font-weight: 800; color: #ff6b6b; margin: 0.5rem 0;">
                {b_wins}
            </p>
            <p style="font-size: 1.5rem; color: #ff6b6b; margin: 0;">
                {b_rate:.1f}%
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 승률 바
    st.markdown(f"""
    <div style="display: flex; height: 35px; border-radius: 20px; overflow: hidden; 
                margin: 1.5rem 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="width: {a_rate}%; background: linear-gradient(90deg, #4ecca3, #45b393); 
                    display: flex; align-items: center; justify-content: center; 
                    font-weight: 700; color: white; font-size: 0.95rem;
                    min-width: {20 if a_rate > 0 else 0}px;">
            {f'{a_rate:.0f}%' if a_rate >= 15 else ''}
        </div>
        <div style="width: {b_rate}%; background: linear-gradient(90deg, #ff6b6b, #ee5a5a); 
                    display: flex; align-items: center; justify-content: center; 
                    font-weight: 700; color: white; font-size: 0.95rem;
                    min-width: {20 if b_rate > 0 else 0}px;">
            {f'{b_rate:.0f}%' if b_rate >= 15 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 상세 기록
    with st.expander(f"📋 상세 대전 기록 ({len(summary.matches)}경기)"):
        _display_match_history(summary)


def _display_match_history(summary: HeadToHeadSummary):
    """상세 대전 기록 표시"""
    
    for idx, match in enumerate(summary.matches, 1):
        # 승자 색상 결정
        if match.winner.lower() == summary.player_a.lower():
            winner_color = "#4ecca3"
            p1_style = "font-weight: 700;" if match.player1.lower() == summary.player_a.lower() else ""
            p2_style = "font-weight: 700;" if match.player2.lower() == summary.player_a.lower() else ""
        else:
            winner_color = "#ff6b6b"
            p1_style = "font-weight: 700;" if match.player1.lower() == summary.player_b.lower() else ""
            p2_style = "font-weight: 700;" if match.player2.lower() == summary.player_b.lower() else ""
        
        st.markdown(f"""
        <div style="padding: 0.6rem 1rem; margin: 0.4rem 0; 
                    background: rgba(255,255,255,0.03); border-radius: 8px;
                    border-left: 3px solid {winner_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <span style="color: rgba(255,255,255,0.4); font-size: 0.8rem;">#{idx}</span>
                <span style="flex: 1; text-align: center;">
                    <span style="{p1_style} color: white;">{match.player1}</span>
                    <span style="color: #4ecca3; font-weight: 700; margin: 0 0.3rem;">{match.score1}</span>
                    <span style="color: #ffd369;">:</span>
                    <span style="color: #ff6b6b; font-weight: 700; margin: 0 0.3rem;">{match.score2}</span>
                    <span style="{p2_style} color: white;">{match.player2}</span>
                </span>
                <span style="color: {winner_color}; font-size: 0.85rem;">🏆 {match.winner}</span>
            </div>
            <div style="color: rgba(255,255,255,0.3); font-size: 0.75rem; margin-top: 0.3rem;">
                {match.date} | {match.match_type}
            </div>
        </div>
        """, unsafe_allow_html=True)
