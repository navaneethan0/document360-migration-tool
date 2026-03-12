import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_project_versions():
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    if not api_token:
        print("Error: DOCUMENT360_API_TOKEN not found in .env")
        return None

    url = f"{base_url}/v2/ProjectVersions"
    headers = {"api_token": api_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        versions = response.json().get("data", [])
        print("\n--- Project Versions ---")
        for v in versions:
            print(f"ID: {v['id']} | Name: {v['version_code_name']} (Default: {v['is_main_version']})")
        return versions
    except Exception as e:
        print(f"Error fetching project versions: {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)
        return None

def list_categories(project_version_id):
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    url = f"{base_url}/v2/ProjectVersions/{project_version_id}/categories"
    headers = {"api_token": api_token}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        categories = response.json().get("data", [])
        print(f"\n--- Categories for Version {project_version_id} ---")
        for c in categories:
            print(f"ID: {c['id']} | Name: {c['name']}")
        return categories
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return None

if __name__ == "__main__":
    versions = list_project_versions()
    if versions:
        # Default to the first version found for category listing if none specified
        first_id = versions[0]['id']
        list_categories(first_id)
        print("\nTIP: Copy the ID you need and paste it into your .env file.")
