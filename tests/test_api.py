import requests
import os
import argparse
import sys


def run_test(api_url, api_key, file_path):
    print("Starting integration test...")
    print(f"Target API: {api_url}")
    print(f"Test file: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: file '{file_path}' does not exist.")
        sys.exit(1)

    headers = {"x-api-key": api_key}

    print("\n[1/2] Testing POST /reports (Upload)...")
    try:
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            files = {
                "file": (filename, f, "application/pdf")
            }

            response = requests.post(
                f"{api_url}/reports",
                headers=headers,
                files=files,
                timeout=300  
            )

        if response.status_code != 201:
            print(f"POST failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        data = response.json()
        report_id = data.get("report_id")

        if not report_id:
            print("POST succeeded but no report_id was returned.")
            sys.exit(1)

        print(f"POST succeeded! Report ID: {report_id}")

    except Exception as e:
        print(f"POST connection error: {e}")
        sys.exit(1)

    print(f"\n[2/2] Testing GET /reports/{report_id}...")
    try:
        response_get = requests.get(
            f"{api_url}/reports/{report_id}",
            headers=headers,
            timeout=60
        )

        if response_get.status_code != 200:
            print(f"GET failed. Status: {response_get.status_code}")
            print(response_get.text)
            sys.exit(1)

        report_data = response_get.json().get("report")

        patient_name = report_data["patient"]["name"]
        images = report_data.get("image_urls", [])

        print("GET succeeded!")
        print(f"Retrieved patient: '{patient_name}'")
        print(f"Images processed: {len(images)}")

    except Exception as e:
        print(f"GET connection error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="End-to-End integration test for Diagnovet Backend API"
    )

    parser.add_argument(
        "--url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL of the API"
    )

    parser.add_argument(
        "--key",
        default=os.getenv("API_KEY", "secret123"),
        help="API Key used for authentication"
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Path to the PDF report used for testing"
    )

    args = parser.parse_args()

    run_test(args.url, args.key, args.file)
