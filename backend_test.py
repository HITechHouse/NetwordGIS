#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime, timedelta
import random

# Base URL from frontend/.env
BASE_URL = "https://8a814be7-1247-4171-a328-06f467fd9987.preview.emergentagent.com/api"

# Test data
CITIES = ["دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس", "درعا", "السويداء", "القنيطرة", "الرقة", "دير الزور", "الحسكة"]
INFRASTRUCTURE_TYPES = ["electricity", "water", "sewage", "telecommunications", "roads", "public_facilities"]
STATUSES = ["operational", "damaged", "under_maintenance", "needs_repair"]
CONDITIONS = ["excellent", "good", "fair", "poor", "critical"]

# Test users
USERS = {
    "municipality": {
        "email": "municipality_user@example.com",
        "username": "بلدية_دمشق",
        "password": "Password123!",
        "role": "municipality",
        "city": "دمشق"
    },
    "directorate": {
        "email": "directorate_user@example.com",
        "username": "مديرية_حلب",
        "password": "Password123!",
        "role": "directorate",
        "city": "حلب"
    },
    "ministry": {
        "email": "ministry_user@example.com",
        "username": "وزارة_البنية_التحتية",
        "password": "Password123!",
        "role": "ministry",
        "city": None
    }
}

# Test infrastructure items
def generate_infrastructure_item(city):
    return {
        "name": f"بنية تحتية {random.choice(INFRASTRUCTURE_TYPES)} في {city}",
        "type": random.choice(INFRASTRUCTURE_TYPES),
        "subtype": "main",
        "coordinates": [random.uniform(35.0, 38.0), random.uniform(32.0, 37.0)],  # Syria coordinates
        "status": random.choice(STATUSES),
        "condition": random.choice(CONDITIONS),
        "installation_date": (datetime.utcnow() - timedelta(days=random.randint(365, 3650))).isoformat(),
        "description": f"وصف لعنصر البنية التحتية في {city}",
        "city": city,
        "district": f"حي {random.randint(1, 10)}"
    }

# Helper functions
def print_test_header(test_name):
    print(f"\n{'=' * 80}")
    print(f"TESTING: {test_name}")
    print(f"{'=' * 80}")

def print_test_result(test_name, success, message=""):
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{status} - {test_name}: {message}")
    return success

def register_user(user_data):
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    return response

def login_user(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    return response

def create_infrastructure(token, data):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/infrastructure", headers=headers, json=data)
    return response

def get_infrastructure(token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/infrastructure", headers=headers, params=params)
    return response

def update_infrastructure(token, item_id, data):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(f"{BASE_URL}/infrastructure/{item_id}", headers=headers, json=data)
    return response

def delete_infrastructure(token, item_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/infrastructure/{item_id}", headers=headers)
    return response

def get_geojson(token, params=None):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/infrastructure/geojson", headers=headers, params=params)
    return response

def get_analytics(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/analytics/overview", headers=headers)
    return response

def get_cities():
    response = requests.get(f"{BASE_URL}/cities")
    return response

def test_root_endpoint():
    print_test_header("Root Endpoint")
    
    response = requests.get(f"{BASE_URL}/")
    success = response.status_code == 200 and "Syrian Infrastructure GIS API" in response.json().get("message", "")
    
    return print_test_result("Root Endpoint", success, f"Status: {response.status_code}, Response: {response.json()}")

def test_authentication():
    print_test_header("Authentication System")
    
    all_passed = True
    tokens = {}
    user_ids = {}
    
    # Test user registration for each role
    for role, user_data in USERS.items():
        # Try to register the user
        response = register_user(user_data)
        
        # If user already exists, this is fine for testing purposes
        if response.status_code == 400 and "Email already registered" in response.json().get("detail", ""):
            print(f"User {user_data['email']} already exists, proceeding to login")
        else:
            success = response.status_code == 200 and "id" in response.json()
            all_passed = all_passed and success
            print_test_result(f"Register {role} user", success, f"Status: {response.status_code}")
            
            if success:
                user_ids[role] = response.json()["id"]
        
        # Test login
        login_response = login_user(user_data["email"], user_data["password"])
        success = login_response.status_code == 200 and "token" in login_response.json()
        all_passed = all_passed and success
        print_test_result(f"Login {role} user", success, f"Status: {login_response.status_code}")
        
        if success:
            tokens[role] = login_response.json()["token"]
            if "id" not in user_ids:
                user_ids[role] = login_response.json()["user"]["id"]
    
    # Test invalid login
    invalid_login = login_user("nonexistent@example.com", "wrongpassword")
    success = invalid_login.status_code == 401
    all_passed = all_passed and success
    print_test_result("Invalid login credentials", success, f"Status: {invalid_login.status_code}")
    
    # Test duplicate registration
    if "ministry" in tokens:  # Only if we successfully registered at least one user
        duplicate_reg = register_user(USERS["ministry"])
        success = duplicate_reg.status_code == 400
        all_passed = all_passed and success
        print_test_result("Duplicate registration", success, f"Status: {duplicate_reg.status_code}")
    
    return all_passed, tokens, user_ids

def test_infrastructure_management(tokens):
    print_test_header("Infrastructure Data Management")
    
    all_passed = True
    created_items = {}
    
    # Test creating infrastructure items for each role
    for role, token in tokens.items():
        city = USERS[role]["city"] if USERS[role]["city"] else random.choice(CITIES)
        item_data = generate_infrastructure_item(city)
        
        response = create_infrastructure(token, item_data)
        
        # Municipality users can only create in their city
        if role == "municipality" and item_data["city"] != USERS[role]["city"]:
            expected_success = False
        else:
            expected_success = True
        
        success = (response.status_code == 200) == expected_success
        all_passed = all_passed and success
        
        message = f"Status: {response.status_code}"
        if response.status_code == 200:
            created_items[role] = response.json()
            message += f", Item ID: {created_items[role]['id']}"
        
        print_test_result(f"Create infrastructure as {role}", success, message)
    
    # Test retrieving infrastructure items
    for role, token in tokens.items():
        response = get_infrastructure(token)
        success = response.status_code == 200 and isinstance(response.json(), list)
        all_passed = all_passed and success
        print_test_result(f"Get all infrastructure as {role}", success, f"Status: {response.status_code}, Items: {len(response.json())}")
        
        # Test filtering by type
        if INFRASTRUCTURE_TYPES:
            type_filter = random.choice(INFRASTRUCTURE_TYPES)
            response = get_infrastructure(token, {"type": type_filter})
            success = response.status_code == 200 and all(item["type"] == type_filter for item in response.json())
            all_passed = all_passed and success
            print_test_result(f"Filter infrastructure by type as {role}", success, f"Status: {response.status_code}, Type: {type_filter}")
        
        # Test filtering by city
        if role in created_items and "city" in created_items[role]:
            city_filter = created_items[role]["city"]
            response = get_infrastructure(token, {"city": city_filter})
            success = response.status_code == 200 and all(item["city"] == city_filter for item in response.json())
            all_passed = all_passed and success
            print_test_result(f"Filter infrastructure by city as {role}", success, f"Status: {response.status_code}, City: {city_filter}")
    
    # Test updating infrastructure items
    for role, item in created_items.items():
        update_data = {
            "name": f"Updated {item['name']}",
            "status": random.choice(STATUSES),
            "condition": random.choice(CONDITIONS),
            "description": f"Updated description for {item['name']}"
        }
        
        response = update_infrastructure(tokens[role], item["id"], update_data)
        
        # Municipality users can only update in their city
        if role == "municipality" and item["city"] != USERS[role]["city"]:
            expected_success = False
        else:
            expected_success = True
        
        success = (response.status_code == 200) == expected_success
        all_passed = all_passed and success
        
        message = f"Status: {response.status_code}"
        if response.status_code == 200:
            message += f", Updated name: {response.json()['name']}"
        
        print_test_result(f"Update infrastructure as {role}", success, message)
    
    # Test deleting infrastructure items
    # We'll only delete one item to leave data for other tests
    if "ministry" in created_items:
        role = "ministry"
        item = created_items[role]
        
        response = delete_infrastructure(tokens[role], item["id"])
        success = response.status_code == 200
        all_passed = all_passed and success
        print_test_result(f"Delete infrastructure as {role}", success, f"Status: {response.status_code}")
    
    return all_passed, created_items

def test_role_based_access(tokens, created_items):
    print_test_header("Role-based Access Control")
    
    all_passed = True
    
    # Test municipality user can only see their city's data
    if "municipality" in tokens and "municipality" in created_items:
        municipality_city = USERS["municipality"]["city"]
        
        # Get all infrastructure as municipality user
        response = get_infrastructure(tokens["municipality"])
        
        if response.status_code == 200:
            # Check if all returned items are from the municipality's city
            city_match = all(item["city"] == municipality_city for item in response.json())
            success = city_match
            all_passed = all_passed and success
            print_test_result("Municipality user city restriction", success, 
                             f"All {len(response.json())} items are from {municipality_city}: {city_match}")
        else:
            all_passed = False
            print_test_result("Municipality user city restriction", False, 
                             f"Failed to get infrastructure: {response.status_code}")
    
    # Test directorate user can see data from multiple cities
    if "directorate" in tokens and "ministry" in tokens:
        # Create items in different cities as ministry user
        ministry_token = tokens["ministry"]
        directorate_token = tokens["directorate"]
        
        # Get all infrastructure as directorate user
        response = get_infrastructure(directorate_token)
        
        if response.status_code == 200:
            # Check if directorate can see items from different cities
            cities = set(item["city"] for item in response.json())
            success = len(cities) > 0  # Should be able to see at least one city
            all_passed = all_passed and success
            print_test_result("Directorate user access", success, 
                             f"Directorate user can see data from {len(cities)} cities")
        else:
            all_passed = False
            print_test_result("Directorate user access", False, 
                             f"Failed to get infrastructure: {response.status_code}")
    
    # Test ministry user can see all data
    if "ministry" in tokens:
        # Get all infrastructure as ministry user
        response = get_infrastructure(tokens["ministry"])
        
        if response.status_code == 200:
            # Ministry should be able to see all items
            success = len(response.json()) > 0
            all_passed = all_passed and success
            print_test_result("Ministry user access", success, 
                             f"Ministry user can see {len(response.json())} infrastructure items")
        else:
            all_passed = False
            print_test_result("Ministry user access", False, 
                             f"Failed to get infrastructure: {response.status_code}")
    
    return all_passed

def test_geojson_api(tokens):
    print_test_header("GeoJSON API for Map Visualization")
    
    all_passed = True
    
    # Test GeoJSON endpoint for each role
    for role, token in tokens.items():
        response = get_geojson(token)
        
        success = response.status_code == 200 and "type" in response.json() and response.json()["type"] == "FeatureCollection"
        all_passed = all_passed and success
        
        message = f"Status: {response.status_code}"
        if success:
            features = response.json().get("features", [])
            message += f", Features: {len(features)}"
            
            # Validate coordinates format
            if features:
                valid_coords = all(
                    len(feature["geometry"]["coordinates"]) == 2 and
                    isinstance(feature["geometry"]["coordinates"][0], (int, float)) and
                    isinstance(feature["geometry"]["coordinates"][1], (int, float))
                    for feature in features
                )
                success = valid_coords
                all_passed = all_passed and success
                message += f", Valid coordinates: {valid_coords}"
        
        print_test_result(f"Get GeoJSON as {role}", success, message)
        
        # Test filtering by type
        if INFRASTRUCTURE_TYPES:
            type_filter = random.choice(INFRASTRUCTURE_TYPES)
            response = get_geojson(token, {"type": type_filter})
            
            success = response.status_code == 200 and "features" in response.json()
            all_passed = all_passed and success
            
            if success and response.json()["features"]:
                type_match = all(feature["properties"]["type"] == type_filter for feature in response.json()["features"])
                success = type_match
                all_passed = all_passed and success
                print_test_result(f"Filter GeoJSON by type as {role}", success, 
                                f"Status: {response.status_code}, Type match: {type_match}")
            else:
                print_test_result(f"Filter GeoJSON by type as {role}", success, 
                                f"Status: {response.status_code}, No features returned")
    
    return all_passed

def test_analytics_api(tokens):
    print_test_header("Analytics Dashboard API")
    
    all_passed = True
    
    # Test analytics endpoint for each role
    for role, token in tokens.items():
        response = get_analytics(token)
        
        success = response.status_code == 200
        all_passed = all_passed and success
        
        message = f"Status: {response.status_code}"
        if success:
            # Check for required analytics sections
            data = response.json()
            has_type_dist = "type_distribution" in data
            has_status_dist = "status_distribution" in data
            has_condition_dist = "condition_distribution" in data
            
            section_success = has_type_dist and has_status_dist and has_condition_dist
            all_passed = all_passed and section_success
            
            message += f", Has type distribution: {has_type_dist}"
            message += f", Has status distribution: {has_status_dist}"
            message += f", Has condition distribution: {has_condition_dist}"
        
        print_test_result(f"Get analytics as {role}", success, message)
    
    return all_passed

def test_cities_api():
    print_test_header("Cities API")
    
    response = get_cities()
    
    success = response.status_code == 200 and isinstance(response.json(), list)
    
    message = f"Status: {response.status_code}"
    if success:
        message += f", Cities: {len(response.json())}"
    
    return print_test_result("Get cities", success, message)

def run_all_tests():
    print("\n\n" + "=" * 100)
    print("STARTING COMPREHENSIVE BACKEND API TESTS FOR SYRIAN INFRASTRUCTURE GIS SYSTEM")
    print("=" * 100)
    
    test_results = {}
    
    # Test root endpoint
    test_results["Root Endpoint"] = test_root_endpoint()
    
    # Test authentication
    auth_success, tokens, user_ids = test_authentication()
    test_results["Authentication System"] = auth_success
    
    if tokens:
        # Test infrastructure management
        infra_success, created_items = test_infrastructure_management(tokens)
        test_results["Infrastructure Data Management"] = infra_success
        
        # Test role-based access
        rbac_success = test_role_based_access(tokens, created_items)
        test_results["Role-based Access Control"] = rbac_success
        
        # Test GeoJSON API
        geojson_success = test_geojson_api(tokens)
        test_results["GeoJSON API"] = geojson_success
        
        # Test analytics API
        analytics_success = test_analytics_api(tokens)
        test_results["Analytics Dashboard API"] = analytics_success
    
    # Test cities API
    cities_success = test_cities_api()
    test_results["Cities API"] = cities_success
    
    # Print summary
    print("\n\n" + "=" * 100)
    print("TEST SUMMARY")
    print("=" * 100)
    
    all_passed = True
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        all_passed = all_passed and result
    
    print("\n" + "=" * 100)
    if all_passed:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉")
    else:
        print("❌ SOME TESTS FAILED. PLEASE CHECK THE DETAILS ABOVE. ❌")
    print("=" * 100 + "\n")
    
    return all_passed, test_results

if __name__ == "__main__":
    run_all_tests()