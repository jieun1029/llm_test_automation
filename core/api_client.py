"""
MyAlan API 클라이언트 모듈 (재시도 로직 포함)
"""
import time


class APIClient:
    """MyAlan API 통신 클래스"""
    
    def __init__(self, session, base_api_v1, base_api_v2, persona_id, user_id):
        self.session = session
        self.base_api_v1 = base_api_v1
        self.base_api_v2 = base_api_v2
        self.persona_id = persona_id
        self.user_id = user_id
    
    def create_channel(self):
        """새 채널(대화방) 생성"""
        payload = {
            "persona_id": self.persona_id,
            "options": {
                "xllm_enabled": False
            }
        }
        
        res = self.session.post(
            f"{self.base_api_v1}/channels",
            json=payload
        )
        
        if res.status_code != 200:
            return None
        
        try:
            data = res.json()
            channel_id = data.get("inserted_id") or data.get("_id") or data.get("id")
            return channel_id
        except:
            return None
    
    def send_message(self, channel_id, message):
        """메시지 전송"""
        payload = {
            "channel_id": channel_id,
            "content": message,
            "user_id": self.user_id,
            "persona_id": self.persona_id,
            "options": {
                "file_ids": []
            }
        }
        
        res = self.session.post(
            f"{self.base_api_v1}/channels/{channel_id}/messages",
            json=payload
        )
        
        if res.status_code not in [200, 201]:
            return None
        
        try:
            return res.json()
        except:
            return None
    
    def get_messages(self, channel_id):
        """메시지 목록 조회"""
        res = self.session.get(f"{self.base_api_v1}/channels/{channel_id}/messages")
        
        try:
            return res.json()
        except:
            return None
    
    def wait_for_response(self, channel_id, timeout=120):
        """AI 답변 대기 (스트리밍)"""
        start = time.time()
        
        while time.time() - start < timeout:
            messages = self.get_messages(channel_id)
            
            if messages and isinstance(messages, dict):
                msg_list = messages.get("messages", [])
                
                for msg in reversed(msg_list):
                    user_role = msg.get("userRole")
                    
                    if user_role == "assistant":
                        content = msg.get("content", "")
                        stop_reason = msg.get("stop_reason")
                        
                        if stop_reason is not None:
                            return content
            
            time.sleep(2)
        
        return None
    
    def execute_test(self, question, max_retries=3):
        """
        단일 테스트 실행: 채널 생성 → 질문 전송 → 답변 대기
        재시도 로직 포함 (Rate Limit 대응)
        
        Args:
            question (str): 질문
            max_retries (int): 최대 재시도 횟수
        
        Returns:
            tuple: (success: bool, answer: str or None, error_message: str or None)
        """
        for attempt in range(max_retries):
            try:
                # 채널 생성
                channel_id = self.create_channel()
                if not channel_id:
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)
                        print(f"⚠️ 채널 생성 실패, {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return False, None, "채널 생성 실패 (최대 재시도 초과)"
                
                # 질문 전송
                result = self.send_message(channel_id, question)
                if not result:
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)
                        print(f"⚠️ 메시지 전송 실패, {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return False, None, "메시지 전송 실패 (최대 재시도 초과)"
                
                # 답변 대기
                answer = self.wait_for_response(channel_id)
                if not answer:
                    if attempt < max_retries - 1:
                        wait_time = 5 * (attempt + 1)
                        print(f"⚠️ 답변 시간 초과, {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    return False, None, "답변 시간 초과 (최대 재시도 초과)"
                
                return True, answer, None
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    print(f"⚠️ 예외 발생: {str(e)}, {wait_time}초 후 재시도... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                return False, None, f"예외 발생: {str(e)} (최대 재시도 초과)"
        
        return False, None, "최대 재시도 횟수 초과"
