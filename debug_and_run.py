"""
디버깅용 간단 실행 스크립트
"""
import os
import sys

print("=" * 80)
print("🔍 경로 디버깅")
print("=" * 80)
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"스크립트 위치: {os.path.dirname(__file__)}")
print()

# cookies.json 찾기
print("cookies.json 찾는 중...")
paths_to_check = [
    "cookies.json",
    "../cookies.json",
    "../../cookies.json",
    os.path.join(os.getcwd(), "cookies.json"),
    os.path.join(os.path.dirname(__file__), "cookies.json"),
    os.path.join(os.path.dirname(__file__), "..", "cookies.json"),
]

found = False
for path in paths_to_check:
    abs_path = os.path.abspath(path)
    exists = os.path.exists(path)
    print(f"  {'✅' if exists else '❌'} {abs_path}")
    if exists and not found:
        found = True
        print(f"      👆 여기서 발견!")

if not found:
    print()
    print("❌ cookies.json을 찾을 수 없습니다!")
    print()
    print("📁 현재 폴더의 파일 목록:")
    for f in os.listdir("."):
        print(f"  - {f}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ 디버깅 완료 - 이제 테스트 실행")
print("=" * 80)
print()

# 실제 테스트 실행
import subprocess
result = subprocess.run([sys.executable, "-m", "pytest", "-v"])
sys.exit(result.returncode)
