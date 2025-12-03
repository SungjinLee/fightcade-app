"""
크롤러 모듈 (Selenium Stealth)
- Selenium + Stealth 모드로 Cloudflare 우회
- 디버그 모드 지원
"""

import time
import json
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

from config import MAX_PAGES_TO_CRAWL, ROWS_PER_PAGE, API_BASE_URL


# =============================================================================
# 브라우저 설정 (Stealth 모드)
# =============================================================================

def _create_stealth_driver() -> webdriver.Chrome:
    """Selenium Stealth 드라이버 생성"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--lang=en-US,en")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 봇 탐지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                # Chromium (Linux/Cloud)
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception:
                # 일반 Chrome
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
    except Exception:
        # 시스템 크롬 직접 사용
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)
    
    # Stealth 모드 적용
    if STEALTH_AVAILABLE and driver:
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    
    # 추가 봇 탐지 우회
    if driver:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# =============================================================================
# API 호출 (Selenium으로 Cloudflare 통과 후)
# =============================================================================

def _call_api_via_selenium(driver: webdriver.Chrome, req_type: str, params: dict) -> Dict[str, Any]:
    """
    Selenium으로 페이지 방문 후 API 호출
    Cloudflare 쿠키를 얻은 상태에서 fetch로 API 호출
    """
    try:
        # API 요청 데이터
        api_data = {"req": req_type, **params}
        
        # JavaScript로 fetch 실행
        script = f"""
        return fetch('{API_BASE_URL}/', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
            }},
            body: JSON.stringify({json.dumps(api_data)})
        }})
        .then(response => response.json())
        .then(data => JSON.stringify(data))
        .catch(error => JSON.stringify({{error: error.toString()}}));
        """
        
        result = driver.execute_script(script)
        
        if result:
            return {"success": True, "data": json.loads(result)}
        else:
            return {"success": False, "error": "Empty response"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# 매치 데이터 파싱
# =============================================================================

def _parse_replay_to_match(replay: Dict, user_a: str, user_b: str) -> Optional[Dict[str, Any]]:
    """리플레이 데이터를 매치 데이터로 변환"""
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
        
        names_lower = {p1_name.lower(), p2_name.lower()}
        if user_a.lower() not in names_lower or user_b.lower() not in names_lower:
            return None
        
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
    """두 유저 간의 대전 기록 조회 (Selenium Stealth)"""
    
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
    
    driver = None
    
    try:
        log("🌐 Stealth 브라우저 시작 중...")
        result["debug"].append({"step": "init", "stealth_available": STEALTH_AVAILABLE})
        
        driver = _create_stealth_driver()
        driver.set_page_load_timeout(60)
        
        # 먼저 메인 페이지 방문 (Cloudflare 쿠키 획득)
        log("🔐 Cloudflare 인증 중...")
        driver.get("https://www.fightcade.com/")
        
        # Cloudflare 챌린지 대기 (최대 15초)
        time.sleep(5)
        
        # 페이지 로드 확인
        page_source = driver.page_source
        if "Just a moment" in page_source:
            log("⏳ Cloudflare 챌린지 처리 중... (최대 15초)")
            time.sleep(10)
            page_source = driver.page_source
        
        result["debug"].append({
            "step": "cloudflare_check",
            "passed": "Just a moment" not in page_source,
            "title": driver.title
        })
        
        if "Just a moment" in page_source:
            result["error"] = "Cloudflare 챌린지 통과 실패"
            return result
        
        log(f"✅ Cloudflare 통과! {user_a}의 데이터 조회 중...")
        
        # API 호출
        total_limit = max_pages * ROWS_PER_PAGE
        api_result = _call_api_via_selenium(driver, "searchquarks", {
            "username": user_a,
            "limit": total_limit,
            "offset": 0
        })
        
        result["debug"].append({
            "step": "api_call",
            "success": api_result.get("success"),
            "has_data": "data" in api_result
        })
        
        if not api_result["success"]:
            result["error"] = f"API 호출 실패: {api_result.get('error', 'Unknown')}"
            return result
        
        # 데이터 파싱
        data = api_result.get("data", {})
        
        # 디버그: 전체 응답 구조 확인
        result["debug"].append({
            "step": "api_response",
            "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
            "data_preview": str(data)[:1000]
        })
        
        replays = data.get("results", data.get("res", []))
        
        if isinstance(replays, dict):
            result["debug"].append({
                "step": "replays_is_dict",
                "replays_keys": list(replays.keys())
            })
            replays = replays.get("results", [])
        
        # 디버그: 첫 번째 리플레이 구조 확인
        if replays and len(replays) > 0:
            result["debug"].append({
                "step": "first_replay",
                "replay_keys": list(replays[0].keys()) if isinstance(replays[0], dict) else "not_dict",
                "replay_preview": str(replays[0])[:500]
            })
        
        log(f"📊 총 {len(replays)}개의 리플레이 발견")
        
        # 매치 필터링
        all_matches = []
        filter_debug = {"total_checked": 0, "no_players": 0, "not_matched": 0, "matched": 0, "sample_players": []}
        
        for replay in replays:
            filter_debug["total_checked"] += 1
            match = _parse_replay_to_match(replay, user_a, user_b)
            if match:
                all_matches.append(match)
                filter_debug["matched"] += 1
            else:
                # 왜 매치 안 됐는지 확인
                players = replay.get("players", [])
                if len(players) < 2:
                    filter_debug["no_players"] += 1
                else:
                    filter_debug["not_matched"] += 1
                    # 샘플로 몇 개 저장
                    if len(filter_debug["sample_players"]) < 3:
                        filter_debug["sample_players"].append({
                            "p1": players[0].get("name", "?") if players else "?",
                            "p2": players[1].get("name", "?") if len(players) > 1 else "?",
                            "raw": str(players)[:200]
                        })
        
        result["debug"].append({
            "step": "filter_result",
            "user_a": user_a,
            "user_b": user_b,
            "filter_stats": filter_debug
        })
        
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
        
        log(f"✅ 완료! {user_a}: {user_a_wins}승, {user_b}: {user_b_wins}승")
        
    except Exception as e:
        result["error"] = f"오류: {str(e)}"
        result["debug"].append({"step": "exception", "error": str(e)})
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return result


def check_user_exists_sync(user_id: str) -> bool:
    """유저 존재 여부 확인"""
    return True  # 간소화


# =============================================================================
# 테스트 함수
# =============================================================================

def test_api_connection() -> Dict[str, Any]:
    """API 연결 테스트 (Selenium Stealth)"""
    results = {
        "stealth_available": STEALTH_AVAILABLE,
        "webdriver_manager": WEBDRIVER_MANAGER_AVAILABLE
    }
    
    driver = None
    try:
        driver = _create_stealth_driver()
        driver.set_page_load_timeout(30)
        
        # 메인 사이트 테스트
        driver.get("https://www.fightcade.com/")
        time.sleep(5)
        
        page_source = driver.page_source
        results["main_site"] = {
            "title": driver.title,
            "cloudflare_challenge": "Just a moment" in page_source,
            "passed": "Just a moment" not in page_source
        }
        
        if "Just a moment" not in page_source:
            # API 테스트
            api_result = _call_api_via_selenium(driver, "getuser", {"username": "test"})
            results["api"] = {
                "success": api_result.get("success"),
                "has_data": "data" in api_result
            }
        
    except Exception as e:
        results["error"] = str(e)
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return results
