import sys
sys.path.insert(0, '.')
from app.utils.firebase_client import FirebaseClient
import bcrypt

firebase_client = FirebaseClient()

# 테스트 계정 데이터
accounts = [
    {
        'email': 'ems01@test.com',
        'password': 'ems01',
        'type': 'ems',
        'name': 'Seoul EMS Unit 1'
    },
    {
        'email': 'hospital01@test.com',
        'password': 'hosp01',
        'type': 'hospital',
        'name': 'Seoul University Hospital'
    },
    {
        'email': 'hospital02@test.com',
        'password': 'hosp02',
        'type': 'hospital',
        'name': 'Samsung Medical Center'
    },
    {
        'email': 'hospital03@test.com',
        'password': 'hosp03',
        'type': 'hospital',
        'name': 'Severance Hospital'
    }
]

print('Create Test Accounts with bcrypt...\n')

for account in accounts:
    try:
        # Check existing account
        existing = firebase_client.get_user_by_email(account['email'])
        if existing:
            print(f"WARNING - {account['email']} already exists")
            continue
        
        # Hash password using bcrypt directly
        password_bytes = account['password'].encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_data = {
            'email': account['email'],
            'password_hash': password_hash,
            'type': account['type'],
            'name': account['name'],
        }
        
        user_id = firebase_client.create_user(user_data)
        
        print(f"SUCCESS - {account['type'].upper()}")
        print(f"   ID: {user_id}")
        print(f"   Email: {account['email']}")
        print(f"   Name: {account['name']}")
        print(f"   Password: {account['password']}")
        print()
        
    except Exception as e:
        print(f"FAIL - {account['email']}: {str(e)}\n")

print('Complete!')
