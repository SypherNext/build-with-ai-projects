"""AI Resume Reviewer -- FastAPI web deployment of the reviewer.py CLI tool."""

import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Error: ANTHROPIC_API_KEY not set")
    sys.exit(1)

import anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Import your reviewer functions
from reviewer import analyze_resume, format_report

app = FastAPI(title="AI Resume Reviewer")


def extract_text_from_upload(file: UploadFile) -> str:
    content = file.file.read()
    if file.filename.endswith(".pdf"):
        import fitz
        doc = fitz.open(stream=content, filetype="pdf")
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
        return text
    return content.decode("utf-8")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
    <head><title>AI Resume Reviewer</title>
    <style>
      body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }
      textarea { width: 100%; padding: 0.5rem; margin: 0.5rem 0; font-family: monospace; }
      input[type=file] { margin: 0.5rem 0; }
      button { padding: 0.75rem 1.5rem; background: #007bff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
      #report { background: #f9f9f9; padding: 1.5rem; border-radius: 4px; margin-top: 1rem; white-space: pre-wrap; }
      .loading { display: none; }
    </style></head>
    <body>
      <h1>AI Resume Reviewer</h1>
      <form id="reviewForm">
        <h3>Resume</h3>
        <textarea name="resume" rows="10" placeholder="Paste resume text or upload a file below"></textarea>
        <input type="file" id="resumeFile" accept=".txt,.pdf,.md" />
        <h3>Job Description</h3>
        <textarea name="jd" rows="8" placeholder="Paste job description here" required></textarea>
        <br/>
        <button type="submit">Review Resume</button>
        <div class="loading" id="loading">Analysing... this takes about 5 seconds</div>
      </form>
      <div id="report"></div>
      <script>
        document.getElementById('resumeFile').onchange = async (e) => {
          const file = e.target.files[0];
          if (!file) return;
          const text = await file.text();
          document.querySelector('textarea[name="resume"]').value = text;
        };
        document.getElementById('reviewForm').onsubmit = async (e) => {
          e.preventDefault();
          document.getElementById('loading').style.display = 'block';
          const form = new FormData(e.target);
          const res = await fetch('/review', { method: 'POST', body: form });
          const data = await res.json();
          document.getElementById('loading').style.display = 'none';
          document.getElementById('report').innerText = data.report;
        };
      </script>
    </body>
    </html>
    """


@app.post("/review")
async def review(
    resume: str = Form(...),
    jd: str = Form(...)
):
    if not resume.strip() or not jd.strip():
        raise HTTPException(400, "Both resume and job description are required")
    analysis = analyze_resume(resume, jd)
    report = format_report(analysis)
    return {"report": report, "score": analysis.get("overall_score")}
