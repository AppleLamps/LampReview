import os
import io
import zipfile
import json
import time
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="AI-Powered Code Review with Gemini 2.5 (OpenRouter)")

# Allow CORS for all origins (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_EXTS = (".py", ".js", ".java", ".ts", ".go", ".rb", ".php", ".cs", ".c", ".cpp", ".h", ".hpp", ".html", ".htm", ".css", ".sql", ".yaml", ".yml", ".json", ".xml", ".md", ".sh", ".bat", ".ps1")
MAX_CONTENT_SIZE = 50 * 1024 * 1024  # 50 MB total
MAX_FILE_SIZE = 50 * 1024 * 1024     # 50 MB per file


def is_supported_file(filename: str) -> bool:
    return filename.lower().endswith(SUPPORTED_EXTS)


def construct_prompt(code_contents: List[dict]) -> str:
    prompt_parts = [
        """# Code Review Request\n\nYou are an expert software engineer conducting a comprehensive code review. I'll provide you with code files to analyze. Take your time to think through each step of the analysis process.\n\n## Thinking Process:\nFollow these steps in your analysis:\n\n1. **Initial Assessment**:\n   - First, understand what each file does and its purpose in the overall system\n   - Identify the programming language and frameworks used\n   - Note the general structure and organization patterns\n\n2. **Deep Analysis** (for each file):\n   - Examine the code structure and flow\n   - Identify functions, classes, and their relationships\n   - Look for design patterns or architectural approaches\n   - Check for code smells and anti-patterns\n   - Assess error handling and edge cases\n   - Evaluate security considerations\n   - Consider performance implications\n   - Review adherence to language/framework best practices\n\n3. **Issue Prioritization**:\n   - CRITICAL: Issues that could lead to security breaches, data loss, or system failures\n   - HIGH: Significant problems affecting functionality, maintainability, or performance\n   - MEDIUM: Issues that should be addressed but don't immediately impact system operation\n   - LOW: Minor improvements, style suggestions, or documentation enhancements\n\n4. **Recommendation Formulation**:\n   - For each issue, develop a specific, actionable recommendation\n   - Where appropriate, provide code examples showing how to implement improvements\n   - Consider trade-offs between different approaches\n   - Ensure recommendations align with modern best practices\n\n## Output Format:\n1. **Executive Summary** (2-3 sentences providing an overall assessment)\n2. **File-by-File Analysis**:\n   - Purpose and role of the file\n   - Strengths and good practices identified\n   - Issues found (organized by priority)\n   - Specific recommendations with code examples where helpful\n3. **Overall Recommendations**:\n   - Cross-cutting concerns\n   - Architectural suggestions\n   - Next steps for improvement\n\nBalance criticism with recognition of good practices. Focus on providing actionable insights rather than just identifying problems.\n""",
        "\n\n---\n\n"
    ]
    for item in code_contents:
        prompt_parts.append(f"Filename: {item['filename']}\n\n```\n{item['content']}\n```\n\n---\n\n")
    return "".join(prompt_parts)


@app.post("/analyze")
async def analyze_code(
    files: List[UploadFile] = File(..., description="Code files or a zip archive"),
    api_key: Optional[str] = Form(None)
):
    """
    Accepts code files (or a zip), an optional OpenRouter API key, and returns a code review.
    """
    env_api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        api_key = env_api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenRouter API key is required.")

    code_contents = []
    total_content_size = 0
    warnings = []

    for uploaded_file in files:
        filename = uploaded_file.filename
        if filename.lower().endswith('.zip'):
            try:
                zip_bytes = await uploaded_file.read()
                with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
                    for zip_info in z.infolist():
                        if zip_info.is_dir():
                            continue
                        if is_supported_file(zip_info.filename):
                            try:
                                file_content = z.read(zip_info.filename).decode("utf-8", errors="replace")
                                file_size = len(file_content)
                                if total_content_size + file_size > MAX_CONTENT_SIZE:
                                    warnings.append(f"File '{zip_info.filename}' skipped due to total content size limits.")
                                    continue
                                if file_size > MAX_FILE_SIZE:
                                    truncated_content = file_content[:MAX_FILE_SIZE]
                                    truncated_content += f"\n\n... [Content truncated - file is {file_size} bytes, showing first {MAX_FILE_SIZE} bytes] ...\n"
                                    code_contents.append({
                                        "filename": f"{zip_info.filename} (truncated)",
                                        "content": truncated_content
                                    })
                                    warnings.append(f"File '{zip_info.filename}' was truncated for analysis as it exceeds size limits.")
                                    total_content_size += len(truncated_content)
                                else:
                                    code_contents.append({
                                        "filename": zip_info.filename,
                                        "content": file_content
                                    })
                                    total_content_size += file_size
                            except Exception as file_error:
                                warnings.append(f"Error processing file '{zip_info.filename}' in zip: {str(file_error)}")
                                continue
            except Exception as zip_error:
                warnings.append(f"Error reading zip file '{filename}': {str(zip_error)}")
                continue
        else:
            try:
                file_content = (await uploaded_file.read()).decode("utf-8")
                file_size = len(file_content)
                if total_content_size + file_size > MAX_CONTENT_SIZE:
                    warnings.append(f"File '{filename}' skipped due to total content size limits.")
                    continue
                if file_size > MAX_FILE_SIZE:
                    truncated_content = file_content[:MAX_FILE_SIZE]
                    truncated_content += f"\n\n... [Content truncated - file is {file_size} bytes, showing first {MAX_FILE_SIZE} bytes] ...\n"
                    code_contents.append({
                        "filename": f"{filename} (truncated)",
                        "content": truncated_content
                    })
                    warnings.append(f"File '{filename}' was truncated for analysis as it exceeds size limits.")
                    total_content_size += len(truncated_content)
                else:
                    code_contents.append({
                        "filename": filename,
                        "content": file_content
                    })
                    total_content_size += file_size
            except Exception as file_error:
                warnings.append(f"Error processing file '{filename}': {str(file_error)}")
                continue

    if not code_contents:
        return JSONResponse(status_code=400, content={"error": "No readable file content found.", "warnings": warnings})

    prompt = construct_prompt(code_contents)

    # Prepare OpenRouter API call
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-app-domain.com",
        "X-Title": "AI-Powered Code Review"
    }
    messages = [
        {
            "role": "system",
            "content": "You are an expert software engineer conducting a comprehensive code review. Take your time to think through each step of the analysis process."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    payload = {
        "model": "google/gemini-2.5-flash-preview:thinking",
        "messages": messages,
        "max_tokens": 65535,
        "temperature": 0.2,
        "top_p": 0.85
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=600)
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        result = response.json()
        review_text = None
        if "choices" in result and result["choices"]:
            review_text = result["choices"][0]["message"]["content"]
        else:
            raise Exception("No response content from OpenRouter.")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "warnings": warnings})

    # Check for potential truncation
    truncated = False
    if review_text and (
        review_text.endswith("...") or
        "I'll continue with" in review_text[-100:] or
        not any(review_text.lower().endswith(end) for end in ['.', '!', '?', ':', ';', ')', '}'])
    ):
        truncated = True
        warnings.append("The review might be truncated due to length limitations. Consider analyzing fewer files at once for more complete results.")

    return {
        "review": review_text,
        "warnings": warnings,
        "truncated": truncated
    } 