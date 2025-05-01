# 🧠 AI-Powered Code Review Backend (FastAPI + Gemini 2.5 via OpenRouter)

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/built%20with-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A FastAPI backend that leverages Google's Gemini 2.5 model (via the OpenRouter API) to perform comprehensive, professional code reviews. This backend is designed to be used with any frontend (such as v0 on Vercel) and provides a robust, structured API for code analysis.

---

## Overview

- Upload multiple code files (or a zip archive) and receive a detailed, AI-powered review.
- Covers security, performance, architecture, code quality, and best practices.
- Uses a multi-step, expert-level prompt for thorough analysis.
- Designed for easy integration with modern frontends.

---

## Features

- **AI-Powered Analysis:** Uses `google/gemini-2.5-flash-preview:thinking` via OpenRouter.
- **Structured Review:** Follows a multi-step expert process (see API contract).
- **Multi-File Support:** Upload multiple files or a zip archive.
- **Wide Language Support:** Accepts `.py`, `.js`, `.java`, `.ts`, `.go`, `.rb`, `.php`, `.cs`, `.c`, `.cpp`, `.html`, `.css`, `.sql`, and more.
- **File Size Handling:** 50MB per file, 50MB total; truncates oversized files with warnings.
- **API Key Management:** Reads from `.env` or accepts via request.
- **CORS Enabled:** Ready for frontend integration.

---

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```
OPENROUTER_API_KEY=sk-your-api-key-here
```
(See `.env.example` for reference.)

---

## Running Locally

```bash
uvicorn main:app --reload
```
- The API will be available at `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

---

## Deploying to Railway (Recommended)

1. Push your code to GitHub.
2. Go to [Railway](https://railway.app/) and create a new project.
3. Deploy from your GitHub repo.
4. Set the environment variable `OPENROUTER_API_KEY` in the Railway dashboard.
5. Set the start command:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
6. Deploy and use your public Railway URL for frontend integration.

---

## API Usage

See `API_CONTRACT.md` for full details.

### **POST `/analyze`**
- **Request:** `multipart/form-data` with `files` (one or more code files or a zip) and optional `api_key`.
- **Response:** JSON with `review` (markdown), `warnings` (list), and `truncated` (bool).
- **Interactive docs:** Visit `/docs` on your deployed backend.

---

## License

This project is licensed under the MIT License. See `LICENSE.txt` for details. 
---
