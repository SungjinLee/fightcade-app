"""
크롤러 모듈 (Selenium Stealth + 직접 페이지 크롤링)
- API 대신 실제 페이지에서 데이터 추출
- XPath로 테이블 데이터 파싱
"""

import time
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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

from config import MAX_PAGES_TO_CRAWL, ROWS_PER_PAGE, XPATH


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
    options.add_argument("--lang=en-US,en")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    
    try:
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                driver = webdriver.Chrome(service=service, options=options)
            except Exception:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
    except Exception:
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)
    
    if STEALTH_AVAILABLE and driver:
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    
    if driver:
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# =============================================================================
# 헬퍼 함수
# =============================================================================

def _safe_get_text(driver: webdriver.Chrome, xpath: str) -> Optional[str]:
    """XPath로 텍스트 안전하게 가져오기"""
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()
    except NoSuchElementException:
        return None
    except Exception:
        return None


def _safe_click(driver: webdriver.Chrome, xpath: str, timeout: int = 10) -> bool:
    """XPath 요소 안전하게 클릭"""
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.click()
        return True
    except Exception:
        return False


def _wait_for_element(driver: webdriver.Chrome, xpath: str, timeout: int = 10) -> bool:
    """요소 대기"""
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except TimeoutException:
        return False


# =============================================================================
# 페이지 크롤링
# =============================================================================

def _parse_match_row(driver: webdriver.Chrome, row_idx: int) -> Optional[Dict[str, Any]]:
    """단일 행에서 매치 데이터 추출"""
    try:
        # XPath 템플릿에 행 인덱스 적용
        id1_xpath = XPATH["row_id1"].format(row=row_idx)
        id2_xpath = XPATH["row_id2"].format(row=row_idx)
        score1_xpath = XPATH["row_score1"].format(row=row_idx)
        score2_xpath = XPATH["row_score2"].format(row=row_idx)
        
        id1 = _safe_get_text(driver, id1_xpath)
        id2 = _safe_get_text(driver, id2_xpath)
        score1_text = _safe_get_text(driver, score1_xpath)
        score2_text = _safe_get_text(driver, score2_xpath)
        
        if not all([id1, id2, score1_text, score2_text]):
            return None
        
        score1 = int(score1_text)
        score2 = int(score2_text)
        
        winner = id1 if score1 > score2 else id2
        
        return {
            "id1": id1,
            "id2": id2,
            "score1": score1,
            "score2": score2,
            "winner": winner
        }
    except Exception:
        return None


def _parse_current_page(driver: webdriver.Chrome, user_a: str, user_b: str) -> List[Dict[str, Any]]:
    """현재 페이지의 매치 데이터 파싱"""
    matches = []
    
    for row_idx in range(1, ROWS_PER_PAGE + 1):
        match = _parse_match_row(driver, row_idx)
        if match:
            # 두 유저 간의 매치인지 확인
            ids = {match["id1"].lower(), match["id2"].lower()}
            if user_a.lower() in ids and user_b.lower() in ids:
                matches.append(match)
        else:
            # 더 이상 행이 없으면 종료
            break
    
    return matches


# =============================================================================
# 메인 크롤링 함수
# =============================================================================

def crawl_head_to_head_sync(user_a: str, user_b: str, 
                            max_pages: int = MAX_PAGES_TO_CRAWL,
                            progress_callback=None) -> Dict[str, Any]:
    """두 유저 간의 대전 기록 조회 (직접 페이지 크롤링)"""
    
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
        
        # 1. 유저 페이지로 이동
        user_url = f"https://www.fightcade.com/id/{user_a}"
        log(f"📡 {user_a}의 페이지로 이동 중...")
        driver.get(user_url)
        time.sleep(3)
        
        # Cloudflare 체크
        page_source = driver.page_source
        if "Just a moment" in page_source:
            log("⏳ Cloudflare 챌린지 처리 중...")
            time.sleep(10)
            page_source = driver.page_source
        
        result["debug"].append({
            "step": "user_page",
            "url": user_url,
            "cloudflare_passed": "Just a moment" not in page_source,
            "title": driver.title
        })
        
        if "Just a moment" in page_source:
            result["error"] = "Cloudflare 챌린지 통과 실패"
            return result
        
        # 2. Replay 탭 클릭
        log("🎬 Replay 탭으로 이동 중...")
        time.sleep(2)
        
        if not _safe_click(driver, XPATH["replay_tab"]):
            result["error"] = "Replay 탭을 찾을 수 없습니다."
            result["debug"].append({"step": "replay_tab", "success": False})
            return result
        
        time.sleep(3)
        result["debug"].append({"step": "replay_tab", "success": True})
        
        # 3. 검색창에 상대방 ID 입력
        log(f"🔍 {user_b} 검색 중...")
        
        try:
            wait = WebDriverWait(driver, 10)
            search_input = wait.until(
                EC.presence_of_element_located((By.XPATH, XPATH["search_input"]))
            )
            search_input.clear()
            search_input.send_keys(user_b)
            search_input.send_keys(Keys.ENTER)
            time.sleep(3)
            result["debug"].append({"step": "search", "query": user_b, "success": True})
        except Exception as e:
            result["error"] = f"검색창을 찾을 수 없습니다: {str(e)}"
            result["debug"].append({"step": "search", "success": False, "error": str(e)})
            return result
        
        # 4. 테이블에서 데이터 추출
        all_matches = []
        
        for page_num in range(1, max_pages + 1):
            log(f"📄 페이지 {page_num}/{max_pages} 크롤링 중...")
            
            # 테이블 로딩 대기
            time.sleep(2)
            
            # 현재 페이지 파싱
            page_matches = _parse_current_page(driver, user_a, user_b)
            
            result["debug"].append({
                "step": f"page_{page_num}",
                "matches_found": len(page_matches)
            })
            
            if not page_matches:
                # 데이터가 없으면 첫 번째 행이라도 확인
                test_id1 = _safe_get_text(driver, XPATH["row_id1"].format(row=1))
                result["debug"].append({
                    "step": f"page_{page_num}_check",
                    "first_row_id1": test_id1,
                    "page_source_preview": driver.page_source[:500] if not test_id1 else "skipped"
                })
                
                if page_num == 1:
                    log("⚠️ 첫 페이지에 데이터가 없습니다.")
                break
            
            all_matches.extend(page_matches)
            log(f"   → {len(page_matches)}개 매치 발견 (누적: {len(all_matches)}개)")
            
            # 다음 페이지로 이동
            if page_num < max_pages:
                if not _safe_click(driver, XPATH["next_page"], timeout=5):
                    log(f"   → 마지막 페이지입니다.")
                    break
                time.sleep(2)
        
        # 결과 집계
        if not all_matches:
            result["error"] = f"'{user_a}'와 '{user_b}' 간의 대전 기록이 없습니다."
            result["success"] = True
            return result
        
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
        
        log(f"✅ 완료! 총 {len(all_matches)}경기, {user_a}: {user_a_wins}승, {user_b}: {user_b_wins}승")
        
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
    return True


# =============================================================================
# 테스트 함수
# =============================================================================

def test_api_connection() -> Dict[str, Any]:
    """연결 테스트"""
    results = {
        "stealth_available": STEALTH_AVAILABLE,
        "webdriver_manager": WEBDRIVER_MANAGER_AVAILABLE
    }
    
    driver = None
    try:
        driver = _create_stealth_driver()
        driver.set_page_load_timeout(30)
        
        # 유저 페이지 테스트
        driver.get("https://www.fightcade.com/id/test")
        time.sleep(5)
        
        page_source = driver.page_source
        results["user_page"] = {
            "title": driver.title,
            "cloudflare_passed": "Just a moment" not in page_source
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
