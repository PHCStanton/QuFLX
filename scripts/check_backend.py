import requests
import sys

BASE_URL = "http://localhost:3001"


def check_health():
    print("[Check] /health endpoint")
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    r.raise_for_status()
    print(r.json())


def check_available_csv():
    print("[Check] /api/available-csv-files endpoint")
    r = requests.get(f"{BASE_URL}/api/available-csv-files", timeout=10)
    r.raise_for_status()
    print({"count": r.json().get("count"), "sample": r.json().get("files", [])[:3]})


def main():
    try:
        check_health()
        check_available_csv()
        print("[OK] Backend basic checks passed")
    except Exception as e:
        print("[ERROR] Backend checks failed:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()