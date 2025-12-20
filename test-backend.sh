#!/bin/bash
echo "Testing backend connection..."
echo ""

# Test 1: Check if backend is running
echo "1. Testing backend health endpoint..."
response=$(curl -s http://localhost:8000/ 2>&1)
if [[ $response == *"status"* ]]; then
    echo "✅ Backend is running"
    echo "   Response: $response"
else
    echo "❌ Backend is NOT running or not accessible"
    echo "   Error: $response"
    echo ""
    echo "   Start backend with:"
    echo "   cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

echo ""
echo "2. Testing login endpoint..."
login_response=$(curl -s -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@bizio.com&password=demo123" 2>&1)

if [[ $login_response == *"access_token"* ]]; then
    echo "✅ Login endpoint works"
    echo "   User exists and credentials are correct"
else
    echo "❌ Login failed"
    echo "   Response: $login_response"
    echo ""
    echo "   Run seed script:"
    echo "   cd backend && python seed_data.py"
    exit 1
fi

echo ""
echo "✅ All tests passed! Backend is ready."
