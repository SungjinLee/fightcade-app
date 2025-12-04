"""
랭킹 룰 모듈
=============================================================================
룰 변경 시 이 파일만 수정하면 됩니다.

현재 룰:
1순위: 직접 대결 (A가 B를 이기면 A > B)
2순위: 총 라운드 승수 (직접 대결이 없으면)
=============================================================================
"""

from typing import List, Dict, Any, Tuple, Set
from data_manager import get_all_players, get_head_to_head, get_player_total_stats


# =============================================================================
# 랭킹 계산 메인 함수
# =============================================================================
def calculate_ranking() -> List[Dict[str, Any]]:
    """
    전체 랭킹 계산
    
    Returns:
        [{"rank": 1, "user_id": "player", "wins": 10, "losses": 5, "games": 3, "note": "..."}, ...]
    """
    players = get_all_players()
    
    if not players:
        return []
    
    # 직접 대결 결과 매트릭스 생성
    h2h_matrix = _build_head_to_head_matrix(players)
    
    # 총 통계
    total_stats = get_player_total_stats()
    
    # 1순위: 직접 대결 기반 정렬
    sorted_players = _sort_by_head_to_head(players, h2h_matrix, total_stats)
    
    # 랭킹 결과 생성
    result = []
    for rank, player in enumerate(sorted_players, start=1):
        stats = total_stats.get(player, {"wins": 0, "losses": 0, "games": 0})
        
        result.append({
            "rank": rank,
            "user_id": player,
            "wins": stats["wins"],
            "losses": stats["losses"],
            "games": stats["games"],
            "win_rate": _calculate_win_rate(stats["wins"], stats["losses"])
        })
    
    return result


def _build_head_to_head_matrix(players: List[str]) -> Dict[str, Dict[str, int]]:
    """
    직접 대결 결과 매트릭스 생성
    
    matrix[A][B] = 1  : A가 B를 이김
    matrix[A][B] = -1 : A가 B에게 짐
    matrix[A][B] = 0  : 대결 없음 또는 무승부
    """
    matrix: Dict[str, Dict[str, int]] = {}
    
    for p in players:
        matrix[p] = {}
        for q in players:
            matrix[p][q] = 0
    
    # 모든 플레이어 쌍에 대해 직접 대결 결과 계산
    for i, p1 in enumerate(players):
        for p2 in players[i+1:]:
            h2h = get_head_to_head(p1, p2)
            
            if h2h["games"] > 0:
                if h2h["player_a_rounds"] > h2h["player_b_rounds"]:
                    matrix[p1][p2] = 1   # p1 승
                    matrix[p2][p1] = -1  # p2 패
                elif h2h["player_a_rounds"] < h2h["player_b_rounds"]:
                    matrix[p1][p2] = -1  # p1 패
                    matrix[p2][p1] = 1   # p2 승
                # 무승부는 0 유지
    
    return matrix


def _sort_by_head_to_head(
    players: List[str], 
    h2h_matrix: Dict[str, Dict[str, int]],
    total_stats: Dict[str, Dict[str, int]]
) -> List[str]:
    """
    직접 대결 + 총 승수 기반 정렬
    
    정렬 기준:
    1. 직접 대결에서 이긴 상대가 많은 순
    2. 총 라운드 승수가 많은 순
    3. 승률이 높은 순
    """
    
    def compare_key(player: str) -> Tuple:
        # 직접 대결 승리 수
        h2h_wins = sum(1 for opp, result in h2h_matrix[player].items() if result == 1)
        h2h_losses = sum(1 for opp, result in h2h_matrix[player].items() if result == -1)
        h2h_score = h2h_wins - h2h_losses
        
        # 총 통계
        stats = total_stats.get(player, {"wins": 0, "losses": 0, "games": 0})
        total_wins = stats["wins"]
        win_rate = _calculate_win_rate(stats["wins"], stats["losses"])
        
        # 정렬 키 (내림차순을 위해 음수)
        return (-h2h_score, -h2h_wins, -total_wins, -win_rate)
    
    return sorted(players, key=compare_key)


def _calculate_win_rate(wins: int, losses: int) -> float:
    """승률 계산"""
    total = wins + losses
    if total == 0:
        return 0.0
    return (wins / total) * 100


# =============================================================================
# 직접 대결 체인 확인 (A > B > C 형태)
# =============================================================================
def get_dominance_chain(players: List[str]) -> List[str]:
    """
    직접 대결 우위 체인 반환
    예: A가 B를 이기고, B가 C를 이기면 [A, B, C]
    """
    h2h_matrix = _build_head_to_head_matrix(players)
    
    # 위상 정렬 시도 (사이클 있으면 부분 결과)
    in_degree = {p: 0 for p in players}
    
    for p1 in players:
        for p2 in players:
            if h2h_matrix[p1][p2] == -1:  # p1이 p2에게 짐 = p2가 p1을 이김
                in_degree[p1] += 1
    
    # 진입 차수가 0인 노드부터 시작 (가장 강한 플레이어)
    result = []
    remaining = set(players)
    
    while remaining:
        # 진입 차수가 가장 낮은 플레이어 선택
        min_degree = float('inf')
        next_player = None
        
        for p in remaining:
            if in_degree[p] < min_degree:
                min_degree = in_degree[p]
                next_player = p
        
        if next_player:
            result.append(next_player)
            remaining.remove(next_player)
            
            # 진입 차수 업데이트
            for p in remaining:
                if h2h_matrix[next_player][p] == 1:  # next_player가 p를 이김
                    in_degree[p] -= 1
    
    return result


# =============================================================================
# 랭킹 라벨 (UI 표시용)
# =============================================================================
def get_ranking_label() -> str:
    """현재 랭킹 기준 설명"""
    return "H2H > Total Rounds"


def get_ranking_description() -> str:
    """랭킹 룰 상세 설명"""
    return """
    **랭킹 산정 기준**
    1. 직접 대결 우위 (A가 B를 이기면 A > B)
    2. 직접 대결이 없으면 총 라운드 승수
    3. 동점 시 승률 순
    """
