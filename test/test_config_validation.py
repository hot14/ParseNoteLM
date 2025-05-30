#!/usr/bin/env python3
"""
환경설정 검증 테스트
모든 환경변수와 설정이 올바르게 로드되는지 확인
"""
import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from app.core.config import settings
from app.core.logging_config import setup_logging

def test_environment_variables():
    """환경변수 로딩 테스트"""
    print("=" * 60)
    print("🔧 환경변수 검증 테스트")
    print("=" * 60)
    
    # 필수 환경변수 목록
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY", 
        "OPENAI_API_KEY"
    ]
    
    print("\n📋 필수 환경변수 확인:")
    all_present = True
    
    for var in required_vars:
        env_value = os.environ.get(var)
        settings_value = getattr(settings, var, None)
        
        if env_value:
            print(f"  ✅ {var}: 환경변수 설정됨")
        else:
            print(f"  ❌ {var}: 환경변수 누락")
            all_present = False
            
        if settings_value:
            if var in ["SECRET_KEY", "OPENAI_API_KEY"]:
                # 민감한 정보는 일부만 표시
                display_value = f"{str(settings_value)[:10]}..." if len(str(settings_value)) > 10 else "***"
            else:
                display_value = settings_value
            print(f"      Settings: {display_value}")
        else:
            print(f"      Settings: 설정되지 않음")
    
    return all_present

def test_database_configuration():
    """데이터베이스 설정 테스트"""
    print("\n🗄️ 데이터베이스 설정 검증:")
    
    db_url = settings.DATABASE_URL
    print(f"  📍 DATABASE_URL: {db_url}")
    
    # SQLite 파일 경로 검증
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        db_file = Path(db_path)
        
        print(f"  📁 DB 파일 경로: {db_path}")
        print(f"  📂 상위 디렉토리 존재: {db_file.parent.exists()}")
        print(f"  📄 DB 파일 존재: {db_file.exists()}")
        
        if db_file.exists():
            print(f"  📏 DB 파일 크기: {db_file.stat().st_size} bytes")
        
        # 절대경로 여부 확인
        is_absolute = db_file.is_absolute()
        print(f"  🎯 절대경로 사용: {is_absolute}")
        
        return is_absolute and db_file.parent.exists()
    else:
        print("  ℹ️ SQLite 이외의 데이터베이스 사용")
        return True

def test_project_paths():
    """프로젝트 경로 설정 테스트"""
    print("\n📂 프로젝트 경로 검증:")
    
    project_root = Path(settings.PROJECT_ROOT)
    print(f"  🏠 PROJECT_ROOT: {project_root}")
    print(f"  📂 루트 디렉토리 존재: {project_root.exists()}")
    
    # 주요 디렉토리 확인
    important_dirs = [
        "backend",
        "backend/app", 
        "backend/app/core",
        "backend/app/routes",
        "docs",
        "test"
    ]
    
    all_exist = True
    for dir_name in important_dirs:
        dir_path = project_root / dir_name
        exists = dir_path.exists()
        print(f"  {'✅' if exists else '❌'} {dir_name}: {exists}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_logging_configuration():
    """로깅 설정 테스트"""
    print("\n📝 로깅 시스템 검증:")
    
    try:
        # 로그 디렉토리 생성
        log_dir = Path(settings.PROJECT_ROOT) / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 로깅 시스템 초기화
        setup_logging(
            level="DEBUG",
            log_file=str(log_dir / "test_config.log"),
            app_name="ConfigTest"
        )
        
        # 테스트 로그 메시지
        test_logger = logging.getLogger("config_test")
        test_logger.debug("DEBUG 레벨 테스트")
        test_logger.info("INFO 레벨 테스트")
        test_logger.warning("WARNING 레벨 테스트")
        test_logger.error("ERROR 레벨 테스트")
        
        print("  ✅ 로깅 시스템 초기화 성공")
        print(f"  📁 로그 디렉토리: {log_dir}")
        print(f"  📄 로그 파일: {log_dir / 'test_config.log'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 로깅 시스템 오류: {e}")
        return False

def test_api_configuration():
    """API 설정 테스트"""
    print("\n🌐 API 설정 검증:")
    
    # OpenAI API 키 확인
    openai_key = settings.OPENAI_API_KEY
    if openai_key:
        print(f"  ✅ OpenAI API 키: 설정됨 ({openai_key[:10]}...)")
    else:
        print("  ❌ OpenAI API 키: 설정되지 않음")
    
    # 기타 API 설정
    print(f"  🔢 최대 프로젝트 수: {settings.MAX_PROJECTS_PER_USER}")
    print(f"  📄 최대 문서 수: {settings.MAX_DOCUMENTS_PER_PROJECT}")
    print(f"  📏 최대 파일 크기: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB")
    print(f"  ⏰ 토큰 만료 시간: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}분")
    
    return bool(openai_key)

def main():
    """메인 테스트 실행"""
    print("🧪 ParseNoteLM 설정 검증 테스트 시작")
    print(f"⏰ 테스트 시간: {os.environ.get('TZ', 'local time')}")
    
    tests = [
        ("환경변수", test_environment_variables),
        ("데이터베이스", test_database_configuration), 
        ("프로젝트 경로", test_project_paths),
        ("로깅 시스템", test_logging_configuration),
        ("API 설정", test_api_configuration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ {test_name} 테스트 중 오류: {e}")
            results[test_name] = False
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    total_tests = len(tests)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 전체 결과: {passed_tests}/{total_tests} 통과")
    
    if passed_tests == total_tests:
        print("🎉 모든 설정 검증 테스트 통과!")
        return 0
    else:
        print("⚠️ 일부 설정에 문제가 있습니다. 위의 오류를 확인해주세요.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
