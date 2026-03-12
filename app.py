import os
import mammoth
import requests
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- REUSED LOGIC FROM migrate.py ---

def convert_docx_to_html(docx_path):
    try:
        with open(docx_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            return result.value, result.messages
    except Exception as e:
        return None, [str(e)]

def upload_to_document360(html_content, title):
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    user_id = os.getenv("DOCUMENT360_USER_ID")
    project_version_id = os.getenv("DOCUMENT360_PROJECT_VERSION_ID")
    category_id = os.getenv("DOCUMENT360_CATEGORY_ID")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")

    if not all([api_token, user_id, project_version_id, category_id]):
        return False, "Missing environment variables in .env"

    url = f"{base_url}/v2/Articles"
    headers = {"api_token": api_token, "Content-Type": "application/json"}
    payload = {
        "title": title,
        "content": html_content,
        "category_id": category_id,
        "project_version_id": project_version_id,
        "user_id": user_id,
        "order": 0,
        "content_type": 1
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True, response.json()
    except Exception as e:
        return False, str(e)

# --- UI TEMPLATE ---

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuMigrate | Document360 Migration Specialist</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #000000;
            --primary-glow: rgba(0, 0, 0, 0.1);
            --secondary: #475569;
            --bg: #ffffff;
            --card-bg: #ffffff;
            --text-main: #000000;
            --text-dim: #64748b;
            --success: #10b981;
            --error: #ef4444;
            --border: #e2e8f0;
            --glass: #f8fafc;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            margin: 0;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }

        .header {
            text-align: center;
            margin-bottom: 4rem;
            animation: fadeIn 0.8s ease-out;
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 1rem;
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 99px;
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--secondary);
            margin-bottom: 1.5rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        h1 {
            font-size: 3rem;
            font-weight: 800;
            margin: 0;
            color: var(--text-main);
            letter-spacing: -0.04em;
        }

        .subtitle {
            color: var(--text-dim);
            font-size: 1rem;
            margin-top: 0.75rem;
            font-weight: 400;
        }

        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1.25rem;
            padding: 3rem;
            box-shadow: 0 4px 20px -4px rgba(0, 0, 0, 0.05);
            animation: fadeIn 1s ease-out;
        }

        .upload-zone {
            border: 2px dashed var(--border);
            border-radius: 1rem;
            padding: 5rem 2rem;
            text-align: center;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
            background: #fafafa;
        }

        .upload-zone:hover {
            border-color: var(--primary);
            background: #f4f4f5;
        }

        .upload-zone svg {
            color: var(--primary);
            margin-bottom: 1.5rem;
            opacity: 0.8;
        }

        input[type="file"] {
            position: absolute;
            inset: 0;
            opacity: 0;
            cursor: pointer;
        }

        .section-box {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 2rem;
            display: flex;
            flex-direction: column;
        }

        .section-label {
            font-size: 0.75rem;
            font-weight: 800;
            color: var(--text-main);
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .scroll-area {
            max-height: 600px;
            overflow-y: auto;
        }

        .scroll-area::-webkit-scrollbar { width: 4px; }
        .scroll-area::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 10px; }

        .btn-migrate {
            background: var(--primary);
            color: #ffffff;
            padding: 1.25rem 2rem;
            border-radius: 0.75rem;
            border: none;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .btn-migrate:hover {
            background: #27272a;
            transform: translateY(-1px);
        }

        .loading-spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 50%;
            border-top-color: #ffffff;
            animation: spin 0.6s linear infinite;
            display: none;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* Preview Styles */
        .preview-content { color: #18181b; line-height: 1.7; font-size: 1rem; }
        .preview-content h1 { color: #000000; font-size: 2rem; border-bottom: 2px solid #f4f4f5; padding-bottom: 1rem; margin-bottom: 2rem; background: none; -webkit-text-fill-color: initial; }
        .preview-content h2 { color: #27272a; font-size: 1.5rem; margin-top: 2.5rem; }
        .preview-content p { margin: 1.25rem 0; }
        .preview-content table { width: 100%; border-collapse: collapse; margin: 2rem 0; border: 1px solid #e2e8f0; }
        .preview-content th, .preview-content td { border: 1px solid #e2e8f0; padding: 12px 16px; text-align: left; }
        .preview-content th { background: #f8fafc; font-weight: 700; color: #000000; }
        .preview-content ul, .preview-content ol { padding-left: 2rem; }

        #toast {
            position: fixed;
            bottom: 3rem;
            left: 50%;
            transform: translateX(-50%);
            padding: 1rem 2rem;
            border-radius: 0.5rem;
            font-weight: 700;
            display: none;
            z-index: 100;
            font-size: 0.85rem;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1);
        }

        .toast-success { background: #000000; color: #ffffff; }
        .toast-error { background: #dc2626; color: #ffffff; }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <span class="badge">Technical Assignment • Migration Module</span>
            <h1>DocuMigrate</h1>
            <p class="subtitle">Clean Word-to-HTML Conversion & Synchronization</p>
        </header>

        <main class="glass-card">
            <div class="upload-zone" id="drop-zone">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <h3 style="margin: 0.5rem 0; font-weight: 700;">Drop Document</h3>
                <p style="color: var(--text-dim); font-size: 0.9rem;">Microsoft Word (.docx)</p>
                <input type="file" id="file-input" accept=".docx">
            </div>

            <div id="migration-interface" style="display: none;">
                <!-- Live Content Preview -->
                <div class="section-box" style="margin-top: 3rem;">
                    <div class="section-label">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        Content Preview
                    </div>
                    <div class="scroll-area preview-content" id="preview-content"></div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 2rem;">
                    <button id="download-btn" class="btn-migrate" style="background: #ffffff; color: #000000; border: 1px solid #e2e8f0; margin-top: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                        <span>Download</span>
                    </button>
                    <button id="migrate-btn" class="btn-migrate" style="margin-top: 0;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14M22 4L12 14.01l-3-3"/></svg>
                        <span>Sync with Document360</span>
                        <div class="loading-spinner" id="spinner"></div>
                    </button>
                </div>
            </div>
        </main>
    </div>

    <div id="toast"></div>

    <script>
        const fileInput = document.getElementById('file-input');
        const migrationInterface = document.getElementById('migration-interface');
        const previewContent = document.getElementById('preview-content');
        const migrateBtn = document.getElementById('migrate-btn');
        const downloadBtn = document.getElementById('download-btn');
        const spinner = document.getElementById('spinner');

        let currentHtml = '';
        let currentTitle = '';

        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.className = type === 'success' ? 'toast-success' : 'toast-error';
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 4000);
        }

        downloadBtn.addEventListener('click', async () => {
            if (!currentHtml) return;
            
            // 1. Browser Download
            const blob = new Blob([currentHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentTitle.toLowerCase().replace(/ /g, '_')}_output.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // 2. Server-side Save (Ensures visibility in project folder)
            try {
                await fetch('/save-local', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ html: currentHtml, filename: 'output.html' })
                });
                showToast('Downloaded! Also check your project folder for output.html');
            } catch (err) {
                showToast('Browser download started');
            }
        });

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/preview', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    currentHtml = data.html;
                    currentTitle = file.name.split('.')[0].replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    previewContent.innerHTML = data.html;

                    migrationInterface.style.display = 'block';
                    migrationInterface.scrollIntoView({ behavior: 'smooth' });
                } else {
                    showToast(data.error, 'error');
                }
            } catch (err) {
                showToast('Connection failed or file too large', 'error');
            }
        });

        migrateBtn.addEventListener('click', async () => {
            migrateBtn.disabled = true;
            spinner.style.display = 'block';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        html: currentHtml,
                        title: currentTitle
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    showToast('Migration Complete! Article created in Document360.');
                    migrateBtn.innerHTML = '<span>Successfully Migrated</span>';
                    migrateBtn.style.background = 'var(--success)';
                } else {
                    showToast(data.error, 'error');
                }
            } catch (err) {
                showToast('Critical API Failure', 'error');
            } finally {
                spinner.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/preview', methods=['POST'])
def preview():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"})

    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)

    html, messages = convert_docx_to_html(path)
    
    # Auto-save a copy to project root for easy access
    try:
        with open("output.html", "w", encoding="utf-8") as f:
            f.write(html)
    except:
        pass

    return jsonify({"success": True, "html": html})

@app.route('/save-local', methods=['POST'])
def save_local():
    data = request.json
    html = data.get('html')
    filename = data.get('filename', 'output.html')
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/upload', methods=['POST'])
def upload():
    data = request.json
    html = data.get('html')
    title = data.get('title', 'Untitled Article').replace("_", " ").title()
    
    success, result = upload_to_document360(html, title)
    if success:
        return jsonify({"success": True, "data": result})
    else:
        return jsonify({"success": False, "error": str(result)})

@app.route('/article/<article_id>')
def get_article(article_id):
    api_token = os.getenv("DOCUMENT360_API_TOKEN")
    base_url = os.getenv("DOCUMENT360_BASE_URL", "https://apihub.document360.io")
    
    url = f"{base_url}/v2/Articles/{article_id}/en"
    headers = {"api_token": api_token}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify({"success": True, "data": response.json().get("data", {})})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
