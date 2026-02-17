from playwright.sync_api import sync_playwright
import json

def login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 로그인 페이지로 이동
        page.goto("https://myalan.ai")
        page.click("button:has-text('로그인')")
        page.click("button:has-text('아이디 로그인')")
        page.fill("input[placeholder*='아이디']", "") # 입력
        page.fill("input[placeholder*='비밀번호']", "") # 입력
        page.click("button:has-text('로그인')")
        
        # 로그인 완료 대기 (더 명확한 조건으로)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)  # 추가 대기
        
        # 특정 도메인의 쿠키 가져오기
        all_cookies = context.cookies()
        
        # api.myalan.ai 도메인의 쿠키만 필터링
        api_cookies = [c for c in all_cookies if 'myalan.ai' in c.get('domain', '')]
        
        print("\n=== 전체 쿠키 목록 ===")
        for c in all_cookies:
            print(f"Name: {c['name']}, Domain: {c.get('domain', 'N/A')}")
        
        print("\n=== API 도메인 쿠키 ===")
        for c in api_cookies:
            print(f"Name: {c['name']}, Domain: {c.get('domain', 'N/A')}, Value: {c['value'][:20]}...")
        
        # alan_session_id 찾기
        session_cookie = next((c for c in all_cookies if c['name'] == 'alan_session_id'), None)
        
        if session_cookie:
            print(f"\nalan_session_id 찾음!")
            print(f"Domain: {session_cookie.get('domain')}")
            print(f"Value: {session_cookie['value']}")
        else:
            print("\nalan_session_id를 찾을 수 없습니다.")
            print("\n다른 방법 시도: API 직접 호출")
            
            # 방법 2: API를 직접 호출해서 쿠키 생성 유도
            response = page.goto("https://api.myalan.ai/api/v2/users/me")
            print(f"API 응답 상태: {response.status}")
            
            page.wait_for_timeout(2000)
            
            # 쿠키 다시 확인
            all_cookies = context.cookies()
            session_cookie = next((c for c in all_cookies if c['name'] == 'alan_session_id'), None)
            
            if session_cookie:
                print(f"\nAPI 호출 후 alan_session_id 찾음!")
                print(f"Value: {session_cookie['value']}")
        
        # 쿠키 저장
        with open("cookies.json", "w") as f:
            json.dump(all_cookies, f, indent=2)
        
        print("\n쿠키 저장 완료: cookies.json")
        
        browser.close()

if __name__ == "__main__":
    login_and_save_cookies()