# RAG Parameter Integration - Complete System

## Overview

This system now includes **full RAG (Retrieval-Augmented Generation) parameter configuration**, allowing users to fine-tune how the AI retrieves and processes reference documents during report generation.

## What's New

### User Interface
- ✅ RAG parameter controls in document generation UI
- ✅ 4 built-in presets (Default, High Precision, Comprehensive, Fast)
- ✅ Real-time validation and feedback
- ✅ Reset to defaults functionality

### Backend
- ✅ Pydantic models for parameter validation
- ✅ Dynamic vector store configuration
- ✅ Preset management system
- ✅ API endpoint integration

### Documentation
- ✅ Comprehensive integration guide
- ✅ Quick start guide
- ✅ API reference
- ✅ Troubleshooting section

---

## Quick Links

📚 **[Full Integration Guide](./docs/RAG_INTEGRATION_GUIDE.md)** - Complete technical documentation

⚡ **[Quick Start Guide](./docs/RAG_QUICK_START.md)** - Get started in 2 minutes

---

## System Architecture

```
Frontend UI (templates/generate_report.html)
    ↓
JavaScript Validation (static/js/newreport.js)
    ↓
API Endpoint (api/endpoints/document.py)
    ↓
RAG Config Models (core/config/rag_config.py)
    ↓
Document Pipeline (core/document.py)
    ↓
Vector Store (core/store.py)
```

---

## File Changes

### New Files
- `core/config/rag_config.py` - RAG parameter models and presets
- `docs/RAG_INTEGRATION_GUIDE.md` - Complete documentation
- `docs/RAG_QUICK_START.md` - Quick reference
- `RAG_INTEGRATION_README.md` - This file

### Modified Files
- `templates/generate_report.html` - Added RAG UI controls
- `static/js/newreport.js` - Added validation and preset logic
- `core/store.py` - Dynamic parameter support
- `core/document.py` - RAG parameter flow
- `api/endpoints/document.py` - API parameter handling

---

## Key Features

### 1. Preset System

Four optimized presets for common use cases:

| Preset | Use Case | Threshold | Top K | Chunk Size |
|--------|----------|-----------|-------|------------|
| Default | General purpose | 0.6 | 5 | 512 |
| High Precision | Accurate content | 0.8 | 3 | 256 |
| Comprehensive | Broad coverage | 0.5 | 10 | 1024 |
| Fast | Quick results | 0.7 | 3 | 256 |

### 2. Parameter Configuration

#### Similarity Threshold (0.0 - 1.0)
Controls relevance strictness. Higher = more precise, lower = broader context.

#### Top K (1 - 50)
Number of document chunks to retrieve. More = comprehensive, fewer = focused.

#### Chunk Size (256/512/1024 tokens)
Size of text segments. Larger = more context, smaller = more precise.

#### Overlap (0% - 50%)
Chunk overlap for continuity. Higher = better flow, lower = faster.

### 3. Validation

- Real-time parameter validation
- Clear error messages
- Range enforcement
- Type checking

### 4. Integration Points

RAG parameters are integrated at every level:

1. **UI Layer**: Interactive controls with validation
2. **API Layer**: Form data processing and preset handling
3. **Pipeline Layer**: Parameter flow through generation
4. **Vector Store Layer**: Dynamic retrieval configuration

---

## Usage Example

### Frontend (JavaScript)

```javascript
// User selects preset
document.getElementById("ragPresetSelect").value = "high_precision";
applyRagPreset("high_precision");

// Or customizes parameters
document.getElementById("similarityThreshold").value = 0.75;
document.getElementById("topK").value = 8;

// Submit form
const formData = new FormData();
formData.append("similarity_threshold", 0.75);
formData.append("top_k", 8);
formData.append("chunk_size", 512);
formData.append("overlap", 20);
```

### Backend (Python)

```python
# API receives parameters
@router.post("/process/")
async def process_document(
    similarity_threshold: Optional[float] = Form(None),
    top_k: Optional[int] = Form(None),
    # ... other parameters
):
    # Create RAG config
    rag_params = RagParameters(
        similarity_threshold=similarity_threshold,
        top_k=top_k,
        chunk_size=chunk_size,
        overlap=overlap
    )

    # Pass to document generation
    report = await core.document.generate(
        sections,
        extracted_texts,
        rag_params=rag_params
    )
```

### Vector Store Usage

```python
# Store uses parameters for chunking
core.store.add_sources(source_texts, rag_params=rag_params)

# Retriever uses parameters for search
retriever = core.store.as_retriever(rag_params=rag_params)
```

---

## Testing

### Manual Testing

1. Start server: `python run.py`
2. Navigate to: http://localhost:8000/generate-report
3. Upload reference documents
4. Select RAG preset or customize parameters
5. Generate report
6. Check server logs for parameter confirmation

### Validation Testing

```bash
# Test presets
curl -X POST http://localhost:8000/documents/process/ \
  -F "files=@test.pdf" \
  -F "template_name=proposal_template.json" \
  -F "rag_preset=high_precision"

# Test custom parameters
curl -X POST http://localhost:8000/documents/process/ \
  -F "files=@test.pdf" \
  -F "template_name=proposal_template.json" \
  -F "similarity_threshold=0.7" \
  -F "top_k=10" \
  -F "chunk_size=1024" \
  -F "overlap=25"
```

### Log Verification

Check logs for RAG parameter usage:

```bash
tail -f logs/app.log | grep "RAG"
```

Expected output:
```
INFO: Using RAG preset: high_precision
INFO: Using custom RAG parameters: {'similarity_threshold': 0.8, 'top_k': 3, ...}
INFO: Loading 3 source document(s) into vector store
```

---

## Integration Checklist

### For Developers

- [x] Backend RAG configuration model created
- [x] Vector store updated for dynamic parameters
- [x] API endpoints accept RAG parameters
- [x] Frontend controls implemented
- [x] Validation logic added
- [x] Preset system functional
- [x] Documentation complete

### For Users

- [x] UI controls visible and interactive
- [x] Presets apply correctly
- [x] Custom parameters work
- [x] Validation provides clear feedback
- [x] Reset functionality works
- [x] Generated reports use parameters

---

## Local Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Server

```bash
python run.py
```

### 3. Access UI

Navigate to: http://localhost:8000/generate-report

### 4. Verify Integration

1. Check RAG parameter section is visible
2. Select "High Precision" preset
3. Verify values update (threshold=0.8, top_k=3, etc.)
4. Upload a document and generate
5. Check server logs confirm parameters used

---

## Troubleshooting

### Parameters Not Applying

**Check**: Browser console for JavaScript errors
**Check**: Network tab shows parameters in POST data
**Check**: Server logs show parameter reception

### UI Not Showing

**Solution**: Clear browser cache, verify JS files loaded

### Validation Errors

**Solution**: Ensure values are within valid ranges (see documentation)

### Performance Issues

**Solution**: Use "Fast" preset or reduce Top K and Chunk Size

---

## Architecture Decisions

### Why Pydantic?
- Strong type validation
- Automatic serialization
- Clear error messages
- Easy preset management

### Why Form Parameters?
- File upload compatibility
- Simple frontend integration
- Standard HTTP multipart/form-data
- No JSON parsing needed

### Why Presets?
- User-friendly defaults
- Quick configuration
- Best practices encoded
- Easy to extend

### Why Global Store State?
- Simplified parameter passing
- Single source of truth
- Thread-safe for single-user mode
- Easy to migrate to per-user state

---

## Future Enhancements

### Potential Additions

1. **Parameter History**
   - Save successful configurations
   - Quick reload of previous settings

2. **A/B Comparison**
   - Generate with two different configs
   - Side-by-side comparison

3. **Auto-tuning**
   - ML-based parameter optimization
   - Learn from user feedback

4. **Per-Template Defaults**
   - Different defaults per report type
   - Template-specific optimization

5. **Advanced Presets**
   - Industry-specific configurations
   - Document-type optimized settings

---

## API Summary

### Endpoints with RAG Support

- `POST /documents/process/` - Document generation
- `POST /documents/targeted-edit/` - Section editing

### Parameters

All endpoints accept:
- `similarity_threshold` (float, 0.0-1.0)
- `top_k` (int, 1-50)
- `chunk_size` (int, 100-2000)
- `overlap` (int, 0-50)
- `rag_preset` (string: default, high_precision, comprehensive, fast)

---

## Support

### Documentation
- [Full Guide](./docs/RAG_INTEGRATION_GUIDE.md)
- [Quick Start](./docs/RAG_QUICK_START.md)

### Debug
- Enable detailed logging in `core/document.py`
- Check server logs: `tail -f logs/app.log`
- Monitor browser console for frontend errors

### Contact
Create an issue with:
- RAG parameters used
- Expected vs actual behavior
- Server logs
- Browser console output

---

## Summary

The RAG parameter integration provides users with fine-grained control over document retrieval and generation. The system includes:

✅ **Complete UI controls** with presets and validation
✅ **Backend processing** with type safety and validation
✅ **Vector store integration** for dynamic configuration
✅ **Comprehensive documentation** for users and developers
✅ **Testing tools** for verification

Users can now optimize their document generation for accuracy, comprehensiveness, or speed based on their specific needs.

---

**Version**: 1.0.0
**Last Updated**: 2025-11-28
**Status**: Production Ready
