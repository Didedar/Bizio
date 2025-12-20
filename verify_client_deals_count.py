import requests
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# API Config
API_URL = "http://localhost:8000/api/v1"
ADMIN_EMAIL = "admin@example.com"  # Assuming default admin
ADMIN_PASS = "admin" # Assuming simplified default or I need to register one

def get_token():
    # Try default credentials or register
    try:
        resp = requests.post(f"{API_URL}/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASS})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except:
        pass
    
    # Try registration
    try:
        reg_data = {
            "email": "test_admin@example.com",
            "password": "password123",
            "full_name": "Test Admin",
            "tenant_name": "Test Tenant"
        }
        requests.post(f"{API_URL}/auth/register", json=reg_data)
        # Login
        resp = requests.post(f"{API_URL}/auth/token", data={"username": "test_admin@example.com", "password": "password123"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception as e:
        print(f"Auth failed: {e}")
        return None

def verify():
    token = get_token()
    if not token:
        print("Could not get auth token")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # Get user to get tenant_id
    me_resp = requests.get(f"{API_URL}/auth/me", headers=headers)
    if me_resp.status_code != 200:
        print(f"Get me failed: {me_resp.text}")
        return
    
    user = me_resp.json()
    if not user.get("tenants"):
        print("No tenants found for user")
        return
        
    tenant_id = user["tenants"][0]["id"]
    print(f"Tenant ID: {tenant_id}")
    
    # List clients
    resp = requests.get(f"{API_URL}/clients?tenant_id={tenant_id}", headers=headers)
    if resp.status_code != 200:
        print(f"List clients failed: {resp.text}")
        return

    clients = resp.json()
    print(f"Found {len(clients)} clients")
    
    for client in clients:
        print(f"Client: {client['name']} (ID: {client['id']})")
        if 'deals_count' in client:
            print(f"  deals_count: {client['deals_count']}")
        else:
            print("  deals_count: MISSING")

if __name__ == "__main__":
    verify()
