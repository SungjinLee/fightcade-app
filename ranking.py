"""
랭킹 룰 모듈 (Elo Rating 기반)
=============================================================================
수정된 Elo Rating 시스템

정렬 기준:
1순위: Rating (MMR)
2순위: 승률
3순위: 판수

최소 9판 이상 플레이해야 랭킹에 반영됨
=============================================================================
"""

from typing import List, Dict, Any
from data_manager import (
    get_all_player_ratings,
    MIN_GAMES_FOR_RANKING
)


# =============================================================================
# 랭킹 계산 메인 함수
# =============================================================================
def calculate_ranking() -> List[Dict[str, Any]]:
    """
    전체 랭킹 계산 (Elo Rating 기반)
    
    Returns:
        [{"rank": 1, "user_id": "player", "rating": 1500, "wins": 10, ...}, ...]
    """
    # Rating 기준 정렬된 플레이어 목록 조회
    players = get_all_player_ratings()
    
    if not players:
        return []
    
    # 순위 부여
    result = []
    for rank, player_data in enumerate(players, start=1):
        result.append({
            "rank": rank,
            "user_id": player_data["user_id"],
            "rating": player_data["rating"],
            "rd": player_data["rd"],
            "wins": player_data["wins"],
            "losses": player_data["losses"],
            "games": player_data["games"],
            "win_rate": player_data["win_rate"]
        })
    
    return result


# =============================================================================
# 랭킹 라벨 (UI 표시용)
# =============================================================================
def get_ranking_label() -> str:
    """현재 랭킹 기준 설명"""
    return f"Elo Rating (min {MIN_GAMES_FOR_RANKING} games)"


def get_ranking_description() -> str:
    """랭킹 룰 상세 설명"""
    return f"""
    **랭킹 산정 기준 (Elo Rating)**
    - 기본 점수: 1200점
    - 승리 시 점수 상승, 패배 시 하락
    - 스코어 차이(마진)에 따라 가중치 적용
    - 최소 {MIN_GAMES_FOR_RANKING}판 이상 플레이 필요
    
    **정렬 순서**
    1. Rating 점수
    2. 승률
    3. 총 판수
    """
