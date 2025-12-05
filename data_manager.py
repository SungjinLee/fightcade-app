"""
데이터 관리 모듈
- 매치 히스토리 저장/불러오기 (JSON)
- 비매너 리스트 저장/불러오기 (JSON)
- 중복 제거 (날짜 + 유저ID 기반)
"""

import json
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime

# =============================================================================
# 파일 경로 설정
# =============================================================================
DATA_DIR = "data"
MATCH_HISTORY_FILE = f"{DATA_DIR}/match_history.json"
BADMANNER_FILE = f"{DATA_DIR}/badmanner_list.json"


# =============================================================================
# 초기화
# =============================================================================
def init_data_directory() -> None:
    """데이터 디렉토리 생성"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_json(filepath: str) -> Any:
    """JSON 파일 로드"""
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
# 매치 히스토리 관리
# =============================================================================
def _create_match_key(date: str, player1: str, player2: str, score1: int, score2: int) -> str:
    """매치 고유 키 생성 (중복 체크용)"""
    # 플레이어를 정렬하여 일관된 키 생성
    players = sorted([player1.lower(), player2.lower()])
    return f"{date}|{players[0]}|{players[1]}|{score1}|{score2}"


def load_match_history() -> List[Dict[str, Any]]:
    """매치 히스토리 불러오기"""
    data = _load_json(MATCH_HISTORY_FILE)
    if data is None or not isinstance(data, list):
        return []
    return data


def save_match_history(history: List[Dict[str, Any]]) -> bool:
    """매치 히스토리 저장"""
    return _save_json(MATCH_HISTORY_FILE, history)


def save_match_data(matches: List[Any]) -> Tuple[int, int]:
    """
    매치 데이터 저장 (중복 제거)
    
    Returns:
        (새로 추가된 수, 중복으로 스킵된 수)
    """
    history = load_match_history()
    
    # 기존 키 세트 생성
    existing_keys: Set[str] = set()
    for m in history:
        key = _create_match_key(
            m.get("date", ""),
            m.get("player1", ""),
            m.get("player2", ""),
            m.get("score1", 0),
            m.get("score2", 0)
        )
        existing_keys.add(key)
    
    added = 0
    skipped = 0
    
    for match in matches:
        # MatchResult 객체 또는 dict 처리
        if hasattr(match, 'date'):
            match_dict = {
                "date": match.date,
                "game": match.game,
                "player1": match.player1,
                "score1": match.score1,
                "player2": match.player2,
                "score2": match.score2,
                "match_type": match.match_type
            }
        else:
            match_dict = match
        
        key = _create_match_key(
            match_dict.get("date", ""),
            match_dict.get("player1", ""),
            match_dict.get("player2", ""),
            match_dict.get("score1", 0),
            match_dict.get("score2", 0)
        )
        
        if key not in existing_keys:
            history.append(match_dict)
            existing_keys.add(key)
            added += 1
        else:
            skipped += 1
    
    save_match_history(history)
    return added, skipped


def get_all_players() -> List[str]:
    """모든 플레이어 목록 (중복 제거)"""
    history = load_match_history()
    players: Set[str] = set()
    
    for m in history:
        players.add(m.get("player1", "").lower())
        players.add(m.get("player2", "").lower())
    
    # 빈 문자열 제거 후 정렬
    return sorted([p for p in players if p])


def get_head_to_head(player_a: str, player_b: str) -> Dict[str, int]:
    """
    두 플레이어 간 직접 대결 결과
    
    Returns:
        {"player_a_rounds": int, "player_b_rounds": int, "games": int}
    """
    history = load_match_history()
    a_lower = player_a.lower()
    b_lower = player_b.lower()
    
    a_rounds = 0
    b_rounds = 0
    games = 0
    
    for m in history:
        p1 = m.get("player1", "").lower()
        p2 = m.get("player2", "").lower()
        s1 = m.get("score1", 0)
        s2 = m.get("score2", 0)
        
        if (p1 == a_lower and p2 == b_lower):
            a_rounds += s1
            b_rounds += s2
            games += 1
        elif (p1 == b_lower and p2 == a_lower):
            a_rounds += s2
            b_rounds += s1
            games += 1
    
    return {
        "player_a_rounds": a_rounds,
        "player_b_rounds": b_rounds,
        "games": games
    }


def get_player_total_stats() -> Dict[str, Dict[str, int]]:
    """
    모든 플레이어의 총 라운드 승/패 통계
    
    Returns:
        {"player_id": {"wins": int, "losses": int, "games": int}}
    """
    history = load_match_history()
    stats: Dict[str, Dict[str, int]] = {}
    
    for m in history:
        p1 = m.get("player1", "").lower()
        p2 = m.get("player2", "").lower()
        s1 = m.get("score1", 0)
        s2 = m.get("score2", 0)
        
        if p1 not in stats:
            stats[p1] = {"wins": 0, "losses": 0, "games": 0}
        if p2 not in stats:
            stats[p2] = {"wins": 0, "losses": 0, "games": 0}
        
        stats[p1]["wins"] += s1
        stats[p1]["losses"] += s2
        stats[p1]["games"] += 1
        
        stats[p2]["wins"] += s2
        stats[p2]["losses"] += s1
        stats[p2]["games"] += 1
    
    return stats


# =============================================================================
# 비매너 리스트 관리
# =============================================================================
def load_badmanner_list() -> List[Dict[str, Any]]:
    """비매너 리스트 불러오기"""
    data = _load_json(BADMANNER_FILE)
    if data is None or not isinstance(data, list):
        return []
    return data


def save_badmanner_list(badmanner_list: List[Dict[str, Any]]) -> bool:
    """비매너 리스트 저장"""
    return _save_json(BADMANNER_FILE, badmanner_list)


def add_badmanner(user_id: str, reason: str = "") -> bool:
    """비매너 유저 추가 (중복 체크)"""
    badmanner_list = load_badmanner_list()
    
    # 중복 체크
    for entry in badmanner_list:
        if entry.get("user_id", "").lower() == user_id.lower():
            return False
    
    badmanner_list.append({
        "user_id": user_id,
        "reason": reason,
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    return save_badmanner_list(badmanner_list)


def remove_badmanner(user_id: str) -> bool:
    """비매너 유저 삭제"""
    badmanner_list = load_badmanner_list()
    
    for i, entry in enumerate(badmanner_list):
        if entry.get("user_id", "").lower() == user_id.lower():
            badmanner_list.pop(i)
            return save_badmanner_list(badmanner_list)
    
    return False


def is_badmanner(user_id: str) -> bool:
    """비매너 유저인지 확인"""
    badmanner_list = load_badmanner_list()
    for entry in badmanner_list:
        if entry.get("user_id", "").lower() == user_id.lower():
            return True
    return False


def search_badmanner(query: str) -> Optional[Dict[str, Any]]:
    """비매너 유저 검색"""
    badmanner_list = load_badmanner_list()
    query_lower = query.lower()
    
    for entry in badmanner_list:
        if query_lower in entry.get("user_id", "").lower():
            return entry
    
    return None


def get_all_reasons() -> List[str]:
    """
    기존에 등록된 모든 사유 목록 (중복 제거, 정렬)
    
    Returns:
        사유 문자열 리스트 (빈 문자열 제외)
    """
    badmanner_list = load_badmanner_list()
    reasons: Set[str] = set()
    
    for entry in badmanner_list:
        reason = entry.get("reason", "").strip()
        if reason:
            reasons.add(reason)
    
    return sorted(list(reasons))


# =============================================================================
# 데이터 백업/복원 (Export/Import)
# =============================================================================
def export_all_data() -> str:
    """
    모든 데이터를 JSON 문자열로 내보내기
    
    Returns:
        JSON 문자열 (match_history + badmanner_list)
    """
    data = {
        "version": "2.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match_history": load_match_history(),
        "badmanner_list": load_badmanner_list()
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def import_all_data(json_str: str) -> Tuple[bool, str]:
    """
    JSON 문자열에서 모든 데이터 가져오기 (기존 데이터 덮어쓰기)
    
    Args:
        json_str: JSON 형식 문자열
        
    Returns:
        (성공 여부, 메시지)
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, f"JSON 파싱 오류: {str(e)}"
    
    # 데이터 검증
    if not isinstance(data, dict):
        return False, "올바른 백업 파일 형식이 아닙니다."
    
    match_history = data.get("match_history", [])
    badmanner_list = data.get("badmanner_list", [])
    
    if not isinstance(match_history, list) or not isinstance(badmanner_list, list):
        return False, "데이터 형식이 올바르지 않습니다."
    
    # 데이터 저장 (기존 데이터 덮어쓰기)
    save_match_history(match_history)
    save_badmanner_list(badmanner_list)
    
    match_count = len(match_history)
    badmanner_count = len(badmanner_list)
    
    return True, f"복원 완료: 매치 {match_count}건, 비매너 {badmanner_count}명"


def clear_all_data() -> bool:
    """모든 데이터 초기화"""
    save_match_history([])
    save_badmanner_list([])
    return True
