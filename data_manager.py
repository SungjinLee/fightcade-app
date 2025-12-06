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
PLAYER_RATINGS_FILE = f"{DATA_DIR}/player_ratings.json"

# =============================================================================
# 랭킹 설정
# =============================================================================
DEFAULT_RATING = 1200       # 초기 레이팅
DEFAULT_RD = 350            # 초기 Rating Deviation (신뢰도)
K_FACTOR = 32               # Elo K값
MIN_GAMES_FOR_RANKING = 9   # 랭킹 반영 최소 판수


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


# =============================================================================
# 일일 방문수 카운터
# =============================================================================
VISIT_COUNT_FILE = f"{DATA_DIR}/visit_count.json"


def get_today_str() -> str:
    """오늘 날짜 문자열 반환 (YYYY-MM-DD)"""
    return datetime.now().strftime("%Y-%m-%d")


def load_visit_count() -> Dict[str, Any]:
    """방문수 데이터 로드"""
    data = _load_json(VISIT_COUNT_FILE)
    if data is None or not isinstance(data, dict):
        return {"date": get_today_str(), "count": 0}
    return data


def save_visit_count(data: Dict[str, Any]) -> bool:
    """방문수 데이터 저장"""
    return _save_json(VISIT_COUNT_FILE, data)


def increment_visit_count() -> int:
    """
    방문수 증가 및 반환
    날짜가 바뀌면 리셋
    
    Returns:
        오늘의 방문수
    """
    data = load_visit_count()
    today = get_today_str()
    
    if data.get("date") != today:
        # 날짜가 바뀌면 리셋
        data = {"date": today, "count": 1}
    else:
        data["count"] = data.get("count", 0) + 1
    
    save_visit_count(data)
    return data["count"]


def get_visit_count() -> int:
    """
    현재 방문수 반환 (증가 없이)
    
    Returns:
        오늘의 방문수
    """
    data = load_visit_count()
    today = get_today_str()
    
    if data.get("date") != today:
        return 0
    
    return data.get("count", 0)


# =============================================================================
# 플레이어 Rating 관리
# =============================================================================
def load_player_ratings() -> Dict[str, Dict[str, Any]]:
    """플레이어 Rating 데이터 로드"""
    data = _load_json(PLAYER_RATINGS_FILE)
    if data is None or not isinstance(data, dict):
        return {}
    return data


def save_player_ratings(ratings: Dict[str, Dict[str, Any]]) -> bool:
    """플레이어 Rating 데이터 저장"""
    return _save_json(PLAYER_RATINGS_FILE, ratings)


def get_player_rating(player_id: str) -> Dict[str, Any]:
    """
    특정 플레이어의 Rating 정보 조회
    없으면 기본값 반환
    """
    ratings = load_player_ratings()
    player_lower = player_id.lower()
    
    if player_lower in ratings:
        return ratings[player_lower]
    
    return {
        "rating": DEFAULT_RATING,
        "rd": DEFAULT_RD,
        "games": 0,
        "last_played": None
    }


def _calculate_expected_win_rate(my_rating: float, opp_rating: float) -> float:
    """기대 승률 계산 (Elo 공식)"""
    return 1 / (1 + 10 ** ((opp_rating - my_rating) / 400))


def _calculate_margin_multiplier(winner_score: int, loser_score: int) -> float:
    """
    마진 가중치 계산
    - 3:0 완승 → 1.5
    - 3:1 → 1.25
    - 3:2 신승 → 1.0
    - 2:0 → 1.3
    - 2:1 → 1.1
    - 기타 → 1.0
    """
    diff = winner_score - loser_score
    total = winner_score + loser_score
    
    if total == 0:
        return 1.0
    
    # 스코어 차이에 따른 가중치
    if diff >= 3:
        return 1.5
    elif diff == 2:
        return 1.3 if winner_score >= 3 else 1.25
    elif diff == 1:
        return 1.1 if winner_score <= 2 else 1.0
    else:
        return 1.0


def update_ratings_from_match(
    player1: str, 
    score1: int, 
    player2: str, 
    score2: int
) -> Tuple[float, float]:
    """
    매치 결과로 양쪽 플레이어 Rating 업데이트
    
    Returns:
        (player1 변동량, player2 변동량)
    """
    ratings = load_player_ratings()
    p1_lower = player1.lower()
    p2_lower = player2.lower()
    
    # 기존 Rating 조회 (없으면 기본값)
    p1_data = ratings.get(p1_lower, {
        "rating": DEFAULT_RATING,
        "rd": DEFAULT_RD,
        "games": 0
    })
    p2_data = ratings.get(p2_lower, {
        "rating": DEFAULT_RATING,
        "rd": DEFAULT_RD,
        "games": 0
    })
    
    r1 = p1_data.get("rating", DEFAULT_RATING)
    r2 = p2_data.get("rating", DEFAULT_RATING)
    
    # 기대 승률
    exp1 = _calculate_expected_win_rate(r1, r2)
    exp2 = _calculate_expected_win_rate(r2, r1)
    
    # 실제 결과 (승리=1, 패배=0, 무승부=0.5)
    if score1 > score2:
        actual1, actual2 = 1, 0
        margin = _calculate_margin_multiplier(score1, score2)
    elif score2 > score1:
        actual1, actual2 = 0, 1
        margin = _calculate_margin_multiplier(score2, score1)
    else:
        actual1, actual2 = 0.5, 0.5
        margin = 1.0
    
    # Rating 변동 계산
    delta1 = K_FACTOR * (actual1 - exp1) * margin
    delta2 = K_FACTOR * (actual2 - exp2) * margin
    
    # 새 Rating 적용
    new_r1 = r1 + delta1
    new_r2 = r2 + delta2
    
    # RD 감소 (게임할수록 신뢰도 증가 = RD 감소)
    new_rd1 = max(50, p1_data.get("rd", DEFAULT_RD) * 0.95)
    new_rd2 = max(50, p2_data.get("rd", DEFAULT_RD) * 0.95)
    
    # 저장
    today = get_today_str()
    ratings[p1_lower] = {
        "rating": round(new_r1, 1),
        "rd": round(new_rd1, 1),
        "games": p1_data.get("games", 0) + 1,
        "last_played": today
    }
    ratings[p2_lower] = {
        "rating": round(new_r2, 1),
        "rd": round(new_rd2, 1),
        "games": p2_data.get("games", 0) + 1,
        "last_played": today
    }
    
    save_player_ratings(ratings)
    
    return round(delta1, 1), round(delta2, 1)


def recalculate_all_ratings() -> int:
    """
    모든 매치 히스토리를 기반으로 Rating 재계산
    (데이터 마이그레이션 또는 리셋 시 사용)
    
    Returns:
        처리된 매치 수
    """
    # Rating 초기화
    save_player_ratings({})
    
    # 매치 히스토리 로드
    history = load_match_history()
    
    if not history:
        return 0
    
    # 날짜순 정렬 (오래된 것부터)
    sorted_history = sorted(history, key=lambda x: x.get("date", ""))
    
    # 각 매치마다 Rating 업데이트
    for match in sorted_history:
        player1 = match.get("player1", "")
        player2 = match.get("player2", "")
        score1 = match.get("score1", 0)
        score2 = match.get("score2", 0)
        
        if player1 and player2:
            update_ratings_from_match(player1, score1, player2, score2)
    
    return len(sorted_history)


def get_all_player_ratings() -> List[Dict[str, Any]]:
    """
    모든 플레이어의 Rating 정보를 랭킹 순으로 반환
    (최소 판수 미달은 제외)
    
    Returns:
        [{"user_id": str, "rating": float, "rd": float, "games": int, ...}, ...]
    """
    ratings = load_player_ratings()
    total_stats = get_player_total_stats()
    
    result = []
    for player_id, data in ratings.items():
        games = data.get("games", 0)
        
        # 최소 판수 체크
        if games < MIN_GAMES_FOR_RANKING:
            continue
        
        stats = total_stats.get(player_id, {"wins": 0, "losses": 0, "games": 0})
        win_rate = 0.0
        if stats["wins"] + stats["losses"] > 0:
            win_rate = (stats["wins"] / (stats["wins"] + stats["losses"])) * 100
        
        result.append({
            "user_id": player_id,
            "rating": data.get("rating", DEFAULT_RATING),
            "rd": data.get("rd", DEFAULT_RD),
            "games": games,
            "wins": stats["wins"],
            "losses": stats["losses"],
            "win_rate": round(win_rate, 1),
            "last_played": data.get("last_played")
        })
    
    # Rating 순 정렬 (내림차순)
    result.sort(key=lambda x: (-x["rating"], -x["win_rate"], -x["games"]))
    
    return result
