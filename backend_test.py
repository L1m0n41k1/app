#!/usr/bin/env python3
"""
Backend API Tests for Sender Mobile Application
Tests authentication, dashboard, and accounts management APIs
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://multi-sender-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class SenderAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.access_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        test_data = {
            "email": "maria.sender@example.com",
            "password": "SecurePass123!",
            "name": "Maria Rodriguez"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    self.access_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.access_token}"
                    self.log_test("User Registration", True, "Successfully registered user and received JWT token")
                    return True
                else:
                    self.log_test("User Registration", False, "Missing token in response", data)
                    return False
            elif response.status_code == 400:
                # Try with different email in case user already exists
                test_data["email"] = f"maria.sender.{datetime.now().timestamp()}@example.com"
                response = requests.post(
                    f"{self.base_url}/auth/register",
                    headers=self.headers,
                    json=test_data,
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.access_token}"
                    self.log_test("User Registration", True, "Successfully registered user with unique email")
                    return True
                else:
                    self.log_test("User Registration", False, f"Registration failed with status {response.status_code}", response.text)
                    return False
            else:
                self.log_test("User Registration", False, f"Unexpected status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login endpoint"""
        # First register a user for login test
        register_data = {
            "email": f"login.test.{datetime.now().timestamp()}@example.com",
            "password": "LoginTest123!",
            "name": "Login Test User"
        }
        
        try:
            # Register user first
            reg_response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=register_data,
                timeout=10
            )
            
            if reg_response.status_code != 200:
                self.log_test("User Login", False, "Failed to create test user for login", reg_response.text)
                return False
            
            # Now test login
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            
            response = requests.post(
                f"{self.base_url}/auth/login",
                headers=self.headers,
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "token_type" in data:
                    # Update token for subsequent tests
                    self.access_token = data["access_token"]
                    self.headers["Authorization"] = f"Bearer {self.access_token}"
                    self.log_test("User Login", True, "Successfully logged in and received JWT token")
                    return True
                else:
                    self.log_test("User Login", False, "Missing token in login response", data)
                    return False
            else:
                self.log_test("User Login", False, f"Login failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Login request failed: {str(e)}")
            return False
    
    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.access_token:
            self.log_test("Get Current User", False, "No access token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "email", "name", "subscription_plan", "is_admin"]
                if all(field in data for field in required_fields):
                    self.log_test("Get Current User", True, f"Successfully retrieved user info for {data.get('name', 'user')}")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Get Current User", False, f"Missing required fields: {missing}", data)
                    return False
            elif response.status_code == 401:
                self.log_test("Get Current User", False, "Authentication failed - invalid token", response.text)
                return False
            else:
                self.log_test("Get Current User", False, f"Unexpected status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get Current User", False, f"Request failed: {str(e)}")
            return False
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        if not self.access_token:
            self.log_test("Dashboard Statistics", False, "No access token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/dashboard",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["active_accounts", "messages_today", "active_jobs", "recent_jobs"]
                if all(field in data for field in required_fields):
                    # Validate structure of messages_today
                    messages = data.get("messages_today", {})
                    if "successful" in messages and "failed" in messages:
                        self.log_test("Dashboard Statistics", True, 
                                    f"Dashboard stats retrieved: {data['active_accounts']} accounts, "
                                    f"{messages['successful']} successful messages today")
                        return True
                    else:
                        self.log_test("Dashboard Statistics", False, "Invalid messages_today structure", data)
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Dashboard Statistics", False, f"Missing required fields: {missing}", data)
                    return False
            elif response.status_code == 401:
                self.log_test("Dashboard Statistics", False, "Authentication failed", response.text)
                return False
            else:
                self.log_test("Dashboard Statistics", False, f"Unexpected status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Dashboard Statistics", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_accounts(self):
        """Test getting user's messaging accounts"""
        if not self.access_token:
            self.log_test("Get Accounts", False, "No access token available")
            return False
        
        try:
            response = requests.get(
                f"{self.base_url}/accounts",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Accounts", True, f"Successfully retrieved {len(data)} messaging accounts")
                    return True
                else:
                    self.log_test("Get Accounts", False, "Response is not a list", data)
                    return False
            elif response.status_code == 401:
                self.log_test("Get Accounts", False, "Authentication failed", response.text)
                return False
            else:
                self.log_test("Get Accounts", False, f"Unexpected status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Get Accounts", False, f"Request failed: {str(e)}")
            return False
    
    def test_create_account(self):
        """Test creating a new messaging account"""
        if not self.access_token:
            self.log_test("Create Account", False, "No access token available")
            return False
        
        account_data = {
            "platform": "whatsapp",
            "display_name": "Maria's WhatsApp Business",
            "session_data": {
                "phone_number": "+1234567890",
                "business_name": "Maria's Marketing Agency"
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/accounts",
                headers=self.headers,
                json=account_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "user_id", "platform", "display_name", "is_active", "created_at"]
                if all(field in data for field in required_fields):
                    if data["platform"] == account_data["platform"] and data["display_name"] == account_data["display_name"]:
                        self.log_test("Create Account", True, f"Successfully created {data['platform']} account: {data['display_name']}")
                        return True
                    else:
                        self.log_test("Create Account", False, "Account data mismatch", data)
                        return False
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Account", False, f"Missing required fields: {missing}", data)
                    return False
            elif response.status_code == 401:
                self.log_test("Create Account", False, "Authentication failed", response.text)
                return False
            else:
                self.log_test("Create Account", False, f"Unexpected status code: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Create Account", False, f"Request failed: {str(e)}")
            return False
    
    def test_invalid_authentication(self):
        """Test API behavior with invalid authentication"""
        invalid_headers = {"Content-Type": "application/json", "Authorization": "Bearer invalid_token"}
        
        try:
            response = requests.get(
                f"{self.base_url}/auth/me",
                headers=invalid_headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Invalid Authentication", True, "Correctly rejected invalid token with 401")
                return True
            else:
                self.log_test("Invalid Authentication", False, f"Expected 401, got {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Invalid Authentication", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting Sender Backend API Tests")
        print("=" * 50)
        
        # Test authentication flow
        print("\n📋 Testing Authentication System...")
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        self.test_invalid_authentication()
        
        # Test dashboard and accounts (requires authentication)
        print("\n📊 Testing Dashboard and Accounts...")
        self.test_dashboard_stats()
        self.test_get_accounts()
        self.test_create_account()
        
        # Summary
        print("\n" + "=" * 50)
        print("📈 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = SenderAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)