#!/usr/bin/env python3
"""
ParseNoteLM 종합 테스트 러너
모든 테스트를 순차적으로 실행하고 결과를 리포트
"""
import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

def run_test(test_name: str, script_path: str):
    """개별 테스트 실행"""
    print(f"\n{'='*20} {test_name} {'='*20}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=60  # 60초 타임아웃
        )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} 성공 (소요시간: {elapsed_time:.2f}초)")
            print("📤 출력:")
            print(result.stdout)
            return True, elapsed_time, result.stdout, None
        else:
            print(f"❌ {test_name} 실패 (소요시간: {elapsed_time:.2f}초)")
            print("📤 표준 출력:")
            print(result.stdout)
            print("🚨 오류 출력:")
            print(result.stderr)
            return False, elapsed_time, result.stdout, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} 타임아웃 (60초 초과)")
        return False, 60, "", "테스트 타임아웃"
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"💥 {test_name} 실행 중 예외 발생: {e}")
        return False, elapsed_time, "", str(e)

def generate_test_report(results: list, output_file: str):
    """테스트 결과 리포트 생성"""
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result['success'])
    total_time = sum(result['time'] for result in results)
    
    report = f"""
# ParseNoteLM 테스트 결과 리포트

📅 **테스트 실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **전체 결과**: {passed_tests}/{total_tests} 통과 ({passed_tests/total_tests*100:.1f}%)
⏱️ **총 소요 시간**: {total_time:.2f}초

## 테스트 상세 결과

"""
    
    for i, result in enumerate(results, 1):
        status = "✅ 통과" if result['success'] else "❌ 실패"
        report += f"### {i}. {result['name']} - {status}\n"
        report += f"- 소요시간: {result['time']:.2f}초\n"
        
        if result['success']:
            report += "- 상태: 정상 실행\n"
        else:
            report += f"- 오류: {result['error']}\n"
        
        report += "\n"
    
    report += f"""
## 권장사항

{'✨ 모든 테스트가 통과했습니다! 시스템이 정상적으로 설정되어 있습니다.' if passed_tests == total_tests else f'''
⚠️ {total_tests - passed_tests}개의 테스트가 실패했습니다. 다음 사항을 확인해주세요:

1. 환경변수(.env) 설정 확인
2. 데이터베이스 연결 확인  
3. 필요한 Python 패키지 설치 확인
4. 파일 권한 및 경로 설정 확인

실패한 테스트를 개별적으로 다시 실행하여 상세한 오류 정보를 확인하세요.
'''}

---
*이 리포트는 자동으로 생성되었습니다.*
"""
    
    # 리포트 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report

def main():
    """메인 테스트 실행"""
    print("🧪 ParseNoteLM 종합 테스트 시작")
    print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 프로젝트 루트 경로
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # 테스트 목록 (순서 중요)
    tests = [
        {
            "name": "환경설정 검증",
            "script": test_dir / "test_config_validation.py",
            "description": "환경변수, 경로, 설정값 검증"
        },
        {
            "name": "인증 시스템",
            "script": test_dir / "test_auth.py",
            "description": "사용자 등록, 로그인, JWT 토큰 검증"
        },
        {
            "name": "비디오 요약 API",
            "script": project_root / "backend/test_video.py",
            "description": "영상 업로드 후 요약/스크립트 반환"
        }
    ]
    
    # 스크립트 존재 확인
    print("\n🔍 테스트 스크립트 확인:")
    available_tests = []
    for test in tests:
        if test["script"].exists():
            print(f"  ✅ {test['name']}: {test['script']}")
            available_tests.append(test)
        else:
            print(f"  ❌ {test['name']}: {test['script']} (파일 없음)")
    
    if not available_tests:
        print("❌ 실행 가능한 테스트가 없습니다.")
        return 1
    
    # 테스트 실행
    results = []
    print(f"\n🏃 {len(available_tests)}개 테스트 실행 시작...")
    
    for test in available_tests:
        success, elapsed_time, stdout, stderr = run_test(
            test["name"], 
            str(test["script"])
        )
        
        results.append({
            "name": test["name"],
            "success": success,
            "time": elapsed_time,
            "stdout": stdout,
            "error": stderr,
            "description": test["description"]
        })
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 최종 테스트 결과")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results if result['success'])
    total_time = sum(result['time'] for result in results)
    
    for result in results:
        status = "✅ 통과" if result['success'] else "❌ 실패"
        print(f"  {result['name']}: {status} ({result['time']:.2f}초)")
    
    print(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 통과")
    print(f"⏱️ 총 소요 시간: {total_time:.2f}초")
    
    # 리포트 생성
    report_file = test_dir / "test_report.md"
    report_content = generate_test_report(results, str(report_file))
    print(f"\n📝 상세 리포트: {report_file}")
    
    # 성공률에 따른 메시지
    success_rate = passed_tests / total_tests
    if success_rate == 1.0:
        print("🎉 모든 테스트 통과! 시스템이 준비되었습니다.")
        return 0
    elif success_rate >= 0.8:
        print("⚠️ 대부분의 테스트가 통과했지만 일부 개선이 필요합니다.")
        return 1
    else:
        print("🚨 많은 테스트가 실패했습니다. 시스템 설정을 점검해주세요.")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
