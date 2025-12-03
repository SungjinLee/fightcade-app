"""
크롤러 모듈 (API 방식 + Cloudflare 우회)
- Fightcade 공식 API 사용
- cloudscraper로 Cloudflare 챌린지 우회
- 디버그 모드 지원
"""

import cloudscraper
from typing import List, Dict, Any, Optional
from config import MAX_PAGES_TO_CRAWL, ROWS_PER_PAGE


# =============================================================================
# API 설정
# =============================================================================
API_BASE_URL = "https://www.fightcade.com/api"


# =============================================================================
# Scraper 생성
# =============================================================================

def _create_scraper():
    """Cloudflare 우회 스크래퍼 생성"""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    return scraper


# =============================================================================
# API 호출 함수
# =============================================================================

def _api_request(endpoint: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
    """
    API 요청 수행 (Cloudflare 우회)
    
    Returns:
        {"success": bool, "data": Any, "error": str, "debug": dict}
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        scraper = _create_scraper()
        
        if method == "GET":
            response = scraper.get(url, timeout=30)
        else:
            response = scraper.post(url, json=data, timeout=30)
        
        # 디버그 정보
        debug_info = {
            "url": url,
            "status_code": response.status_code,
            "content_preview": response.text[:500] if response.text else "",
            "method": method
        }
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                return {"success": True, "data": json_data, "debug": debug_info}
            except Exception as e:
                return {
                    "success": False, 
                    "error": f"JSON 파싱 오류: {str(e)}", 
                    "data": response.text,
                    "debug": debug_info
                }
        elif response.status_code == 403:
            return {
                "success": False, 
                "error": "Cloudflare 차단됨 (403). cloudscraper로도 우회 실패.",
                "debug": debug_info
            }
        elif response.status_code == 503:
            return {
                "success": False,
                "error": "서버 점검 중 (503)",
                "debug": debug_info
            }
        else:
            return {
                "success": False, 
                "error": f"API 오류: HTTP {response.status_code}",
                "debug": debug_info
            }
            
    except cloudscraper.exceptions.CloudflareChallengeError as e:
        return {
            "success": False, 
            "error": f"Cloudflare 챌린지 실패: {str(e)}",
            "debug": {"url": url, "exception": "CloudflareChallengeError"}
        }
    except Exception as e:
        return {
            "success": False, 
            "error": f"요청 오류: {str(e)}",
            "debug": {"url": url, "exception": type(e).__name__}
        }


def get_user_replays(username: str, limit: int = 75, offset: int = 0) -> Dict[str, Any]:
    """
    유저의 리플레이 목록 조회
    
    API: POST /api/
    Body: {"req": "searchquarks", "username": "...", "limit": 75, "offset": 0}
    """
    data = {
        "req": "searchquarks",
        "username": username,
        "limit": limit,
        "offset": offset
    }
    return _api_request("", method="POST", data=data)


def get_user_info(username: str) -> Dict[str, Any]:
    """
    유저 정보 조회
    
    API: POST /api/
    Body: {"req": "getuser", "username": "..."}
    """
    data = {
        "req": "getuser",
        "username": username
    }
    return _api_request("", method="POST", data=data)


# =============================================================================
# 매치 데이터 파싱
# =============================================================================

def _parse_replay_to_match(replay: Dict, user_a: str, user_b: str) -> Optional[Dict[str, Any]]:
    """
    리플레이 데이터를 매치 데이터로 변환
    """
    try:
        players = replay.get("players", [])
        if len(players) < 2:
            return None
        
        p1 = players[0]
        p2 = players[1]
        
        p1_name = p1.get("name", "").strip()
        p2_name = p2.get("name", "").strip()
        p1_score = int(p1.get("score", 0))
        p2_score = int(p2.get("score", 0))
        
        # user_a와 user_b가 모두 포함된 매치만 필터링
        names_lower = {p1_name.lower(), p2_name.lower()}
        if user_a.lower() not in names_lower or user_b.lower() not in names_lower:
            return None
        
        # 승자 판정
        winner = p1_name if p1_score > p2_score else p2_name
        
        return {
            "id1": p1_name,
            "id2": p2_name,
            "score1": p1_score,
            "score2": p2_score,
            "winner": winner,
            "game": replay.get("channelname", "unknown")
        }
    except Exception:
        return None


# =============================================================================
# 메인 크롤링 함수
# =============================================================================

def crawl_head_to_head_sync(user_a: str, user_b: str, 
                            max_pages: int = MAX_PAGES_TO_CRAWL,
                            progress_callback=None) -> Dict[str, Any]:
    """
    두 유저 간의 대전 기록 조회 (API 방식)
    """
    result = {
        "success": False,
        "matches": [],
        "summary": {
            "total_matches": 0,
            "user_a_wins": 0,
            "user_b_wins": 0,
            "user_a_id": user_a,
            "user_b_id": user_b
        },
        "error": None,
        "debug": []
    }
    
    def log(msg):
        if progress_callback:
            progress_callback(msg)
        print(msg)
    
    total_limit = max_pages * ROWS_PER_PAGE
    
    log(f"📡 {user_a}의 리플레이 데이터 조회 중... (cloudscraper 사용)")
    
    # API 호출
    api_result = get_user_replays(user_a, limit=total_limit, offset=0)
    
    # 디버그 정보 저장
    result["debug"].append({
        "step": "get_user_replays",
        "user": user_a,
        "result": api_result.get("debug", {})
    })
    
    if not api_result["success"]:
        result["error"] = api_result["error"]
        log(f"❌ API 오류: {api_result['error']}")
        return result
    
    # 리플레이 데이터 파싱
    replays_data = api_result.get("data", {})
    
    # 응답 구조 확인
    if isinstance(replays_data, dict):
        replays = replays_data.get("results", replays_data.get("replays", replays_data.get("res", [])))
        if not replays and "qupiresults" in str(replays_data):
            replays = replays_data.get("results", {}).get("results", [])
    elif isinstance(replays_data, list):
        replays = replays_data
    else:
        result["error"] = f"예상치 못한 응답 형식: {type(replays_data)}"
        result["debug"].append({"response_type": str(type(replays_data)), "preview": str(replays_data)[:500]})
        return result
    
    log(f"📊 총 {len(replays)}개의 리플레이 발견")
    
    # user_b와의 매치만 필터링
    all_matches = []
    for replay in replays:
        match = _parse_replay_to_match(replay, user_a, user_b)
        if match:
            all_matches.append(match)
    
    log(f"🎮 {user_b}와의 매치: {len(all_matches)}개")
    
    if not all_matches:
        result["error"] = f"'{user_a}'와 '{user_b}' 간의 대전 기록이 없습니다."
        result["success"] = True
        return result
    
    # 결과 집계
    user_a_wins = sum(1 for m in all_matches if m["winner"].lower() == user_a.lower())
    user_b_wins = sum(1 for m in all_matches if m["winner"].lower() == user_b.lower())
    
    result["success"] = True
    result["matches"] = all_matches
    result["summary"] = {
        "total_matches": len(all_matches),
        "user_a_wins": user_a_wins,
        "user_b_wins": user_b_wins,
        "user_a_id": user_a,
        "user_b_id": user_b
    }
    
    log(f"✅ 완료! 총 {len(all_matches)}경기")
    
    return result


def check_user_exists_sync(user_id: str) -> bool:
    """유저 존재 여부 확인"""
    result = get_user_info(user_id)
    return result.get("success", False)


# =============================================================================
# 테스트 함수
# =============================================================================

def test_api_connection() -> Dict[str, Any]:
    """API 연결 테스트"""
    results = {}
    
    try:
        scraper = _create_scraper()
        
        # 테스트 1: 메인 사이트
        response = scraper.get("https://www.fightcade.com/", timeout=10)
        results["main_site"] = {
            "status": response.status_code,
            "ok": response.status_code == 200
        }
        
        # 테스트 2: API
        response = scraper.post(
            f"{API_BASE_URL}/",
            json={"req": "getuser", "username": "test"},
            timeout=10
        )
        results["api"] = {
            "status": response.status_code,
            "response_preview": response.text[:300],
            "ok": response.status_code == 200
        }
        
    except Exception as e:
        results["error"] = str(e)
    
    return results
