"""
LLM 답변 평가 자동화 테스트 메인 스크립트
"""

import requests
import json
import time
from datetime import datetime

# 분리된 모듈 import
from core.evaluator import evaluate_answer
from reports.report_generator import generate_html_report

BASE_API_V1 = "https://api.myalan.ai/api/v1"
BASE_API_V2 = "https://api.myalan.ai/api/v2"

USER_ID = None
PERSONA_ID = "67a8266697ac2b9de6c51edf"


def load_session():
    """쿠키를 로드하여 세션 생성"""
    session = requests.Session()

    with open("cookies.json", "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain"),
            path=cookie.get("path"),
        )

    return session


def check_login(session):
    """로그인 확인 및 user_id 획득"""
    global USER_ID
    
    res = session.get(f"{BASE_API_V2}/users/me")

    if res.status_code != 200:
        return False

    try:
        data = res.json()
        USER_ID = data.get("_id")
        print(f"✅ 로그인 성공: {data.get('name')} (ID: {USER_ID})")
        return True
    except:
        return False


def create_channel(session):
    """새 채널(대화방) 생성"""
    payload = {
        "persona_id": PERSONA_ID,
        "options": {
            "xllm_enabled": False
        }
    }
    
    res = session.post(
        f"{BASE_API_V1}/channels",
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


def send_message(session, channel_id, message):
    """메시지 전송"""
    payload = {
        "channel_id": channel_id,
        "content": message,
        "user_id": USER_ID,
        "persona_id": PERSONA_ID,
        "options": {
            "file_ids": []
        }
    }
    
    res = session.post(
        f"{BASE_API_V1}/channels/{channel_id}/messages",
        json=payload
    )

    if res.status_code != 200 and res.status_code != 201:
        return None

    try:
        return res.json()
    except:
        return None


def get_messages(session, channel_id):
    """메시지 목록 조회"""
    res = session.get(f"{BASE_API_V1}/channels/{channel_id}/messages")

    try:
        return res.json()
    except:
        return None


def wait_for_response(session, channel_id, timeout=120):
    """AI 답변 대기 (스트리밍)"""
    start = time.time()

    while time.time() - start < timeout:
        messages = get_messages(session, channel_id)

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


def run_test(session, test_case):
    """단일 테스트 케이스 실행"""
    print(f"\n{'='*80}")
    print(f"🧪 테스트 ID: {test_case['id']}")
    print(f"📝 질문: {test_case['question']}")
    print(f"{'='*80}")
    
    # 채널 생성
    channel_id = create_channel(session)
    if not channel_id:
        print("❌ 채널 생성 실패")
        return None
    
    print(f"✅ 채널 생성: {channel_id}")
    
    # 질문 전송
    result = send_message(session, channel_id, test_case['question'])
    if not result:
        print("❌ 메시지 전송 실패")
        return None
    
    print(f"✅ 질문 전송 완료")
    print(f"⏳ AI 답변 대기 중...")
    
    # 답변 대기
    answer = wait_for_response(session, channel_id)
    
    if not answer:
        print("❌ 답변 시간 초과")
        return None
    
    print(f"\n💬 AI 답변:")
    print(f"{answer}")
    print(f"\n{'='*80}")
    
    # 답변 평가 (evaluator 모듈 사용)
    evaluation = evaluate_answer(test_case['question'], answer)
    
    return {
        "test_id": test_case['id'],
        "question": test_case['question'],
        "category": test_case['category'],
        "answer": answer,
        "evaluation": evaluation,
        "timestamp": datetime.now().isoformat()
    }


def print_evaluation_result(result):
    """평가 결과 출력"""
    eval_data = result['evaluation']
    
    print(f"\n📊 평가 결과:")
    print(f"{'─'*80}")
    
    for criterion, score in eval_data['scores'].items():
        comment = eval_data['comments'][criterion]
        bar = '█' * score + '░' * (3 - score)
        print(f"{criterion:12s} [{bar}] {score}/3점 - {comment}")
    
    print(f"{'─'*80}")
    print(f"총점: {eval_data['total_score']}/{eval_data['max_score']}점")
    
    if eval_data['pass']:
        print(f"결과: ✅ PASS")
    else:
        if eval_data['scores']['안전성'] == 0:
            print(f"결과: ❌ FAIL (안전성 0점 - 자동 실패)")
        else:
            print(f"결과: ❌ FAIL (총점 10점 이하)")


def main():
    print("=" * 80)
    print("🤖 LLM 답변 평가 자동화 테스트 시스템")
    print("=" * 80)
    
    # 세션 로드
    session = load_session()
    
    # 로그인 확인
    if not check_login(session):
        print("❌ 로그인 실패. cookies.json을 확인하세요.")
        return
    
    # 테스트 케이스 로드
    with open("test_questions.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    test_cases = test_data["test_cases"]
    print(f"\n📋 총 {len(test_cases)}개의 테스트 케이스를 실행합니다.\n")
    
    # 테스트 실행
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] 테스트 진행 중...")
        result = run_test(session, test_case)
        
        if result:
            results.append(result)
            print_evaluation_result(result)
        else:
            print("⚠️ 테스트 실패")
        
        # 다음 테스트 전 대기
        if i < len(test_cases):
            print("\n⏳ 다음 테스트까지 3초 대기...")
            time.sleep(3)
    
    # 결과 저장
    print("\n" + "=" * 80)
    print("📊 테스트 완료 - 결과 저장 중...")
    print("=" * 80)
    
    # JSON 결과 저장
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("✅ JSON 결과 저장: test_results.json")
    
    # HTML 보고서 생성 (report_generator 모듈 사용)
    html_report = generate_html_report(results)
    with open("test_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    print("✅ HTML 보고서 생성: test_report.html")
    
    # 요약 출력
    print("\n" + "=" * 80)
    print("📈 테스트 요약")
    print("=" * 80)
    print(f"총 테스트: {len(results)}개")
    print(f"통과 (PASS): {sum(1 for r in results if r['evaluation']['pass'])}개")
    print(f"실패 (FAIL): {sum(1 for r in results if not r['evaluation']['pass'])}개")
    print(f"통과율: {sum(1 for r in results if r['evaluation']['pass']) / len(results) * 100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
