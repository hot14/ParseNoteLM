
# ParseNoteLM 테스트 결과 리포트

📅 **테스트 실행 시간**: 2025-05-30 13:06:36
📊 **전체 결과**: 1/2 통과 (50.0%)
⏱️ **총 소요 시간**: 0.34초

## 테스트 상세 결과

### 1. 환경설정 검증 - ✅ 통과
- 소요시간: 0.19초
- 상태: 정상 실행

### 2. 인증 시스템 - ❌ 실패
- 소요시간: 0.15초
- 오류: 2025-05-30 13:06:36,377 - server_health - INFO - ✅ 서버 상태 정상
2025-05-30 13:06:36,377 - AuthTestClient - INFO - 🆕 사용자 등록 테스트: test1@example.com
2025-05-30 13:06:36,388 - AuthTestClient - WARNING - ❌ 등록 실패: test1@example.com - {'detail': '사용자 등록 중 오류가 발생했습니다'}
2025-05-30 13:06:36,388 - AuthTestClient - INFO - 🆕 사용자 등록 테스트: test2@example.com
2025-05-30 13:06:36,391 - AuthTestClient - WARNING - ❌ 등록 실패: test2@example.com - {'detail': '사용자 등록 중 오류가 발생했습니다'}
2025-05-30 13:06:36,391 - registration_test - INFO - 🔄 중복 등록 테스트
2025-05-30 13:06:36,391 - AuthTestClient - INFO - 🆕 사용자 등록 테스트: test1@example.com
2025-05-30 13:06:36,393 - AuthTestClient - WARNING - ❌ 등록 실패: test1@example.com - {'detail': '사용자 등록 중 오류가 발생했습니다'}
2025-05-30 13:06:36,393 - AuthTestClient - INFO - 🔐 로그인 테스트: test1@example.com
2025-05-30 13:06:36,395 - AuthTestClient - WARNING - ❌ 로그인 실패: test1@example.com - {'detail': '로그인 처리 중 오류가 발생했습니다'}
2025-05-30 13:06:36,396 - AuthTestClient - INFO - 🔐 로그인 테스트: test1@example.com
2025-05-30 13:06:36,398 - AuthTestClient - WARNING - ❌ 로그인 실패: test1@example.com - {'detail': '로그인 처리 중 오류가 발생했습니다'}
2025-05-30 13:06:36,398 - AuthTestClient - INFO - 🔐 로그인 테스트: nonexistent@example.com
2025-05-30 13:06:36,400 - AuthTestClient - WARNING - ❌ 로그인 실패: nonexistent@example.com - {'detail': '로그인 처리 중 오류가 발생했습니다'}



## 권장사항


⚠️ 1개의 테스트가 실패했습니다. 다음 사항을 확인해주세요:

1. 환경변수(.env) 설정 확인
2. 데이터베이스 연결 확인  
3. 필요한 Python 패키지 설치 확인
4. 파일 권한 및 경로 설정 확인

실패한 테스트를 개별적으로 다시 실행하여 상세한 오류 정보를 확인하세요.


---
*이 리포트는 자동으로 생성되었습니다.*
