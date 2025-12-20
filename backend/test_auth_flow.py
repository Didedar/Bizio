import requests
import sys
import random
import string

BASE_URL = "http://localhost:8000/api/v1"

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_random_email():
    return f"test_{generate_random_string()}@example.com"

def test_auth():
    email = generate_random_email()
    password = "password123"
    tenant_name = f"Test Tenant {generate_random_string()}"
    
    # 1. Register
    print(f"Registering user {email} with tenant '{tenant_name}'...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "tenant_name": tenant_name
        })
        if resp.status_code == 201:
            print("✅ Registration successful")
        else:
            print(f"❌ Registration failed: {resp.status_code} {resp.text}")
            return
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return

    # 2. Login
    print(f"Logging in user {email}...")
    try:
        resp = requests.post(f"{BASE_URL}/auth/token", data={
            "username": email,
            "password": password
        })
        if resp.status_code == 200:
            token_data = resp.json()
            access_token = token_data["access_token"]
            print(f"✅ Login successful. Token: {access_token[:20]}...")
        else:
            print(f"❌ Login failed: {resp.status_code} {resp.text}")
            return
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return

    # 3. Get Me
    print("Getting current user info...")
    try:
        resp = requests.get(f"{BASE_URL}/auth/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        if resp.status_code == 200:
            user = resp.json()
            print(f"✅ Get Me successful: {user['email']}")
            if user['tenants']:
                print(f"   Tenant: {user['tenants'][0]['name']}")
            else:
                print("   ⚠️ No tenants found for user")
        else:
            print(f"❌ Get Me failed: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"❌ Get Me request failed: {e}")

if __name__ == "__main__":
    test_auth()
