"""
세션 및 쿠키 관리 모듈
"""
import requests
import json
import os


class SessionManager:
    """쿠키 기반 세션 관리 클래스"""
    
    def __init__(self, cookie_file="cookies.json"):
        # 여러 경로에서 쿠키 파일 찾기
        possible_paths = [
            cookie_file,                    # 현재 폴더
            f"../{cookie_file}",           # 상위 폴더
            f"../../{cookie_file}"         # 상위의 상위 폴더
        ]
        
        self.cookie_file = None
        for path in possible_paths:
            if os.path.exists(path):
                self.cookie_file = path
                break
        
        if not self.cookie_file:
            self.cookie_file = cookie_file  # 기본값 유지 (에러 메시지용)
        
        self.session = None
        self.user_id = None
    
    def load_session(self):
        """쿠키를 로드하여 세션 생성"""
        if not os.path.exists(self.cookie_file):
            raise FileNotFoundError(
                f"❌ {self.cookie_file} 파일이 없습니다. "
                "login_and_save_session.py를 먼저 실행하세요."
            )
        
        self.session = requests.Session()
        
        with open(self.cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        for cookie in cookies:
            self.session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path"),
            )
        
        return self.session
    
    def check_login(self, base_api_v2):
        """로그인 확인 및 user_id 획득"""
        if not self.session:
            raise ValueError("세션이 초기화되지 않았습니다. load_session()을 먼저 호출하세요.")
        
        res = self.session.get(f"{base_api_v2}/users/me")
        
        if res.status_code != 200:
            return False, None
        
        try:
            data = res.json()
            self.user_id = data.get("_id")
            user_name = data.get("name", "Unknown")
            return True, user_name
        except:
            return False, None
    
    def get_user_id(self):
        """현재 user_id 반환"""
        return self.user_id
