import requests
import os
import argparse
import sys


def run_test(api_url, api_key, file_path):
    print("Iniciando prueba de integración...")
    print(f"Target: {api_url}")
    print(f"Archivo: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        sys.exit(1)

    headers = {"x-api-key": api_key}

    print("\n[1/2] Probando POST /reports (Upload)...")
    try:
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            response = requests.post(
                f"{api_url}/reports",
                headers=headers,
                files=files,
                timeout=300,  
            )

        if response.status_code != 201:
            print(f"Falló POST. Status: {response.status_code}")
            print(f"Detalle: {response.text}")
            sys.exit(1)

        data = response.json()
        report_id = data.get("report_id")

        if not report_id:
            print("POST exitoso pero no se recibió report_id")
            sys.exit(1)

        print(f"POST Exitoso! ID Reporte: {report_id}")

    except Exception as e:
        print(f"Error de conexión en POST: {e}")
        sys.exit(1)


    print(f"\n[2/2] Probando GET /reports/{report_id}...")
    try:
        response_get = requests.get(
            f"{api_url}/reports/{report_id}",
            headers=headers,
            timeout=60,
        )

        if response_get.status_code != 200:
            print(f"Falló GET. Status: {response_get.status_code}")
            print(response_get.text)
            sys.exit(1)

        report_data = response_get.json()["report"]

        patient_name = report_data["patient"]["name"]
        images = report_data.get("image_urls", [])

        print("GET Exitoso!")
        print(f"Paciente: {patient_name}")
        print(f"Imágenes procesadas: {len(images)}")

    except Exception as e:
        print(f"Error de conexión en GET: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test de integración para Diagnovet API"
    )

    parser.add_argument(
        "--url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="URL base de la API",
    )
    parser.add_argument(
        "--key",
        default=os.getenv("API_KEY", "secret123"),
        help="API Key para autenticación",
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Ruta al archivo PDF de prueba",
    )

    args = parser.parse_args()

    run_test(args.url, args.key, args.file)
