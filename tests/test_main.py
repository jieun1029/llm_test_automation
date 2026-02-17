"""
pytest 메인 테스트 파일 (10개 질문 × 2회 반복, 랜덤 딜레이)
"""
import pytest
import json
import time
import random
from datetime import datetime
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.session_manager import SessionManager
from core.api_client import APIClient
from core.evaluator import Evaluator
from reports.report_generator import generate_excel_report, save_detailed_answers_csv
from utils.logger import setup_logger, log_test_start, log_test_result, log_test_error
from utils.scoring import calculate_statistics, print_statistics, calculate_category_statistics, print_category_statistics

# 설정
BASE_API_V1 = "https://api.myalan.ai/api/v1"
BASE_API_V2 = "https://api.myalan.ai/api/v2"
PERSONA_ID = "67a8266697ac2b9de6c51edf"
COOKIE_FILE = "cookies.json"

# 전역 변수 (테스트 결과 수집용)
all_results = []


class TestLLMEvaluation:
    """LLM 답변 평가 테스트 클래스"""
    
    @classmethod
    def setup_class(cls):
        """테스트 클래스 초기화"""
        print("\n" + "="*80)
        print("🤖 LLM 답변 평가 자동화 테스트 시작")
        print("="*80)
        
        # 로거 설정
        cls.logger = setup_logger()
        cls.logger.info("테스트 시스템 초기화 중...")
        
        # 설정 로드
        with open("config/test_questions.json", "r", encoding="utf-8") as f:
            cls.test_data = json.load(f)
        
        cls.settings = cls.test_data["settings"]
        cls.test_cases = cls.test_data["test_cases"]
        cls.repeat_count = cls.settings["repeat_count"]
        cls.delay_between_tests = cls.settings["delay_between_tests"]
        cls.delay_between_rounds = cls.settings.get("delay_between_rounds", 5)
        
        cls.logger.info(f"테스트 케이스 수: {len(cls.test_cases)}개")
        cls.logger.info(f"반복 횟수: {cls.repeat_count}회")
        
        # 예상 소요 시간 계산
        if isinstance(cls.delay_between_tests, list):
            avg_delay = sum(cls.delay_between_tests) / 2
        else:
            avg_delay = cls.delay_between_tests
        
        total_time = (len(cls.test_cases) - 1) * avg_delay * cls.repeat_count + cls.delay_between_rounds * (cls.repeat_count - 1)
        cls.logger.info(f"예상 소요 시간: 약 {int(total_time / 60)}분")
        
        # 세션 매니저 초기화
        cls.session_manager = SessionManager(COOKIE_FILE)
        cls.session_manager.load_session()
        
        # 로그인 확인
        success, user_name = cls.session_manager.check_login(BASE_API_V2)
        if not success:
            cls.logger.error("❌ 로그인 실패. cookies.json을 확인하세요.")
            pytest.exit("로그인 실패")
        
        cls.logger.info(f"✅ 로그인 성공: {user_name} (ID: {cls.session_manager.get_user_id()})")
        
        # API 클라이언트 초기화
        cls.api_client = APIClient(
            session=cls.session_manager.session,
            base_api_v1=BASE_API_V1,
            base_api_v2=BASE_API_V2,
            persona_id=PERSONA_ID,
            user_id=cls.session_manager.get_user_id()
        )
        
        # 평가자 초기화
        cls.evaluator = Evaluator("config/evaluation_criteria.json")
        
        cls.logger.info("✅ 테스트 시스템 초기화 완료\n")
    
    def test_llm_response(self, test_params):
        """
        LLM 답변 평가 테스트 (동적 파라미터)
        
        Args:
            test_params: pytest fixture (round_num, test_case 포함)
        """
        # 파라미터 가져오기
        round_num = test_params['round_num']
        test_case = test_params['test_case']
        
        # 로그 시작
        log_test_start(self.logger, test_case['id'], test_case['question'], round_num)
        
        # 1. 채널 생성 및 질문 전송
        success, answer, error_msg = self.api_client.execute_test(test_case['question'])
        
        if not success:
            log_test_error(self.logger, test_case['id'], error_msg)
            pytest.fail(f"테스트 실패: {error_msg}")
        
        self.logger.info(f"💬 답변 수신 완료 ({len(answer)}자)")
        
        # 2. 답변 평가
        evaluation = self.evaluator.evaluate_answer(test_case, answer)
        
        # 로그 결과
        log_test_result(self.logger, test_case['id'], evaluation, len(answer))
        
        # 3. 결과 저장
        result = {
            "test_id": test_case['id'],
            "round": round_num,
            "question": test_case['question'],
            "category": test_case['category'],
            "answer": answer,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }
        
        all_results.append(result)
        
        # 4. 랜덤 대기 (다음 테스트 전)
        if self.delay_between_tests:
            # 리스트면 랜덤, 숫자면 그대로
            if isinstance(self.delay_between_tests, list):
                delay = random.randint(self.delay_between_tests[0], self.delay_between_tests[1])
            else:
                delay = self.delay_between_tests
            
            self.logger.info(f"⏳ 다음 테스트까지 {delay}초 대기...\n")
            time.sleep(delay)
        
        # Assertion (pytest fail 처리)
        assert evaluation['pass'], f"평가 실패: 총점 {evaluation['total_score']}/{evaluation['max_score']}점"
    
    @classmethod
    def teardown_class(cls):
        """테스트 클래스 종료 처리"""
        if not all_results:
            cls.logger.warning("⚠️ 테스트 결과가 없습니다.")
            return
        
        cls.logger.info("\n" + "="*80)
        cls.logger.info("📊 테스트 완료 - 결과 저장 중...")
        cls.logger.info("="*80)
        
        # 타임스탬프 폴더 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"output/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Excel 리포트 생성
        generate_excel_report(all_results, f"{output_dir}/test_results.xlsx")
        cls.logger.info(f"✅ Excel 리포트 생성: {output_dir}/test_results.xlsx")
        
        # 상세 답변 CSV 저장
        save_detailed_answers_csv(all_results, f"{output_dir}/detailed_answers.csv")
        cls.logger.info(f"✅ 상세 답변 CSV 저장: {output_dir}/detailed_answers.csv")
        
        # 통계 출력
        stats = calculate_statistics(all_results)
        print_statistics(stats)
        
        # 카테고리별 통계
        category_stats = calculate_category_statistics(all_results)
        print_category_statistics(category_stats)
        
        cls.logger.info("\n✅ 모든 작업 완료!")


def pytest_configure(config):
    """pytest 설정 커스터마이징"""
    # 테스트 케이스 로드
    with open("config/test_questions.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    config.test_cases = test_data["test_cases"]
    config.addinivalue_line("markers", "round: 테스트 라운드 마커")


def pytest_generate_tests(metafunc):
    """동적으로 테스트 파라미터 생성"""
    if "test_params" in metafunc.fixturenames:
        # 설정 파일 로드
        import json
        with open("config/test_questions.json", "r", encoding="utf-8") as f:
            test_data = json.load(f)
        
        repeat_count = test_data["settings"]["repeat_count"]
        test_cases = test_data["test_cases"]
        
        # 파라미터 조합 생성
        params = []
        for round_num in range(1, repeat_count + 1):
            for test_case in test_cases:
                params.append({
                    'round_num': round_num,
                    'test_case': test_case
                })
        
        # 테스트 ID 생성
        ids = [f"Round{p['round_num']}-{p['test_case']['id']}" for p in params]
        
        metafunc.parametrize("test_params", params, ids=ids)


@pytest.fixture
def test_params(request):
    """테스트 파라미터 fixture"""
    return request.param


def pytest_collection_modifyitems(config, items):
    """테스트 아이템 수정 (정렬 등)"""
    # 라운드 순서대로 정렬
    items.sort(key=lambda item: item.nodeid)
