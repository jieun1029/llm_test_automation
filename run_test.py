"""
간단 실행 스크립트 (Windows/Mac/Linux 모두 지원)
"""
import os
import sys
import subprocess

print("=" * 80)
print("🤖 LLM 답변 평가 자동화 테스트")
print("=" * 80)
print()

# 1. cookies.json 체크 (여러 경로 시도)
cookie_paths = [
    "cookies.json",           # 현재 폴더
    "../cookies.json",        # 상위 폴더
    "../../cookies.json"      # 상위의 상위 폴더
]

cookie_path = None
for path in cookie_paths:
    if os.path.exists(path):
        cookie_path = path
        break

if not cookie_path:
    print("❌ cookies.json 파일이 없습니다.")
    print("📝 먼저 login_and_save_session.py를 실행하여 쿠키를 생성하세요.")
    print()
    print("실행 방법:")
    print("  python login_and_save_session.py")
    print()
    print("또는 다음 위치에 cookies.json을 복사하세요:")
    print(f"  - {os.path.abspath('.')}")
    print(f"  - {os.path.abspath('..')}")
    sys.exit(1)

print(f"✅ cookies.json 확인 완료 ({cookie_path})")
print()

# 2. pytest 실행
result = subprocess.run([sys.executable, "-m", "pytest", "-v"], cwd=os.path.dirname(__file__))

# 3. 결과 확인
print()
print("=" * 80)
print("📊 테스트 완료!")
print("=" * 80)
print()
print("📁 결과 파일:")
print("  - Excel 리포트: output/[타임스탬프]/test_results.xlsx")
print("  - 상세 답변 CSV: output/[타임스탬프]/detailed_answers.csv")
print()

sys.exit(result.returncode)
