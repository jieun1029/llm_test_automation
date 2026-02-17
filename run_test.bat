@echo off
chcp 65001 > nul
echo ========================================
echo 🤖 LLM 답변 평가 자동화 테스트
echo ========================================
echo.

REM 1. cookies.json 체크
if not exist "cookies.json" (
    echo ❌ cookies.json 파일이 없습니다.
    echo 📝 먼저 login_and_save_session.py를 실행하여 쿠키를 생성하세요.
    echo.
    echo 실행 방법:
    echo   python login_and_save_session.py
    pause
    exit /b 1
)

echo ✅ cookies.json 확인 완료
echo.

REM 2. 의존성 체크
echo 📦 의존성 확인 중...
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo ❌ pytest가 설치되어 있지 않습니다.
    echo 📝 다음 명령어로 설치하세요:
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ 의존성 확인 완료
echo.

REM 3. 이전 결과 삭제 여부
set /p DELETE="🗑️  이전 결과를 삭제하시겠습니까? (y/N): "
if /i "%DELETE%"=="y" (
    if exist output rmdir /s /q output
    echo ✅ 이전 결과 삭제 완료
)

echo.
echo 🚀 테스트 실행 중...
echo ========================================
echo.

REM 4. pytest 실행
pytest -v

REM 5. 결과 확인
echo.
echo ========================================
echo 📊 테스트 완료!
echo ========================================
echo.
echo 📁 결과 파일:
echo   - HTML 리포트: output\test_report.html
echo   - JSON 결과: output\test_results.json
echo   - 상세 답변: output\detailed_answers.json
echo   - Allure 결과: output\allure-results\
echo.
echo 🌐 Allure 리포트 보기:
echo   allure serve output\allure-results
echo.
pause
