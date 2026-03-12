import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def verify_article(article_id):
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    if not api_token:
        print("Error: DOCUMENT360_API_TOKEN not found in .env")
        return

    # Updated endpoint with language code (e.g., /en)
    url = f"{base_url}/v2/Articles/{article_id}/en"
    headers = {"api_token": api_token}

    print(f"Fetching article {article_id} from Document360...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", {})
        
        with open("article_response.json", "w") as f:
            json.dump(data, f, indent=2)
        print("\nFull response saved to article_response.json")
        
        print("\n--- VERIFICATION SUCCESS ---")
        print(f"Title: {data.get('title')}")
        print(f"Article ID: {data.get('id')}")
        print(f"Status: {data.get('status')} (0=Draft)")
        print("\n--- HTML CONTENT FROM SERVER ---")
        print(data.get('content'))
        
    except Exception as e:
        print(f"Error verifying article: {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)

if __name__ == "__main__":
    # Your Leave article ID
    leave_article_id = "a5d5dd08-e2b1-498b-9e28-3bd4cb758181"
    verify_article(leave_article_id)
