# RAG Parameter Integration Guide

## Overview

This document provides a comprehensive guide to the RAG (Retrieval-Augmented Generation) parameter configuration system integrated into the automated documentation generation platform. Users can now customize how the AI retrieves and processes reference documents through an intuitive UI.

## Table of Contents

1. [What are RAG Parameters?](#what-are-rag-parameters)
2. [System Architecture](#system-architecture)
3. [Parameter Definitions](#parameter-definitions)
4. [Using RAG Parameters](#using-rag-parameters)
5. [Integration Details](#integration-details)
6. [Local Setup Guide](#local-setup-guide)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## What are RAG Parameters?

RAG parameters control how the system retrieves relevant information from your reference documents. By adjusting these parameters, you can:

- **Control relevance**: Set minimum similarity thresholds for document retrieval
- **Adjust context size**: Configure how much text is retrieved at once
- **Optimize performance**: Balance between speed and comprehensiveness
- **Fine-tune accuracy**: Get more or fewer relevant document chunks

---

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (UI)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RAG Parameter Controls                                │ │
│  │  - Preset Selection                                    │ │
│  │  - Similarity Threshold Slider                         │ │
│  │  - Top K Input                                         │ │
│  │  - Chunk Size Dropdown                                 │ │
│  │  - Overlap Percentage Input                            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ FormData POST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API Layer                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  /documents/process/                                   │ │
│  │  - Validates RAG parameters                            │ │
│  │  - Applies presets or custom values                    │ │
│  │  - Passes to document generation pipeline              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ RagParameters object
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Core Processing Layer                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  core.document.generate()                              │ │
│  │  - Receives RAG parameters                             │ │
│  │  - Passes to vector store initialization               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Configuration
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Vector Store Layer                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  core.store.add_sources()                              │ │
│  │  - Uses chunk_size and overlap for text splitting      │ │
│  │                                                        │ │
│  │  core.store.as_retriever()                             │ │
│  │  - Uses top_k and similarity_threshold for retrieval   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
project/
├── templates/
│   └── generate_report.html          # UI with RAG controls
├── static/
│   └── js/
│       ├── newreport.js               # Frontend logic & validation
│       └── rag-config.js              # RAG parameter manager (optional)
├── api/
│   └── endpoints/
│       └── document.py                # API endpoints with RAG params
├── core/
│   ├── config/
│   │   └── rag_config.py             # Parameter models & presets
│   ├── store.py                       # Vector store with RAG support
│   └── document.py                    # Document generation pipeline
└── docs/
    └── RAG_INTEGRATION_GUIDE.md      # This file
```

---

## Parameter Definitions

### 1. Similarity Threshold

**Type**: Float
**Range**: 0.0 to 1.0
**Default**: 0.6
**Step**: 0.05

**Description**: Minimum relevance score required for a document chunk to be included in the context. Higher values mean stricter matching.

**Use Cases**:
- **Low (0.4-0.5)**: Broader context, more creative outputs
- **Medium (0.6-0.7)**: Balanced relevance and coverage
- **High (0.8-0.9)**: Strict matching, very relevant results only

### 2. Top K

**Type**: Integer
**Range**: 1 to 50
**Default**: 5

**Description**: Number of most relevant document chunks to retrieve and include in the generation context.

**Use Cases**:
- **Low (1-3)**: Focused, targeted information
- **Medium (5-10)**: Standard context window
- **High (15-50)**: Comprehensive coverage, may include less relevant info

### 3. Chunk Size

**Type**: Integer (tokens)
**Range**: 100 to 2000
**Default**: 512
**Options**: Small (256), Medium (512), Large (1024)

**Description**: Size of text chunks to split and retrieve. Larger chunks provide more context per retrieval but may be less precise.

**Use Cases**:
- **Small (256)**: Precise retrieval, good for specific facts
- **Medium (512)**: Balanced context and precision
- **Large (1024)**: Broader context, better for understanding relationships

### 4. Overlap Percentage

**Type**: Integer
**Range**: 0 to 50
**Default**: 15
**Unit**: Percentage

**Description**: Percentage of overlap between consecutive text chunks. Higher overlap ensures context continuity across chunk boundaries.

**Use Cases**:
- **Low (0-10%)**: Minimal redundancy, faster processing
- **Medium (15-20%)**: Balanced continuity
- **High (30-50%)**: Maximum context preservation

---

## Using RAG Parameters

### Method 1: Using Presets (Recommended for Beginners)

The system includes 4 built-in presets optimized for different scenarios:

#### 1. **Default (Balanced)**
```
Similarity Threshold: 0.6
Top K: 5
Chunk Size: 512
Overlap: 15%
```
**Best for**: General purpose document generation

#### 2. **High Precision**
```
Similarity Threshold: 0.8
Top K: 3
Chunk Size: 256
Overlap: 10%
```
**Best for**: When you need highly accurate, fact-based content

#### 3. **Comprehensive**
```
Similarity Threshold: 0.5
Top K: 10
Chunk Size: 1024
Overlap: 20%
```
**Best for**: Complex documents requiring broad context

#### 4. **Fast**
```
Similarity Threshold: 0.7
Top K: 3
Chunk Size: 256
Overlap: 10%
```
**Best for**: Quick results with minimal processing time

### Method 2: Custom Configuration

1. **Select a preset** as a starting point
2. **Adjust individual parameters** using the controls
3. **Validation** happens automatically on blur/change
4. **Click "Reset"** to return to default values

### UI Controls

```html
<!-- Preset Selector -->
<select id="ragPresetSelect">
  <option value="default">Default (Balanced)</option>
  <option value="high_precision">High Precision</option>
  <option value="comprehensive">Comprehensive</option>
  <option value="fast">Fast</option>
</select>

<!-- Similarity Threshold Slider -->
<input type="range" id="similarityThreshold"
       min="0" max="1" step="0.05" value="0.6">

<!-- Top K Input -->
<input type="number" id="topK"
       min="1" max="50" value="5">

<!-- Chunk Size Dropdown -->
<select id="chunkSize">
  <option value="256">Small (256)</option>
  <option value="512" selected>Medium (512)</option>
  <option value="1024">Large (1024)</option>
</select>

<!-- Overlap Input -->
<input type="number" id="overlap"
       min="0" max="50" value="15">
```

---

## Integration Details

### Backend Integration

#### 1. RAG Configuration Model (`core/config/rag_config.py`)

```python
from pydantic import BaseModel, Field

class RagParameters(BaseModel):
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    top_k: int = Field(default=5, ge=1, le=50)
    chunk_size: int = Field(default=512, ge=100, le=2000)
    overlap: int = Field(default=15, ge=0, le=50)
```

Features:
- **Pydantic validation**: Automatic parameter validation
- **Default values**: Sensible defaults for all parameters
- **Type safety**: Strong typing with range constraints

#### 2. Vector Store Integration (`core/store.py`)

```python
def add_sources(
    source_texts: Mapping[str, str],
    rag_params: Optional[RagParameters] = None
) -> list[str]:
    # Calculate chunk overlap in tokens
    chunk_overlap_tokens = int(
        rag_params.chunk_size * (rag_params.overlap / 100.0)
    )

    # Configure text splitter with RAG parameters
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=rag_params.chunk_size,
        chunk_overlap=chunk_overlap_tokens,
        add_start_index=True
    )

    # Split and add documents
    docs = text_splitter.create_documents(texts, metadatas)
    return vector_store.add_documents(documents=all_splits)

def as_retriever(
    limit_to_sources: list[str] = [],
    rag_params: Optional[RagParameters] = None
):
    search_kwargs = {
        "k": rag_params.top_k,
        "score_threshold": rag_params.similarity_threshold
    }

    return vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs=search_kwargs
    )
```

#### 3. API Endpoint (`api/endpoints/document.py`)

```python
@router.post("/process/")
async def process_document(
    files: List[UploadFile] = File(...),
    template_name: str = Form("proposal_template.json"),
    similarity_threshold: Optional[float] = Form(None),
    top_k: Optional[int] = Form(None),
    chunk_size: Optional[int] = Form(None),
    overlap: Optional[int] = Form(None),
    rag_preset: Optional[str] = Form(None)
):
    # Initialize from preset if provided
    rag_params = None
    if rag_preset:
        rag_params = RagPreset.get_preset(rag_preset)

    # Override with custom parameters
    if any([similarity_threshold, top_k, chunk_size, overlap]):
        if not rag_params:
            rag_params = RagParameters()

        if similarity_threshold is not None:
            rag_params.similarity_threshold = similarity_threshold
        # ... (apply other parameters)

    # Pass to document generation
    report_sections = await core.document.generate(
        sections,
        extracted_texts,
        example_document_text=example_text,
        rag_params=rag_params
    )
```

### Frontend Integration

#### JavaScript Functions (`static/js/newreport.js`)

```javascript
// Validation
function validateRagParameters() {
  const errors = [];
  const threshold = parseFloat(document.getElementById("similarityThreshold").value);

  if (isNaN(threshold) || threshold < 0 || threshold > 1) {
    errors.push("Similarity threshold must be between 0.0 and 1.0");
  }

  // Display errors or return validation status
  if (errors.length > 0) {
    document.getElementById("ragValidationErrors").innerHTML = errors.join("<br>");
    return false;
  }

  return true;
}

// Preset application
function applyRagPreset(presetName) {
  const presets = {
    default: { similarity_threshold: 0.6, top_k: 5, chunk_size: 512, overlap: 15 },
    // ... other presets
  };

  const preset = presets[presetName];
  document.getElementById("similarityThreshold").value = preset.similarity_threshold;
  // ... apply other values
}

// Form submission
async function uploadFile() {
  const formData = new FormData();

  // Add RAG parameters to form
  formData.append("similarity_threshold",
    parseFloat(document.getElementById("similarityThreshold").value));
  formData.append("top_k",
    parseInt(document.getElementById("topK").value));
  // ... add other parameters

  // Submit to API
  const response = await fetch("/documents/process/", {
    method: "POST",
    body: formData
  });
}
```

---

## Local Setup Guide

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend development)
- Git

### Installation Steps

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd <project-directory>
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `fastapi`: API framework
- `pydantic`: Data validation
- `langchain`: RAG framework
- `langchain-huggingface`: Embeddings
- `python-dotenv`: Environment management

#### 3. Verify File Structure

Ensure the following files exist:

```bash
# Backend files
core/config/rag_config.py
core/store.py
core/document.py
api/endpoints/document.py

# Frontend files
templates/generate_report.html
static/js/newreport.js
static/js/rag-config.js
```

#### 4. Environment Configuration

Create a `.env` file (if not exists):

```bash
# No RAG-specific environment variables needed
# The system uses default configuration
```

#### 5. Start the Server

```bash
python run.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --port 8000
```

#### 6. Access the Application

Open your browser and navigate to:

```
http://localhost:8000/generate-report
```

### Verification Steps

1. **Check UI Rendering**:
   - Navigate to the "Generate Reports" page
   - Verify RAG Parameter section is visible
   - Confirm all controls are interactive

2. **Test Preset Selection**:
   - Select "High Precision" preset
   - Verify all values update accordingly
   - Check similarity threshold shows 0.8

3. **Test Custom Parameters**:
   - Adjust similarity threshold slider
   - Enter custom Top K value
   - Click "Reset" to verify defaults restore

4. **Test Validation**:
   - Enter invalid value (e.g., Top K = 100)
   - Blur the input field
   - Verify error message appears

5. **Test Document Generation**:
   - Upload a test document
   - Select a template
   - Set custom RAG parameters
   - Click "Start Generating!"
   - Check server logs for RAG parameter confirmation

### Troubleshooting Setup

#### Issue: RAG Controls Not Visible

**Solution**:
1. Clear browser cache
2. Check browser console for JavaScript errors
3. Verify `newreport.js` is loading correctly

#### Issue: Parameters Not Applying

**Solution**:
1. Check browser Network tab for POST data
2. Verify FormData includes RAG parameters
3. Check server logs for parameter reception

#### Issue: Validation Errors

**Solution**:
1. Ensure all inputs have valid IDs
2. Verify validation functions are attached to events
3. Check console for JavaScript errors

---

## API Reference

### POST `/documents/process/`

Generate a new document with custom RAG parameters.

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | File[] | Yes | - | Reference documents (PDF/DOCX) |
| `template_name` | string | Yes | - | Template JSON filename |
| `example_file` | File | No | null | Style example document |
| `similarity_threshold` | float | No | 0.6 | Minimum relevance score (0.0-1.0) |
| `top_k` | int | No | 5 | Number of documents to retrieve (1-50) |
| `chunk_size` | int | No | 512 | Text chunk size in tokens (100-2000) |
| `overlap` | int | No | 15 | Chunk overlap percentage (0-50) |
| `rag_preset` | string | No | null | Preset name (default, high_precision, etc.) |

#### Example Request (cURL)

```bash
curl -X POST http://localhost:8000/documents/process/ \
  -F "files=@reference.pdf" \
  -F "template_name=proposal_template.json" \
  -F "similarity_threshold=0.7" \
  -F "top_k=8" \
  -F "chunk_size=1024" \
  -F "overlap=20"
```

#### Example Request (JavaScript)

```javascript
const formData = new FormData();
formData.append("files", fileInput.files[0]);
formData.append("template_name", "proposal_template.json");
formData.append("similarity_threshold", 0.7);
formData.append("top_k", 8);
formData.append("chunk_size", 1024);
formData.append("overlap", 20);

const response = await fetch("/documents/process/", {
  method: "POST",
  body: formData
});

const result = await response.json();
```

#### Response Format

```json
{
  "message": "Full report successfully generated",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "report_sections": {
    "section1": {
      "title": "Introduction",
      "content": "..."
    }
  },
  "flattened_sections": {},
  "docx_path": "/outputs/docx_report_20251128_123456.docx",
  "pdf_path": "/outputs/pdf_report_20251128_123456.pdf",
  "json_path": "/outputs/extracted_report_20251128_123456.json"
}
```

### POST `/documents/targeted-edit/`

Edit specific sections with custom RAG parameters.

#### Request Parameters

Same RAG parameters as `/process/`, plus:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `example_file` | File | Yes | Base document to edit |
| `reference_files` | File[] | Yes | Reference materials |
| `section_changes` | string | Yes | JSON array of section modifications |

---

## Troubleshooting

### Common Issues

#### 1. Parameters Not Taking Effect

**Symptoms**:
- Custom parameters entered but results seem unchanged
- Server logs show default values being used

**Diagnosis**:
```bash
# Check server logs
tail -f logs/app.log | grep "RAG parameters"
```

**Solutions**:
- Verify form submission includes all parameters
- Check browser Network tab for POST payload
- Ensure no JavaScript errors in console
- Confirm backend receives parameters (add debug logs)

#### 2. Validation Errors

**Symptoms**:
- Red error messages appear below RAG controls
- Form submission blocked

**Solutions**:
- Check parameter ranges (see Parameter Definitions)
- Ensure numerical inputs contain valid numbers
- Use presets first to verify working configuration
- Check browser console for validation function errors

#### 3. Performance Issues

**Symptoms**:
- Slow document generation
- Timeouts during processing

**Solutions**:
- Try "Fast" preset for quicker results
- Reduce `top_k` value (fewer documents retrieved)
- Use smaller `chunk_size` (256 instead of 1024)
- Check document size (very large PDFs may be slow)

#### 4. Low-Quality Results

**Symptoms**:
- Generated content lacks relevant information
- Output seems generic or off-topic

**Solutions**:
- Increase `top_k` to retrieve more context
- Lower `similarity_threshold` (0.5 instead of 0.8)
- Use larger `chunk_size` for more context
- Try "Comprehensive" preset
- Verify reference documents are relevant

#### 5. Over-Retrieval (Too Much Context)

**Symptoms**:
- Generated content is too verbose
- Includes tangential or irrelevant information

**Solutions**:
- Decrease `top_k` (try 3 instead of 10)
- Increase `similarity_threshold` (0.8 instead of 0.6)
- Use "High Precision" preset
- Verify chunk boundaries with smaller chunks

### Debug Mode

Enable detailed logging:

```python
# In core/document.py
if rag_params:
    logger.info(f"RAG Config: {rag_params.model_dump()}")
    logger.info(f"Chunk overlap: {rag_params.chunk_size * (rag_params.overlap / 100)}")
```

Check logs:

```bash
tail -f logs/app.log
```

### Testing RAG Parameters

Create a test script:

```python
# test_rag_params.py
from core.config.rag_config import RagParameters, RagPreset

# Test default parameters
default_params = RagParameters()
print(f"Default: {default_params.model_dump()}")

# Test preset
high_precision = RagPreset.get_preset("high_precision")
print(f"High Precision: {high_precision.model_dump()}")

# Test custom parameters
custom = RagParameters(
    similarity_threshold=0.75,
    top_k=8,
    chunk_size=768,
    overlap=25
)
print(f"Custom: {custom.model_dump()}")
```

Run:

```bash
python test_rag_params.py
```

---

## Best Practices

### 1. Start with Presets

Always begin with a preset that matches your use case:
- **General documents**: Default
- **Technical/precise**: High Precision
- **Complex/comprehensive**: Comprehensive
- **Quick drafts**: Fast

### 2. Iterative Refinement

1. Generate document with preset
2. Review results
3. Identify issues (too broad, too narrow, missing info)
4. Adjust one parameter at a time
5. Regenerate and compare

### 3. Parameter Relationships

Understand parameter interactions:
- **High threshold + Low top_k**: Very focused, may miss context
- **Low threshold + High top_k**: Comprehensive but may include noise
- **Large chunks + High overlap**: Maximum context, slower processing
- **Small chunks + Low overlap**: Fast, precise, may lose context

### 4. Document-Specific Tuning

Different document types benefit from different settings:

**Technical Reports**:
```
similarity_threshold: 0.7-0.8 (high precision)
top_k: 5-8 (focused retrieval)
chunk_size: 512 (balanced)
overlap: 15-20% (good continuity)
```

**Literature Reviews**:
```
similarity_threshold: 0.5-0.6 (broader context)
top_k: 10-15 (comprehensive)
chunk_size: 1024 (larger context)
overlap: 20-25% (strong continuity)
```

**Executive Summaries**:
```
similarity_threshold: 0.7 (focused)
top_k: 3-5 (concise)
chunk_size: 256-512 (targeted)
overlap: 10-15% (efficient)
```

### 5. Performance Optimization

For faster generation:
- Use smaller chunk sizes (256)
- Reduce top_k (3-5)
- Lower overlap percentage (10%)
- Pre-process large documents into focused sections

### 6. Quality Assurance

After generation:
- Verify factual accuracy against source documents
- Check for missing critical information
- Ensure proper context flow
- Validate citations and references

---

## Appendix

### A. Parameter Impact Matrix

| Parameter | ↑ Increases | ↓ Decreases |
|-----------|-------------|-------------|
| **similarity_threshold** | Precision, focus | Recall, coverage |
| **top_k** | Context, coverage | Speed, focus |
| **chunk_size** | Context per chunk | Precision, speed |
| **overlap** | Continuity | Speed, efficiency |

### B. Preset Comparison Table

| Preset | Threshold | Top K | Chunk Size | Overlap | Best For |
|--------|-----------|-------|------------|---------|----------|
| Default | 0.6 | 5 | 512 | 15% | General use |
| High Precision | 0.8 | 3 | 256 | 10% | Accurate, focused |
| Comprehensive | 0.5 | 10 | 1024 | 20% | Broad coverage |
| Fast | 0.7 | 3 | 256 | 10% | Quick results |

### C. Glossary

- **RAG**: Retrieval-Augmented Generation - combining retrieval and generation
- **Chunk**: A segment of text split from the source document
- **Embedding**: Vector representation of text for similarity comparison
- **Similarity Score**: Numerical measure of relevance (0.0 to 1.0)
- **Top K**: Number of most relevant results to retrieve
- **Overlap**: Shared tokens between consecutive chunks
- **Threshold**: Minimum score required for inclusion

### D. Related Documentation

- [System Architecture Overview](./Doc%20Prep%20-%20Technical%20Documentation.docx)
- [API Documentation](../README.md)
- [Frontend Development Guide](./STYLE_GUIDANCE_FEATURE.md)

---

## Support

For issues, questions, or feature requests:

1. Check this documentation first
2. Review server logs for errors
3. Test with default presets
4. Create an issue with:
   - RAG parameters used
   - Expected vs actual behavior
   - Server logs (relevant sections)
   - Browser console output

---

**Last Updated**: 2025-11-28
**Version**: 1.0.0
