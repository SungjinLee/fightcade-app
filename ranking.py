"""
랭킹 룰 모듈
- 랭킹 계산 로직을 별도 분리하여 유지보수 용이
- 추후 weight나 방식 변경 시 이 파일만 수정
"""

from typing import List, Dict, Any
from data_manager import load_ranking, save_ranking


# =============================================================================
# 랭킹 계산 룰 (이 함수들만 수정하면 랭킹 방식 변경 가능)
# =============================================================================

def calculate_score(user_data: Dict[str, Any]) -> float:
    """
    개별 유저의 랭킹 점수 계산
    
    [현재 룰]: 총 승리 횟수
    
    [추후 변경 예시]
    - 승률 기반: return user_data["total_wins"] / max(user_data["total_matches"], 1)
    - 가중치 적용: return user_data["total_wins"] * 1.5 + user_data["total_matches"] * 0.5
    - ELO 방식: 별도 ELO 계산 로직 구현
    
    Args:
        user_data: {"user_id": str, "total_wins": int, "total_matches": int}
    
    Returns:
        float: 랭킹 점수 (높을수록 상위)
    """
    return float(user_data.get("total_wins", 0))


def get_ranking_label() -> str:
    """
    현재 랭킹 기준 설명 텍스트
    UI에 표시할 때 사용
    """
    return "총 승리 횟수"


def format_ranking_display(user_data: Dict[str, Any], rank: int) -> Dict[str, Any]:
    """
    랭킹 표시용 데이터 포맷
    
    Args:
        user_data: 유저 데이터
        rank: 순위 (1부터 시작)
    
    Returns:
        UI 표시용 딕셔너리
    """
    total_matches = user_data.get("total_matches", 0)
    total_wins = user_data.get("total_wins", 0)
    
    # 승률 계산
    win_rate = (total_wins / total_matches * 100) if total_matches > 0 else 0
    
    return {
        "rank": rank,
        "user_id": user_data.get("user_id", "Unknown"),
        "total_wins": total_wins,
        "total_matches": total_matches,
        "win_rate": f"{win_rate:.1f}%",
        "score": calculate_score(user_data)
    }


# =============================================================================
# 랭킹 정렬 및 조회
# =============================================================================

def sort_ranking(ranking_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    랭킹 데이터 정렬
    
    Args:
        ranking_data: 정렬할 랭킹 리스트
    
    Returns:
        정렬된 랭킹 리스트 (점수 내림차순)
    """
    return sorted(
        ranking_data,
        key=lambda x: calculate_score(x),
        reverse=True
    )


def get_sorted_ranking() -> List[Dict[str, Any]]:
    """
    정렬된 전체 랭킹 조회
    
    Returns:
        정렬 및 포맷된 랭킹 리스트
    """
    ranking_data = load_ranking()
    sorted_data = sort_ranking(ranking_data)
    
    result = []
    for idx, user_data in enumerate(sorted_data, start=1):
        result.append(format_ranking_display(user_data, idx))
    
    return result


def get_user_rank(user_id: str) -> int:
    """
    특정 유저의 순위 조회
    
    Args:
        user_id: 유저 ID
    
    Returns:
        순위 (1부터 시작, 없으면 -1)
    """
    sorted_ranking = get_sorted_ranking()
    for entry in sorted_ranking:
        if entry["user_id"].lower() == user_id.lower():
            return entry["rank"]
    return -1


# =============================================================================
# 랭킹 업데이트 (매치 결과 반영)
# =============================================================================

def update_ranking_from_match(user_a: str, user_b: str, 
                               user_a_wins: int, user_b_wins: int) -> bool:
    """
    매치 결과를 랭킹에 반영
    
    Args:
        user_a, user_b: 유저 ID
        user_a_wins, user_b_wins: 각 유저의 승리 횟수
    
    Returns:
        성공 여부
    """
    ranking_data = load_ranking()
    total_matches = user_a_wins + user_b_wins
    
    # user_a 업데이트
    _update_user_in_ranking(ranking_data, user_a, user_a_wins, total_matches)
    
    # user_b 업데이트
    _update_user_in_ranking(ranking_data, user_b, user_b_wins, total_matches)
    
    return save_ranking(ranking_data)


def _update_user_in_ranking(ranking_data: List[Dict], 
                            user_id: str, wins: int, matches: int) -> None:
    """
    랭킹 데이터 내 특정 유저 업데이트 (내부 함수)
    
    주의: 이 함수는 기존 데이터를 덮어씀 (누적 X)
    누적이 필요하면 data_manager.update_user_ranking 사용
    """
    user_found = False
    for entry in ranking_data:
        if entry["user_id"].lower() == user_id.lower():
            # 기존 유저: 해당 매치 결과로 갱신 (최신 조회 기준)
            entry["total_wins"] = wins
            entry["total_matches"] = matches
            user_found = True
            break
    
    if not user_found:
        ranking_data.append({
            "user_id": user_id,
            "total_wins": wins,
            "total_matches": matches
        })


# =============================================================================
# 향후 확장을 위한 플레이스홀더
# =============================================================================

def calculate_elo_change(winner_elo: float, loser_elo: float, k_factor: float = 32) -> tuple:
    """
    ELO 점수 변화 계산 (향후 ELO 시스템 도입 시 사용)
    
    Args:
        winner_elo: 승자의 현재 ELO
        loser_elo: 패자의 현재 ELO
        k_factor: K 계수 (변동 폭)
    
    Returns:
        (승자 변화량, 패자 변화량)
    """
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner
    
    winner_change = k_factor * (1 - expected_winner)
    loser_change = k_factor * (0 - expected_loser)
    
    return (winner_change, loser_change)


def apply_weight(base_score: float, weight_config: Dict[str, float] = None) -> float:
    """
    가중치 적용 (향후 weight 시스템 도입 시 사용)
    
    Args:
        base_score: 기본 점수
        weight_config: 가중치 설정
    
    Returns:
        가중치 적용된 점수
    """
    if weight_config is None:
        return base_score
    
    # 예시: {"win_multiplier": 1.5, "bonus": 10}
    multiplier = weight_config.get("win_multiplier", 1.0)
    bonus = weight_config.get("bonus", 0)
    
    return base_score * multiplier + bonus
