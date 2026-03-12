import os
import requests
from dotenv import load_dotenv

load_dotenv()

def list_articles_in_category():
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    category_id = os.getenv("DOCUMENT360_CATEGORY_ID")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    if not api_token or not category_id:
        print("Error: Required environment variables not found in .env")
        return

    # Endpoint to get articles in a category
    url = f"{base_url}/v2/Categories/{category_id}/articles"
    headers = {"api_token": api_token}

    print(f"Listing articles in category {category_id}...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        articles = response.json().get("data", [])
        
        print(f"\n--- SUCCESS: {len(articles)} ARTICLE(S) FOUND ---")
        for art in articles:
            print(f"- Title: {art.get('title')}")
            print(f"  ID: {art.get('id')}")
            print(f"  Slug: {art.get('slug')}")
            print("-" * 30)
        
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print("Response:", e.response.text)

if __name__ == "__main__":
    list_articles_in_category()
