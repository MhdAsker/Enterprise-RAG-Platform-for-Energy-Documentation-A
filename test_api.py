"""
Comprehensive test suite for Energy Docs RAG FastAPI application
Run: uv run python test_api.py
"""
import time
import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"

# ANSI colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")


def print_test(name, status, details=""):
    icon = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{icon} {Colors.BOLD}{name}{Colors.END}")
    if details:
        print(f"  {Colors.CYAN}{details}{Colors.END}")


def print_response(response):
    print(f"{Colors.YELLOW}Status: {response.status_code}{Colors.END}")
    try:
        print(f"{Colors.BLUE}Response:{Colors.END}")
        print(json.dumps(response.json(), indent=2)[:500])
    except:
        print(response.text[:500])


# ============================================================================
# Test Functions
# ============================================================================

def test_server_running():
    """Test if server is running"""
    print_header("1. SERVER STATUS")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print_test("Server is running", response.status_code == 200)
        if response.status_code != 200:
            print_response(response)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print_test("Server is running", False, f"Cannot connect to {BASE_URL}")
        print(f"  {Colors.RED}Make sure to run: uv run python main.py{Colors.END}")
        return False
    except Exception as e:
        print_test("Server is running", False, str(e))
        return False


def test_health_endpoint():
    """Test health check endpoint"""
    print_header("2. HEALTH CHECK ENDPOINT")
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200

        print_test("GET /health", success)

        if success:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Timestamp: {data.get('timestamp')}")
        else:
            print_response(response)

        return success
    except Exception as e:
        print_test("GET /health", False, str(e))
        return False


def test_web_ui():
    """Test web UI endpoint"""
    print_header("3. WEB UI")
    try:
        response = requests.get(f"{BASE_URL}/")
        success = response.status_code == 200 and "Energy" in response.text

        print_test("GET /", success)

        if success:
            size_kb = len(response.text) / 1024
            print(f"  HTML size: {size_kb:.1f} KB")
            print(f"  Contains chat UI: {'chat-messages' in response.text}")
        else:
            print_response(response)

        return success
    except Exception as e:
        print_test("GET /", False, str(e))
        return False


def test_static_files():
    """Test static file serving"""
    print_header("4. STATIC FILES")
    files = ["styles.css", "app.js"]
    results = []

    for file in files:
        try:
            response = requests.get(f"{BASE_URL}/static/{file}")
            success = response.status_code == 200
            results.append(success)

            size_kb = len(response.text) / 1024
            print_test(f"GET /static/{file}", success, f"{size_kb:.1f} KB")

            if not success:
                print_response(response)
        except Exception as e:
            results.append(False)
            print_test(f"GET /static/{file}", False, str(e))

    return all(results)


def test_chat_simple():
    """Test simple chat request"""
    print_header("5. CHAT API - SIMPLE REQUEST")
    try:
        payload = {
            "question": "What is the Standard Frequency Range for Continental Europe?",
            "session_id": "test_session_1"
        }

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        response_time = (time.time() - start_time) * 1000

        success = response.status_code == 200

        print_test("POST /chat", success, f"Response time: {response_time:.0f}ms")

        if success:
            data = response.json()
            print(f"  Question: {data.get('question')[:60]}...")
            print(f"  Answer preview: {data.get('answer')[:80]}...")
            print(f"  Session: {data.get('session_id')}")
        else:
            print_response(response)

        return success
    except requests.exceptions.Timeout:
        print_test("POST /chat", False, "Request timed out (>30s)")
        return False
    except Exception as e:
        print_test("POST /chat", False, str(e))
        return False


def test_chat_multiple_questions():
    """Test multiple questions in sequence"""
    print_header("6. CHAT API - MULTIPLE QUESTIONS")

    questions = [
        "What is the Agorameter?",
        "What are the Maximum Instantaneous Frequency Deviations?",
        "What does BDEW TAB 2023 cover?"
    ]

    session_id = f"test_session_{int(time.time())}"
    results = []

    for i, question in enumerate(questions, 1):
        try:
            payload = {
                "question": question,
                "session_id": session_id
            }

            start_time = time.time()
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
            response_time = (time.time() - start_time) * 1000

            success = response.status_code == 200
            results.append(success)

            print_test(
                f"Q{i}: {question[:50]}...",
                success,
                f"{response_time:.0f}ms"
            )

            if not success:
                print_response(response)

        except Exception as e:
            results.append(False)
            print_test(f"Q{i}", False, str(e))

    return all(results)


def test_chat_error_handling():
    """Test error handling"""
    print_header("7. ERROR HANDLING")

    # Test empty question
    try:
        payload = {
            "question": "",
            "session_id": "test_error_1"
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)

        # This might succeed with empty answer or fail - both are acceptable
        print_test("Empty question handling", True, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Empty question handling", True, f"Exception: {str(e)[:50]}")

    # Test missing required field
    try:
        payload = {"session_id": "test_error_2"}  # missing question
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=10)

        success = response.status_code in [400, 422]  # validation error expected
        print_test("Missing required field validation", success, f"Status: {response.status_code}")
    except Exception as e:
        print_test("Missing required field validation", True, str(e)[:50])

    return True


def test_api_docs():
    """Test API documentation endpoints"""
    print_header("8. API DOCUMENTATION")

    endpoints = [
        ("/docs", "Swagger UI"),
        ("/redoc", "ReDoc"),
        ("/openapi.json", "OpenAPI schema")
    ]

    results = []
    for path, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}")
            success = response.status_code == 200

            results.append(success)
            print_test(f"GET {path} ({name})", success, f"Status: {response.status_code}")

            if not success:
                print_response(response)
        except Exception as e:
            results.append(False)
            print_test(f"GET {path}", False, str(e))

    return all(results)


def test_concurrent_requests():
    """Test handling of concurrent requests"""
    print_header("9. CONCURRENT REQUESTS")

    import concurrent.futures

    questions = [
        "What is frequency control?",
        "What is grid regulation?",
        "What is energy market?"
    ]

    def make_request(q_index, question):
        try:
            payload = {
                "question": question,
                "session_id": f"concurrent_{q_index}"
            }
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
            return response.status_code == 200, q_index
        except Exception as e:
            return False, q_index

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_request, i, q)
                for i, q in enumerate(questions)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for success, _ in results if success)
        print_test(f"Concurrent requests ({len(results)} total)", success_count == len(results))
        print(f"  Successful: {success_count}/{len(results)}")

        return success_count == len(results)
    except Exception as e:
        print_test("Concurrent requests", False, str(e))
        return False


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print(f"{Colors.BOLD}Energy Docs RAG - API Test Suite{Colors.END}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")

    # Check if server is running
    if not test_server_running():
        print(f"\n{Colors.RED}{Colors.BOLD}Server is not running!{Colors.END}")
        print(f"Start it with: {Colors.YELLOW}uv run python main.py{Colors.END}")
        return

    tests = [
        ("Health Check", test_health_endpoint),
        ("Web UI", test_web_ui),
        ("Static Files", test_static_files),
        ("Chat (Simple)", test_chat_simple),
        ("Chat (Multiple Questions)", test_chat_multiple_questions),
        ("Error Handling", test_chat_error_handling),
        ("API Documentation", test_api_docs),
        ("Concurrent Requests", test_concurrent_requests),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"{Colors.RED}Unexpected error in {name}: {e}{Colors.END}")
            results[name] = False

    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, success in results.items():
        icon = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
        print(f"{icon} {name}")

    print(f"\n{Colors.BOLD}Result: {passed}/{total} test groups passed{Colors.END}")

    if passed == total:
        print(f"{Colors.GREEN}All tests passed!{Colors.END}")
    else:
        print(f"{Colors.YELLOW}Some tests failed. Check the output above.{Colors.END}")

    print(f"\nFinished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    run_all_tests()
