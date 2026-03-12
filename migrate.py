import os
import sys
import mammoth
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def convert_docx_to_html(docx_path):
    """
    Converts a .docx file to HTML using mammoth.
    Mammoth automatically extracts structure:
    - Heading 1 -> <h1>
    - Heading 2 -> <h2>
    - Paragraphs -> <p>
    - Bullet/Numbered Lists -> <ul>/<ol>
    - Tables -> <table>
    - Hyperlinks -> <a>
    """
    try:
        with open(docx_path, "rb") as docx_file:
            # We use mammoth's default mapping which satisfies the assignment requirements
            result = mammoth.convert_to_html(docx_file)
            html = result.value
            messages = result.messages
            
            if messages:
                print(f"[*] Mammoth Info: {messages}")
            
            return html
    except Exception as e:
        print(f"[!] Error converting document: {e}")
        return None

def upload_to_document360(html_content, title):
    """Uploads HTML content to Document360 via the Article Creation API."""
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    user_id = os.getenv("DOCUMENT360_USER_ID")
    project_version_id = os.getenv("DOCUMENT360_PROJECT_VERSION_ID")
    category_id = os.getenv("DOCUMENT360_CATEGORY_ID")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    if not all([api_token, user_id, project_version_id, category_id]):
        print("[!] Error: Missing required environment variables in .env")
        return False

    url = f"{base_url}/v2/Articles"
    
    headers = {
        "api_token": api_token,
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "content": html_content,
        "category_id": category_id,
        "project_version_id": project_version_id,
        "user_id": user_id,
        "order": 0,
        "content_type": 1  # 1 for WYSIWYG/HTML editor
    }

    try:
        print(f"[*] Sending POST request to {url}...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        print("[+] Successfully migrated to Document360!")
        print(f"[*] API Response: {response.json()}")
        return True
    except requests.exceptions.HTTPError as err:
        print(f"[!] API HTTP Error: {err}")
        print(f"[*] Response Body: {response.text}")
    except Exception as err:
        print(f"[!] General Error: {err}")
    
    return False

def main():
    print("=== Document360 Migration Toolkit ===")
    
    if len(sys.argv) < 2:
        print("Usage: python3 migrate.py <path_to_docx>")
        sys.exit(1)

    docx_path = sys.argv[1]
    if not os.path.exists(docx_path):
        print(f"[!] Error: File '{docx_path}' not found.")
        sys.exit(1)

    print(f"[*] Processing '{docx_path}'...")
    html_output = convert_docx_to_html(docx_path)

    if html_output:
        # Save HTML for verification as required by deliverables
        output_html_path = "output.html"
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(html_output)
        print(f"[+] Clean HTML generated and saved to '{output_html_path}'")

        # Derive title from filename
        title = os.path.splitext(os.path.basename(docx_path))[0].replace("_", " ").title()
        
        # Execute migration if API credentials are present
        if os.getenv("DOCUMENT360_API_TOKEN"):
            print(f"[*] Attempting migration for topic: '{title}'...")
            upload_to_document360(html_output, title)
        else:
            print("[!] Skipping upload: No API Token found in environment.")
    else:
        print("[!] Conversion failed. Please check the document format.")

if __name__ == "__main__":
    main()
