"""
로깅 유틸리티 모듈
"""
import logging
from datetime import datetime
import os


def setup_logger(name="llm_test", log_dir="output/logs"):
    """
    로거 설정
    
    Args:
        name (str): 로거 이름
        log_dir (str): 로그 파일 저장 디렉토리
    
    Returns:
        logging.Logger: 설정된 로거 객체
    """
    # 로그 디렉토리 생성
    os.makedirs(log_dir, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 이미 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 포매터 생성
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 파일 핸들러 (전체 로그)
    log_filename = f"{log_dir}/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_test_start(logger, test_id, question, round_num):
    """테스트 시작 로그"""
    logger.info("="*80)
    logger.info(f"🧪 테스트 시작: {test_id} (Round {round_num})")
    logger.info(f"📝 질문: {question}")
    logger.info("="*80)


def log_test_result(logger, test_id, evaluation, answer_length):
    """테스트 결과 로그"""
    logger.info(f"✅ 테스트 완료: {test_id}")
    logger.info(f"답변 길이: {answer_length}자")
    logger.info(f"총점: {evaluation['total_score']}/{evaluation['max_score']}점")
    
    if evaluation['pass']:
        logger.info("결과: ✅ PASS")
    else:
        if evaluation['scores']['안전성'] == 0:
            logger.warning("결과: ❌ FAIL (안전성 0점 - 자동 실패)")
        else:
            logger.warning(f"결과: ❌ FAIL (총점 {evaluation['total_score']}점)")


def log_test_error(logger, test_id, error_msg):
    """테스트 에러 로그"""
    logger.error(f"❌ 테스트 실패: {test_id}")
    logger.error(f"에러: {error_msg}")
