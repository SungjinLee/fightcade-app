"""
1사분면: 텍스트 파싱 기반 승률 조회
- Fightcade 리플레이 목록 텍스트 붙여넣기
- 자동으로 유저 ID 추출 및 승률 계산
- 이미지로 결과 생성 + 클립보드 복사
"""

import re
import io
import base64
from typing import List, Dict, Tuple, Optional
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
    winner: str
    match_type: str


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
    
    player_a_original = _find_original_case(matches, unique_players[0])
    player_b_original = _find_original_case(matches, unique_players[1])
    
    player_a_wins = sum(1 for m in matches if m.winner.lower() == unique_players[0])
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
    winner = player1 if score1 > score2 else player2
    
    return MatchResult(
        date=date_str, game=game, player1=player1, score1=score1,
        player2=player2, score2=score2, winner=winner, match_type=match_type
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
    """승률 결과 이미지 생성"""
    if not PIL_AVAILABLE:
        return None
    
    # 이미지 크기 및 색상 설정
    width, height = 600, 320
    bg_color = (26, 26, 46)  # 다크 블루
    
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트 설정 (시스템 기본 폰트 사용)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 색상 정의
    green = (78, 204, 163)      # Player A 색상
    red = (255, 107, 107)       # Player B 색상
    gold = (255, 211, 105)      # 강조 색상
    white = (255, 255, 255)
    gray = (150, 150, 150)
    
    # 승률 계산
    a_rate = (summary.player_a_wins / summary.total_matches) * 100
    b_rate = (summary.player_b_wins / summary.total_matches) * 100
    
    # 승자 표시
    a_crown = "[WIN] " if summary.player_a_wins > summary.player_b_wins else ""
    b_crown = "[WIN] " if summary.player_b_wins > summary.player_a_wins else ""
    
    # 타이틀 (총 경기 수)
    title = f"TOTAL {summary.total_matches} GAMES"
    draw.text((width // 2, 30), title, fill=gold, font=font_small, anchor="mm")
    
    # 중앙 VS
    draw.text((width // 2, 160), "VS", fill=gold, font=font_medium, anchor="mm")
    
    # Player A (왼쪽)
    a_name = f"{a_crown}{summary.player_a}"
    draw.text((150, 80), a_name, fill=green, font=font_small, anchor="mm")
    draw.text((150, 140), str(summary.player_a_wins), fill=green, font=font_large, anchor="mm")
    draw.text((150, 200), f"{a_rate:.1f}%", fill=green, font=font_medium, anchor="mm")
    
    # Player B (오른쪽)
    b_name = f"{b_crown}{summary.player_b}"
    draw.text((450, 80), b_name, fill=red, font=font_small, anchor="mm")
    draw.text((450, 140), str(summary.player_b_wins), fill=red, font=font_large, anchor="mm")
    draw.text((450, 200), f"{b_rate:.1f}%", fill=red, font=font_medium, anchor="mm")
    
    # 승률 바
    bar_y = 250
    bar_height = 25
    bar_margin = 50
    bar_width = width - (bar_margin * 2)
    
    # 바 배경
    draw.rounded_rectangle(
        [bar_margin, bar_y, width - bar_margin, bar_y + bar_height],
        radius=12, fill=(50, 50, 70)
    )
    
    # Player A 바
    a_bar_width = int(bar_width * (a_rate / 100))
    if a_bar_width > 0:
        draw.rounded_rectangle(
            [bar_margin, bar_y, bar_margin + a_bar_width, bar_y + bar_height],
            radius=12, fill=green
        )
    
    # Player B 바 (오른쪽에서 시작)
    b_bar_width = int(bar_width * (b_rate / 100))
    if b_bar_width > 0:
        draw.rounded_rectangle(
            [width - bar_margin - b_bar_width, bar_y, width - bar_margin, bar_y + bar_height],
            radius=12, fill=red
        )
    
    # 푸터
    footer = "Fightcade Win Rate Analyzer"
    draw.text((width // 2, height - 20), footer, fill=gray, font=font_small, anchor="mm")
    
    # 바이트로 변환
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


# =============================================================================
# UI 렌더링
# =============================================================================
def render_quadrant_1():
    """1사분면 렌더링: 텍스트 파싱 기반 승률 조회"""
    
    st.markdown('<p class="section-title">⚔️ 승률 조회</p>', unsafe_allow_html=True)
    
    # 상단: 결과 이미지 표시
    _display_result_image()
    
    # 구분선
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0.5rem 0;'>", 
                unsafe_allow_html=True)
    
    # 하단: 텍스트 입력 영역 (높이 낮게)
    replay_text = st.text_area(
        "리플레이 데이터",
        height=80,
        placeholder="Fightcade 리플레이 텍스트 붙여넣기...",
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
                st.session_state.result_image = None
            else:
                st.session_state.search_result = summary
                # 이미지 생성
                img_bytes = create_result_image(summary)
                st.session_state.result_image = img_bytes
                st.rerun()
        else:
            st.warning("텍스트를 입력해주세요.")


def _display_result_image():
    """이미지 결과 표시 + 클립보드 복사 버튼"""
    
    summary = st.session_state.get("search_result")
    img_bytes = st.session_state.get("result_image")
    
    if not summary or not img_bytes:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem; color: rgba(255,255,255,0.5);">
            <p style="font-size: 2.5rem; margin: 0;">📋</p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">리플레이 데이터를 붙여넣고<br>승률 추출 버튼을 눌러주세요</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 이미지를 base64로 인코딩
    img_b64 = base64.b64encode(img_bytes).decode()
    
    # st.image로 이미지 표시 + 복사/다운로드 버튼
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # 다운로드 버튼
        st.download_button(
            label="💾 저장",
            data=img_bytes,
            file_name=f"winrate_{summary.player_a}_vs_{summary.player_b}.png",
            mime="image/png",
            use_container_width=True
        )
    
    # 이미지와 복사 버튼을 HTML 컴포넌트로 표시
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            }}
            .container {{
                position: relative;
                display: inline-block;
                width: 100%;
            }}
            .result-image {{
                width: 100%;
                max-width: 100%;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                display: block;
            }}
            .copy-btn {{
                position: absolute;
                top: 8px;
                right: 8px;
                background: linear-gradient(135deg, #e94560, #0f3460);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                cursor: pointer;
                font-weight: 600;
                font-size: 13px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: all 0.3s;
                z-index: 10;
            }}
            .copy-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4);
            }}
            .copy-btn.success {{
                background: #4ecca3;
            }}
            .toast {{
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(78, 204, 163, 0.95);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                opacity: 0;
                transition: opacity 0.3s;
                z-index: 10;
            }}
            .toast.show {{
                opacity: 1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <img id="resultImg" class="result-image" src="data:image/png;base64,{img_b64}" />
            <button id="copyBtn" class="copy-btn" onclick="copyImage()">📋 복사</button>
            <div id="toast" class="toast">✅ 클립보드에 복사됨!</div>
        </div>
        
        <script>
            async function copyImage() {{
                const btn = document.getElementById('copyBtn');
                const toast = document.getElementById('toast');
                
                try {{
                    const img = document.getElementById('resultImg');
                    const response = await fetch(img.src);
                    const blob = await response.blob();
                    
                    await navigator.clipboard.write([
                        new ClipboardItem({{ 'image/png': blob }})
                    ]);
                    
                    // 성공 표시
                    btn.innerHTML = '✅ 완료!';
                    btn.classList.add('success');
                    toast.classList.add('show');
                    
                    setTimeout(() => {{
                        btn.innerHTML = '📋 복사';
                        btn.classList.remove('success');
                        toast.classList.remove('show');
                    }}, 2000);
                    
                }} catch (err) {{
                    // 실패 시 안내
                    btn.innerHTML = '❌ 실패';
                    setTimeout(() => {{
                        btn.innerHTML = '📋 복사';
                        alert('클립보드 접근이 제한되었습니다.\\n이미지를 우클릭하여 복사하거나\\n저장 버튼을 이용해주세요.');
                    }}, 500);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    # HTML 컴포넌트로 렌더링 (높이 조절)
    components.html(html_content, height=220, scrolling=False)
