"""
프로젝트 멤버 관리 기능 테스트 스크립트
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_user_registration():
    """테스트 사용자 등록"""
    users = [
        {
            "email": "owner@test.com",
            "username": "project_owner", 
            "password": "testpass123"
        },
        {
            "email": "member1@test.com",
            "username": "member_one",
            "password": "testpass123"
        },
        {
            "email": "member2@test.com", 
            "username": "member_two",
            "password": "testpass123"
        }
    ]
    
    for user in users:
        response = requests.post(f"{BASE_URL}/auth/register", json=user)
        print(f"사용자 등록 ({user['username']}): {response.status_code}")
        if response.status_code not in [200, 201, 400]:  # 이미 등록된 경우도 허용
            print(f"등록 실패: {response.text}")

def get_auth_token(email, password):
    """인증 토큰 획득"""
    response = requests.post(f"{BASE_URL}/auth/token", data={
        "username": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_create_project(token):
    """프로젝트 생성 테스트"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "title": f"멤버십 테스트 프로젝트_{timestamp}",
        "description": "프로젝트 멤버 관리 기능을 테스트하는 프로젝트입니다."
    }
    
    response = requests.post(f"{BASE_URL}/api/projects/", 
                            json=project_data, headers=headers)
    print(f"프로젝트 생성: {response.status_code}")
    if response.status_code in [200, 201]:
        project = response.json()
        print(f"프로젝트 ID: {project['id']}")
        return project["id"]
    else:
        print(f"프로젝트 생성 실패: {response.text}")
        return None

def test_invite_member(project_id, token, member_email, role="viewer"):
    """멤버 초대 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    invitation_data = {
        "email": member_email,
        "role": role,
        "message": f"{role} 역할로 초대합니다."
    }
    
    response = requests.post(f"{BASE_URL}/api/projects/{project_id}/members",
                            json=invitation_data, headers=headers)
    print(f"멤버 초대 ({member_email}, {role}): {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"초대 결과: {result['message']}")
        return result.get("member_id")
    else:
        print(f"초대 실패: {response.text}")
        return None

def test_get_members(project_id, token):
    """멤버 목록 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/members",
                           headers=headers)
    print(f"멤버 목록 조회: {response.status_code}")
    if response.status_code == 200:
        members_data = response.json()
        print(f"전체 멤버 수: {members_data['total']}")
        for member in members_data["members"]:
            print(f"  - {member['user_username']} ({member['user_email']}) - {member['role']}")
        return members_data
    else:
        print(f"멤버 목록 조회 실패: {response.text}")
        return None

def test_member_stats(project_id, token):
    """멤버 통계 조회 테스트"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/members/stats",
                           headers=headers)
    print(f"멤버 통계 조회: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"통계 정보:")
        print(f"  - 전체 멤버: {stats['total_members']}")
        print(f"  - 활성 멤버: {stats['active_members']}")
        print(f"  - 소유자: {stats['owners']}")
        print(f"  - 관리자: {stats['admins']}")
        print(f"  - 편집자: {stats['editors']}")
        print(f"  - 뷰어: {stats['viewers']}")
        return stats
    else:
        print(f"통계 조회 실패: {response.text}")
        return None

def run_tests():
    """전체 테스트 실행"""
    print("=== 프로젝트 멤버 관리 기능 테스트 시작 ===\n")
    
    # 1. 사용자 등록
    print("1. 테스트 사용자 등록")
    test_user_registration()
    print()
    
    # 2. 로그인
    print("2. 프로젝트 소유자 로그인")
    owner_token = get_auth_token("owner@test.com", "testpass123")
    if not owner_token:
        print("소유자 로그인 실패!")
        return
    print("소유자 로그인 성공")
    print()
    
    # 3. 프로젝트 생성
    print("3. 프로젝트 생성")
    project_id = test_create_project(owner_token)
    if not project_id:
        print("프로젝트 생성 실패!")
        return
    print()
    
    # 4. 멤버 초대
    print("4. 멤버 초대")
    member1_id = test_invite_member(project_id, owner_token, "member1@test.com", "editor")
    member2_id = test_invite_member(project_id, owner_token, "member2@test.com", "viewer")
    print()
    
    # 5. 멤버 목록 조회
    print("5. 멤버 목록 조회")
    test_get_members(project_id, owner_token)
    print()
    
    # 6. 멤버 통계 조회
    print("6. 멤버 통계 조회")
    test_member_stats(project_id, owner_token)
    print()
    
    print("=== 테스트 완료 ===")

if __name__ == "__main__":
    run_tests()
