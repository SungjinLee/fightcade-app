"""
데이터 관리 모듈
- User ID 리스트 저장/불러오기
- 매치 히스토리 저장/불러오기
- 랭킹 데이터 저장/불러오기
"""

import json
import os
from typing import List, Dict, Any, Optional
from config import DATA_DIR, USER_LIST_FILE, MATCH_HISTORY_FILE, RANKING_FILE


# =============================================================================
# 초기화
# =============================================================================
def init_data_directory() -> None:
    """데이터 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_json(filepath: str) -> Any:
    """JSON 파일 로드 (없으면 빈 구조 반환)"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_json(filepath: str, data: Any) -> bool:
    """JSON 파일 저장"""
    try:
        init_data_directory()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


# =============================================================================
# User ID 리스트 관리
# =============================================================================
def load_user_list() -> List[str]:
    """저장된 유저 리스트 불러오기"""
    data = _load_json(USER_LIST_FILE)
    if data is None or not isinstance(data, list):
        return []
    return data


def save_user_list(user_list: List[str]) -> bool:
    """유저 리스트 저장"""
    return _save_json(USER_LIST_FILE, user_list)


def add_user(user_id: str) -> bool:
    """유저 추가 (중복 체크)"""
    user_list = load_user_list()
    if user_id in user_list:
        return False  # 이미 존재
    user_list.append(user_id)
    return save_user_list(user_list)


def remove_user(user_id: str) -> bool:
    """유저 삭제"""
    user_list = load_user_list()
    if user_id not in user_list:
        return False  # 존재하지 않음
    user_list.remove(user_id)
    return save_user_list(user_list)


def search_user(query: str) -> Optional[str]:
    """유저 검색 (부분 매칭, 첫 번째 결과 반환)"""
    user_list = load_user_list()
    query_lower = query.lower()
    for user in user_list:
        if query_lower in user.lower():
            return user
    return None


def user_exists(user_id: str) -> bool:
    """유저 존재 여부 확인"""
    return user_id in load_user_list()


# =============================================================================
# 매치 히스토리 관리
# =============================================================================
def load_match_history() -> Dict[str, Any]:
    """매치 히스토리 불러오기
    
    구조:
    {
        "userA_vs_userB": {
            "user_a": "userA",
            "user_b": "userB",
            "matches": [
                {"winner": "userA", "score_a": 3, "score_b": 1, "date": "..."},
                ...
            ],
            "summary": {
                "total_matches": 10,
                "user_a_wins": 6,
                "user_b_wins": 4
            }
        }
    }
    """
    data = _load_json(MATCH_HISTORY_FILE)
    if data is None or not isinstance(data, dict):
        return {}
    return data


def save_match_history(history: Dict[str, Any]) -> bool:
    """매치 히스토리 저장"""
    return _save_json(MATCH_HISTORY_FILE, history)


def get_match_key(user_a: str, user_b: str) -> str:
    """두 유저 간 매치 키 생성 (정렬하여 일관성 유지)"""
    sorted_users = sorted([user_a.lower(), user_b.lower()])
    return f"{sorted_users[0]}_vs_{sorted_users[1]}"


def save_match_result(user_a: str, user_b: str, matches: List[Dict], summary: Dict) -> bool:
    """특정 유저 쌍의 매치 결과 저장"""
    history = load_match_history()
    key = get_match_key(user_a, user_b)
    history[key] = {
        "user_a": user_a,
        "user_b": user_b,
        "matches": matches,
        "summary": summary
    }
    return save_match_history(history)


def get_match_result(user_a: str, user_b: str) -> Optional[Dict]:
    """특정 유저 쌍의 매치 결과 조회"""
    history = load_match_history()
    key = get_match_key(user_a, user_b)
    return history.get(key)


# =============================================================================
# 랭킹 데이터 관리
# =============================================================================
def load_ranking() -> List[Dict[str, Any]]:
    """랭킹 데이터 불러오기
    
    구조:
    [
        {"user_id": "userA", "total_wins": 15, "total_matches": 20},
        {"user_id": "userB", "total_wins": 10, "total_matches": 18},
        ...
    ]
    """
    data = _load_json(RANKING_FILE)
    if data is None or not isinstance(data, list):
        return []
    return data


def save_ranking(ranking: List[Dict[str, Any]]) -> bool:
    """랭킹 데이터 저장"""
    return _save_json(RANKING_FILE, ranking)


def update_user_ranking(user_id: str, wins: int, matches: int) -> bool:
    """특정 유저의 랭킹 데이터 업데이트 (누적)"""
    ranking = load_ranking()
    
    # 기존 유저 찾기
    user_found = False
    for entry in ranking:
        if entry["user_id"].lower() == user_id.lower():
            entry["total_wins"] += wins
            entry["total_matches"] += matches
            user_found = True
            break
    
    # 새 유저면 추가
    if not user_found:
        ranking.append({
            "user_id": user_id,
            "total_wins": wins,
            "total_matches": matches
        })
    
    return save_ranking(ranking)


def get_user_ranking_stats(user_id: str) -> Optional[Dict]:
    """특정 유저의 랭킹 통계 조회"""
    ranking = load_ranking()
    for entry in ranking:
        if entry["user_id"].lower() == user_id.lower():
            return entry
    return None
