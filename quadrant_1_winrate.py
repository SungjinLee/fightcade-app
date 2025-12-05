"""
1사분면: 텍스트 파싱 기반 승률 조회
- 라운드 합계 기반 승률 (스코어 합산)
- 이미지 생성 + 클립보드 복사
"""

import re
import io
import base64
from typing import List, Tuple, Optional
from dataclasses import dataclass
import streamlit as st
import streamlit.components.v1 as components

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


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
    match_type: str


@dataclass
class HeadToHeadSummary:
    """1:1 대전 요약 (라운드 합계 기반)"""
    player_a: str
    player_b: str
    total_games: int          # 총 경기 수
    total_rounds: int         # 총 라운드 수
    player_a_rounds: int      # Player A 라운드 승
    player_b_rounds: int      # Player B 라운드 승
    winner: str               # 최종 승자
    matches: List[MatchResult]


# =============================================================================
# 텍스트 파싱 로직
# =============================================================================
def parse_replay_text(raw_text: str) -> Tuple[Optional[HeadToHeadSummary], Optional[str]]:
    """Fightcade 리플레이 텍스트를 파싱하여 승률 정보 추출"""
    if not raw_text or not raw_text.strip():
        return None, "텍스트를 입력해주세요."
    
    lines = [line.strip() for line in raw_text.strip().split('\n') if line.strip()]
    
    if len(lines) < 9:
        return None, "데이터가 너무 짧습니다. 최소 1경기 이상의 데이터를 붙여넣어주세요."
    
    matches: List[MatchResult] = []
    all_players: set = set()
    
    date_pattern = re.compile(r'^\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.')
    
    i = 0
    while i < len(lines):
        if date_pattern.match(lines[i]):
            try:
                match_data = _parse_single_match(lines, i)
                if match_data:
                    matches.append(match_data)
                    all_players.add(match_data.player1.lower())
                    all_players.add(match_data.player2.lower())
                    i += 9
                    continue
            except (IndexError, ValueError):
                pass
        i += 1
    
    if not matches:
        return None, "경기 데이터를 파싱할 수 없습니다. 올바른 형식인지 확인해주세요."
    
    unique_players = list(all_players)
    if len(unique_players) != 2:
        player_list = ", ".join(sorted(all_players))
        return None, f"정확히 2명의 유저 데이터가 필요합니다. 감지된 유저: {player_list}"
    
    # 원본 대소문자 찾기
    player_a_original = _find_original_case(matches, unique_players[0])
    player_b_original = _find_original_case(matches, unique_players[1])
    
    # 라운드 합계 계산
    player_a_rounds = 0
    player_b_rounds = 0
    
    for m in matches:
        if m.player1.lower() == unique_players[0]:
            player_a_rounds += m.score1
            player_b_rounds += m.score2
        else:
            player_a_rounds += m.score2
            player_b_rounds += m.score1
    
    total_rounds = player_a_rounds + player_b_rounds
    
    # 승자 결정
    if player_a_rounds > player_b_rounds:
        winner = player_a_original
    elif player_b_rounds > player_a_rounds:
        winner = player_b_original
    else:
        winner = "DRAW"
    
    summary = HeadToHeadSummary(
        player_a=player_a_original,
        player_b=player_b_original,
        total_games=len(matches),
        total_rounds=total_rounds,
        player_a_rounds=player_a_rounds,
        player_b_rounds=player_b_rounds,
        winner=winner,
        matches=matches
    )
    
    return summary, None


def _parse_single_match(lines: List[str], start_idx: int) -> Optional[MatchResult]:
    """단일 경기 파싱"""
    if start_idx + 8 >= len(lines):
        return None
    
    date_str = lines[start_idx]
    game_player1_line = lines[start_idx + 1]
    parts = re.split(r'\t+', game_player1_line)
    
    if len(parts) >= 2:
        game = parts[0].strip()
        player1 = parts[1].strip()
    else:
        parts = game_player1_line.split()
        if len(parts) >= 2:
            game = parts[0]
            player1 = parts[1]
        else:
            return None
    
    try:
        score1 = int(lines[start_idx + 2])
        match_type = lines[start_idx + 3]
        score2 = int(lines[start_idx + 4])
    except ValueError:
        return None
    
    player2 = lines[start_idx + 5].strip()
    
    return MatchResult(
        date=date_str, game=game, player1=player1, score1=score1,
        player2=player2, score2=score2, match_type=match_type
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
# 이미지 생성
# =============================================================================
def create_result_image(summary: HeadToHeadSummary) -> Optional[bytes]:
    """승률 결과 이미지 생성 (작은 크기)"""
    if not PIL_AVAILABLE:
        return None
    
    # 이미지 크기 (작게 조정)
    width, height = 500, 200
    bg_color = (26, 26, 46)
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 색상 정의
    green = (78, 204, 163)
    red = (255, 107, 107)
    gold = (255, 211, 105)
    gray = (150, 150, 150)
    
    # 승률 계산
    a_rate = (summary.player_a_rounds / summary.total_rounds) * 100 if summary.total_rounds > 0 else 0
    b_rate = (summary.player_b_rounds / summary.total_rounds) * 100 if summary.total_rounds > 0 else 0
    
    # 승자 표시
    a_color = green if summary.winner == summary.player_a else red
    b_color = green if summary.winner == summary.player_b else red
    a_prefix = "* " if summary.winner == summary.player_a else ""
    b_prefix = "* " if summary.winner == summary.player_b else ""
    
    # 타이틀
    title = f"TOTAL {summary.total_games} GAMES / {summary.total_rounds} ROUNDS"
    draw.text((width // 2, 20), title, fill=gold, font=font_small, anchor="mm")
    
    # 중앙 스코어
    score_text = f"{summary.player_a_rounds} : {summary.player_b_rounds}"
    draw.text((width // 2, 80), score_text, fill=gold, font=font_large, anchor="mm")
    
    # Player A (왼쪽)
    draw.text((80, 55), f"{a_prefix}{summary.player_a}", fill=a_color, font=font_small, anchor="mm")
    draw.text((80, 110), f"{a_rate:.1f}%", fill=a_color, font=font_medium, anchor="mm")
    
    # Player B (오른쪽)
    draw.text((420, 55), f"{b_prefix}{summary.player_b}", fill=b_color, font=font_small, anchor="mm")
    draw.text((420, 110), f"{b_rate:.1f}%", fill=b_color, font=font_medium, anchor="mm")
    
    # 승률 바
    bar_y = 145
    bar_height = 18
    bar_margin = 40
    bar_width = width - (bar_margin * 2)
    
    draw.rounded_rectangle([bar_margin, bar_y, width - bar_margin, bar_y + bar_height], radius=9, fill=(50, 50, 70))
    
    a_bar_width = int(bar_width * (a_rate / 100))
    if a_bar_width > 0:
        draw.rounded_rectangle([bar_margin, bar_y, bar_margin + a_bar_width, bar_y + bar_height], radius=9, fill=green)
    
    b_bar_width = int(bar_width * (b_rate / 100))
    if b_bar_width > 0:
        draw.rounded_rectangle([width - bar_margin - b_bar_width, bar_y, width - bar_margin, bar_y + bar_height], radius=9, fill=red)
    
    # 푸터
    draw.text((width // 2, height - 15), "Fightcade Win Rate Analyzer", fill=gray, font=font_small, anchor="mm")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    result = img_bytes.getvalue()
    img_bytes.close()  # 명시적으로 닫기
    
    return result


# =============================================================================
# UI 렌더링
# =============================================================================
def render_quadrant_1():
    """1사분면 렌더링"""
    
    st.markdown('<p class="section-title">⚔️ 승률 조회</p>', unsafe_allow_html=True)
    
    # 상단: 결과 이미지
    _display_result_image()
    
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.5rem 0;'>", unsafe_allow_html=True)
    
    # 세션 상태 초기화 (텍스트 입력 키 버전용)
    if "input_key_version" not in st.session_state:
        st.session_state.input_key_version = 0
    
    # 하단: 입력 (키 버전으로 초기화 관리)
    replay_text = st.text_area(
        "리플레이 데이터",
        height=80,
        placeholder="Fightcade 리플레이 텍스트 붙여넣기...",
        key=f"replay_text_input_{st.session_state.input_key_version}",
        label_visibility="collapsed"
    )
    
    # 입력 상태 인디케이터 + 버튼
    col_indicator, col_btn = st.columns([1, 2])
    
    with col_indicator:
        if replay_text.strip():
            char_count = len(replay_text)
            st.markdown(
                f"<span style='color: #4ecca3; font-size: 0.8rem;'>✏️ 입력됨 ({char_count}자)</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<span style='color: rgba(255,255,255,0.4); font-size: 0.8rem;'>📋 입력 대기중</span>",
                unsafe_allow_html=True
            )
    
    with col_btn:
        if st.button("🎯 승률 추출", key="btn_extract", use_container_width=True):
            if replay_text:
                summary, error = parse_replay_text(replay_text)
                
                if error:
                    st.error(f"❌ {error}")
                    st.session_state.search_result = None
                    st.session_state.result_image = None
                else:
                    st.session_state.search_result = summary
                    img_bytes = create_result_image(summary)
                    st.session_state.result_image = img_bytes
                    
                    # 데이터 저장 (2사분면 랭킹용)
                    from data_manager import save_match_data
                    save_match_data(summary.matches)
                    
                    # 입력 텍스트 초기화 (키 버전 증가)
                    st.session_state.input_key_version += 1
                    
                    st.rerun()
            else:
                st.warning("텍스트를 입력해주세요.")


def _display_result_image():
    """이미지 표시 + 복사 버튼"""
    
    summary = st.session_state.get("search_result")
    img_bytes = st.session_state.get("result_image")
    
    if not summary or not img_bytes:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: rgba(255,255,255,0.5);">
            <p style="font-size: 2rem; margin: 0;">📋</p>
            <p style="margin: 0.3rem 0 0 0; font-size: 0.85rem;">리플레이 붙여넣기 → 승률 추출</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    img_b64 = base64.b64encode(img_bytes).decode()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            label="💾 저장",
            data=img_bytes,
            file_name=f"winrate_{summary.player_a}_vs_{summary.player_b}.png",
            mime="image/png",
            use_container_width=True
        )
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            .container {{ position: relative; display: inline-block; width: 100%; }}
            .result-image {{ width: 100%; max-width: 500px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: block; margin: 0 auto; }}
            .copy-btn {{ position: absolute; top: 5px; right: 5px; background: linear-gradient(135deg, #e94560, #0f3460); color: white; border: none; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-weight: 600; font-size: 12px; z-index: 10; }}
            .copy-btn:hover {{ transform: translateY(-1px); }}
            .copy-btn.success {{ background: #4ecca3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <img id="resultImg" class="result-image" src="data:image/png;base64,{img_b64}" />
            <button id="copyBtn" class="copy-btn" onclick="copyImage()">📋 복사</button>
        </div>
        <script>
            async function copyImage() {{
                const btn = document.getElementById('copyBtn');
                try {{
                    const img = document.getElementById('resultImg');
                    const response = await fetch(img.src);
                    const blob = await response.blob();
                    await navigator.clipboard.write([new ClipboardItem({{ 'image/png': blob }})]);
                    btn.innerHTML = '✅ 완료!';
                    btn.classList.add('success');
                    setTimeout(() => {{ btn.innerHTML = '📋 복사'; btn.classList.remove('success'); }}, 2000);
                }} catch (err) {{
                    alert('클립보드 접근이 제한되었습니다. 저장 버튼을 이용해주세요.');
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    components.html(html_content, height=160, scrolling=False)
