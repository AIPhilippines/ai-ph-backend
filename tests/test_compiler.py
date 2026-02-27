import requests
import json
import time

BASE_URL = "http://localhost:20000/api/v1"

def test_successful_execution():
    print("Testing successful execution...")
    payload = {"code": "print('Hello, AI PH!')"}
    response = requests.post(f"{BASE_URL}/compile", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert "Hello, AI PH!" in response.json()["stdout"]

def test_syntax_error():
    print("\nTesting syntax error...")
    payload = {"code": "print('Hello'"}
    response = requests.post(f"{BASE_URL}/compile", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["exit_code"] != 0
    assert "SyntaxError" in response.json()["stderr"]

def test_timeout():
    print("\nTesting timeout...")
    payload = {"code": "import time\nwhile True: time.sleep(1)"}
    # This should trigger the default 5s timeout
    start = time.time()
    response = requests.post(f"{BASE_URL}/compile", json=payload)
    duration = time.time() - start
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"Actual Duration: {duration}s")
    assert response.status_code == 200
    assert response.json()["error"] == "Execution timed out"

if __name__ == "__main__":
    try:
        test_successful_execution()
        test_syntax_error()
        test_timeout()
        print("\nAll local tests passed! (Assuming server is running)")
    except Exception as e:
        print(f"\nTests failed: {e}")
        print("Make sure the server is running on http://localhost:20000")
