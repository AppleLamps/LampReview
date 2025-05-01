# AI-Powered Code Review API

## POST `/analyze`

Analyze uploaded code files using Gemini 2.5 (OpenRouter) and receive a professional, structured code review.

---

### **Request**

**Endpoint:**  
`POST /analyze`  
**Content-Type:** `multipart/form-data`

#### **Parameters**

| Name      | Type                | Required | Description                                      |
|-----------|---------------------|----------|--------------------------------------------------|
| files     | File[] (multi-part) | Yes      | One or more code files, or a zip archive         |
| api_key   | string (form field) | No       | OpenRouter API key (if not in backend .env file) |

- **files**: Accepts multiple files. Each file can be a code file (`.py`, `.js`, etc.) or a single `.zip` containing code files.
- **api_key**: Optional if the backend already has the key in its environment.

#### **Example Request (JavaScript/Fetch)**

```js
const formData = new FormData();
formData.append('files', file1); // file1: File object
formData.append('files', file2); // file2: File object (or just one .zip)
formData.append('api_key', 'sk-...'); // optional

fetch('https://your-backend-url/analyze', {
  method: 'POST',
  body: formData
})
  .then(res => res.json())
  .then(data => {
    // data.review, data.warnings, data.truncated
  });
```

---

### **Response**

#### **Success (200 OK)**

```json
{
  "review": "string (markdown, full AI review)",
  "warnings": ["string", "..."],
  "truncated": true
}
```

- **review**: The full code review as markdown (render as rich text).
- **warnings**: Array of warning messages (may be empty).
- **truncated**: Boolean, true if the review may be incomplete due to length.

#### **Error Responses**

- **400 Bad Request**
  ```json
  {
    "error": "No readable file content found.",
    "warnings": ["..."]
  }
  ```
  - If no valid files are uploaded or all are skipped.

- **500 Internal Server Error**
  ```json
  {
    "error": "Error message from backend or OpenRouter",
    "warnings": ["..."]
  }
  ```
  - If something goes wrong with the OpenRouter API or file processing.

---

### **Frontend UI Guidance**

- **File Upload**: Allow users to select multiple files or a zip archive.
- **API Key Input**: (Optional) Text input for OpenRouter API key.
- **Submit Button**: Triggers the POST request.
- **Progress Indicator**: Show a spinner or progress bar while waiting for the response.
- **Results Display**:
  - Render the `review` markdown as rich text.
  - Show any `warnings` as alerts or info boxes.
  - If `truncated` is true, display a warning about possible incomplete results.
- **Error Handling**: Show error messages from the backend if present.

---

**Contact the backend developer if you need more details or want to extend the API.** 