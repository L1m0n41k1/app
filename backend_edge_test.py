#!/usr/bin/env python3
"""
Backend Edge Case Tests for Sender Mobile Application
Tests error handling, validation, and edge cases
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://multi-sender-1.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class SenderEdgeCaseTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
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
    
    def test_duplicate_registration(self):
        """Test registering with duplicate email"""
        test_data = {
            "email": "duplicate.test@example.com",
            "password": "TestPass123!",
            "name": "Duplicate Test"
        }
        
        try:
            # First registration
            response1 = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=test_data,
                timeout=10
            )
            
            # Second registration with same email
            response2 = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=test_data,
                timeout=10
            )
            
            if response1.status_code == 200 and response2.status_code == 400:
                self.log_test("Duplicate Registration", True, "Correctly rejected duplicate email with 400")
                return True
            else:
                self.log_test("Duplicate Registration", False, 
                            f"Expected 200 then 400, got {response1.status_code} then {response2.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Duplicate Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_invalid_login_credentials(self):
        """Test login with invalid credentials"""
        invalid_data = {
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                headers=self.headers,
                json=invalid_data,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Invalid Login", True, "Correctly rejected invalid credentials with 401")
                return True
            else:
                self.log_test("Invalid Login", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_malformed_json(self):
        """Test API with malformed JSON"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                data="invalid json data",
                timeout=10
            )
            
            if response.status_code == 422:  # FastAPI returns 422 for validation errors
                self.log_test("Malformed JSON", True, "Correctly handled malformed JSON with 422")
                return True
            else:
                self.log_test("Malformed JSON", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Malformed JSON", False, f"Request failed: {str(e)}")
            return False
    
    def test_missing_required_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {
            "email": "incomplete@example.com"
            # Missing password and name
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=incomplete_data,
                timeout=10
            )
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_test("Missing Required Fields", True, "Correctly rejected incomplete data with 422")
                return True
            else:
                self.log_test("Missing Required Fields", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Missing Required Fields", False, f"Request failed: {str(e)}")
            return False
    
    def test_invalid_email_format(self):
        """Test registration with invalid email format"""
        invalid_email_data = {
            "email": "not-an-email",
            "password": "ValidPass123!",
            "name": "Test User"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=invalid_email_data,
                timeout=10
            )
            
            if response.status_code == 422:  # FastAPI validation error for invalid email
                self.log_test("Invalid Email Format", True, "Correctly rejected invalid email format with 422")
                return True
            else:
                self.log_test("Invalid Email Format", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Email Format", False, f"Request failed: {str(e)}")
            return False
    
    def test_create_account_invalid_platform(self):
        """Test creating account with invalid platform"""
        # First register and login to get token
        register_data = {
            "email": f"platform.test.{datetime.now().timestamp()}@example.com",
            "password": "PlatformTest123!",
            "name": "Platform Test User"
        }
        
        try:
            reg_response = requests.post(
                f"{self.base_url}/auth/register",
                headers=self.headers,
                json=register_data,
                timeout=10
            )
            
            if reg_response.status_code != 200:
                self.log_test("Invalid Platform Account", False, "Failed to create test user")
                return False
            
            token = reg_response.json()["access_token"]
            auth_headers = self.headers.copy()
            auth_headers["Authorization"] = f"Bearer {token}"
            
            # Try to create account with invalid platform
            invalid_account_data = {
                "platform": "invalid_platform",
                "display_name": "Invalid Platform Account",
                "session_data": {}
            }
            
            response = requests.post(
                f"{self.base_url}/accounts",
                headers=auth_headers,
                json=invalid_account_data,
                timeout=10
            )
            
            if response.status_code == 422:  # FastAPI validation error
                self.log_test("Invalid Platform Account", True, "Correctly rejected invalid platform with 422")
                return True
            else:
                self.log_test("Invalid Platform Account", False, f"Expected 422, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Invalid Platform Account", False, f"Request failed: {str(e)}")
            return False
    
    def run_edge_case_tests(self):
        """Run all edge case tests"""
        print("🔍 Starting Sender Backend Edge Case Tests")
        print("=" * 50)
        
        self.test_duplicate_registration()
        self.test_invalid_login_credentials()
        self.test_malformed_json()
        self.test_missing_required_fields()
        self.test_invalid_email_format()
        self.test_create_account_invalid_platform()
        
        # Summary
        print("\n" + "=" * 50)
        print("📈 EDGE CASE TEST SUMMARY")
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
    tester = SenderEdgeCaseTester()
    success = tester.run_edge_case_tests()
    sys.exit(0 if success else 1)