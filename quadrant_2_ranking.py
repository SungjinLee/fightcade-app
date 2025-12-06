"""
2사분면: 랭킹 시스템
- 직접 대결 > 총 승수 기준 랭킹
- 이미지로 표시 + 다운로드/복사 버튼
"""

import io
import base64
import streamlit as st
import streamlit.components.v1 as components

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from ranking import calculate_ranking, get_ranking_label


# =============================================================================
# 이미지 생성
# =============================================================================
def create_ranking_image(ranking_data: list) -> bytes:
    """랭킹 이미지 생성"""
    if not PIL_AVAILABLE or not ranking_data:
        return None
    
    # 이미지 크기 (플레이어 수에 따라 조정)
    num_players = min(len(ranking_data), 15)  # 최대 15명
    width = 400
    header_height = 50
    row_height = 35
    height = header_height + (num_players * row_height) + 30
    
    bg_color = (26, 26, 46)
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 폰트
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_row = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except:
        font_title = ImageFont.load_default()
        font_row = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 색상
    gold = (255, 211, 105)
    silver = (192, 192, 192)
    bronze = (205, 127, 50)
    white = (255, 255, 255)
    gray = (150, 150, 150)
    green = (78, 204, 163)
    
    # 헤더
    draw.text((width // 2, 25), "RANKING", fill=gold, font=font_title, anchor="mm")
    
    # 구분선
    draw.line([(20, header_height - 5), (width - 20, header_height - 5)], fill=(50, 50, 70), width=2)
    
    # 랭킹 행
    for i, entry in enumerate(ranking_data[:num_players]):
        y = header_height + (i * row_height) + 15
        
        rank = entry["rank"]
        user_id = entry["user_id"]
        wins = entry["wins"]
        losses = entry["losses"]
        win_rate = entry.get("win_rate", 0)
        
        # 순위 색상
        if rank == 1:
            rank_color = gold
        elif rank == 2:
            rank_color = silver
        elif rank == 3:
            rank_color = bronze
        else:
            rank_color = white
        
        # 순위 (숫자)
        draw.text((35, y), f"{rank}.", fill=rank_color, font=font_row, anchor="mm")
        
        # 유저 ID
        draw.text((100, y), user_id[:15], fill=white, font=font_row, anchor="lm")
        
        # 전적 (W:L)
        record = f"{wins}:{losses}"
        draw.text((280, y), record, fill=green, font=font_row, anchor="mm")
        
        # 승률
        rate_text = f"{win_rate:.1f}%"
        draw.text((350, y), rate_text, fill=gray, font=font_small, anchor="mm")
    
    # 푸터
    draw.text((width // 2, height - 12), "H2H > Win Rate > Games", fill=gray, font=font_small, anchor="mm")
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    result = img_bytes.getvalue()
    img_bytes.close()  # 명시적으로 닫기
    
    return result


# =============================================================================
# UI 렌더링
# =============================================================================
def render_quadrant_2():
    """2사분면 렌더링: 랭킹 시스템"""
    
    st.markdown('<p class="section-title">🏆 랭킹</p>', unsafe_allow_html=True)
    
    # 랭킹 데이터 로드
    ranking_data = calculate_ranking()
    
    if not ranking_data:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);">
            <p style="font-size: 2rem;">📊</p>
            <p>랭킹 데이터가 없습니다.</p>
            <p style="font-size: 0.8rem;">1사분면에서 대전 기록을 추가하면<br>자동으로 랭킹에 반영됩니다.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 이미지 생성
    img_bytes = create_ranking_image(ranking_data)
    
    if img_bytes:
        _display_ranking_image(img_bytes, ranking_data)
    else:
        _display_ranking_text(ranking_data)
    
    # 새로고침 버튼
    if st.button("🔄 새로고침", key="btn_refresh_ranking", use_container_width=True):
        st.rerun()


def _display_ranking_image(img_bytes: bytes, ranking_data: list):
    """이미지로 랭킹 표시"""
    
    img_b64 = base64.b64encode(img_bytes).decode()
    
    # 다운로드 버튼
    col1, col2 = st.columns([3, 1])
    with col2:
        st.download_button(
            label="💾 저장",
            data=img_bytes,
            file_name="ranking.png",
            mime="image/png",
            use_container_width=True
        )
    
    # 높이 계산 (15명 기준)
    num_players = min(len(ranking_data), 15)
    img_height = 50 + (num_players * 35) + 30
    
    # 최대 표시 높이 (약 8명 분량, 그 이상은 스크롤)
    max_display_height = 320
    needs_scroll = img_height > max_display_height
    
    # 이미지 + 복사 버튼
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            .scroll-container {{
                max-height: {max_display_height}px;
                overflow-y: {'auto' if needs_scroll else 'hidden'};
                scrollbar-width: thin;
                scrollbar-color: #e94560 rgba(255,255,255,0.1);
            }}
            .scroll-container::-webkit-scrollbar {{
                width: 6px;
            }}
            .scroll-container::-webkit-scrollbar-track {{
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
            }}
            .scroll-container::-webkit-scrollbar-thumb {{
                background: #e94560;
                border-radius: 3px;
            }}
            .container {{ position: relative; display: inline-block; width: 100%; }}
            .ranking-image {{ width: 100%; max-width: 400px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); display: block; margin: 0 auto; }}
            .copy-btn {{ position: absolute; top: 5px; right: 5px; background: linear-gradient(135deg, #e94560, #0f3460); color: white; border: none; border-radius: 6px; padding: 6px 12px; cursor: pointer; font-weight: 600; font-size: 12px; z-index: 10; }}
            .copy-btn:hover {{ transform: translateY(-1px); }}
            .copy-btn.success {{ background: #4ecca3; }}
        </style>
    </head>
    <body>
        <div class="scroll-container">
            <div class="container">
                <img id="rankImg" class="ranking-image" src="data:image/png;base64,{img_b64}" />
                <button id="copyBtn" class="copy-btn" onclick="copyImage()">📋 복사</button>
            </div>
        </div>
        <script>
            async function copyImage() {{
                const btn = document.getElementById('copyBtn');
                try {{
                    const img = document.getElementById('rankImg');
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
    
    # 컴포넌트 높이 (스크롤 영역 포함)
    component_height = min(img_height + 10, max_display_height + 10)
    components.html(html_content, height=component_height, scrolling=False)


def _display_ranking_text(ranking_data: list):
    """텍스트로 랭킹 표시 (이미지 생성 실패 시 폴백)"""
    
    st.markdown(f"""
    <p style="font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-bottom: 0.5rem;">
        기준: <strong style="color: #ffd369;">{get_ranking_label()}</strong>
    </p>
    """, unsafe_allow_html=True)
    
    for entry in ranking_data[:15]:
        rank = entry["rank"]
        user_id = entry["user_id"]
        wins = entry["wins"]
        losses = entry["losses"]
        win_rate = entry.get("win_rate", 0)
        
        if rank == 1:
            medal = "🥇"
            color = "#ffd700"
        elif rank == 2:
            medal = "🥈"
            color = "#c0c0c0"
        elif rank == 3:
            medal = "🥉"
            color = "#cd7f32"
        else:
            medal = f"{rank}."
            color = "white"
        
        st.markdown(f"""
        <div style="padding: 0.5rem; margin: 0.3rem 0; background: rgba(255,255,255,0.03); border-radius: 6px; display: flex; align-items: center;">
            <span style="width: 40px; color: {color}; font-weight: 700;">{medal}</span>
            <span style="flex: 1; color: white;">{user_id}</span>
            <span style="color: #4ecca3; margin-right: 1rem;">{wins}:{losses}</span>
            <span style="color: rgba(255,255,255,0.5); font-size: 0.8rem;">{win_rate:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)
