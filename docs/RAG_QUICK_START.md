# RAG Parameters - Quick Start Guide

## What You Need to Know in 2 Minutes

### What Are RAG Parameters?

RAG parameters control **how the AI finds and uses information** from your reference documents when generating reports.

### The 4 Parameters

1. **Similarity Threshold** (0.0 - 1.0): How closely documents must match your needs
   - Lower = More results, broader context
   - Higher = Fewer results, more precise

2. **Top K** (1 - 50): How many relevant chunks to retrieve
   - Lower = Faster, more focused
   - Higher = More comprehensive

3. **Chunk Size** (256/512/1024): Size of text pieces
   - Small = Precise facts
   - Large = Broader context

4. **Overlap** (0% - 50%): How much chunks overlap
   - Low = Faster processing
   - High = Better context flow

---

## Quick Start

### Option 1: Use Presets (Easiest)

Just select a preset and click "Start Generating!":

- **Default**: General purpose ✓
- **High Precision**: When accuracy matters
- **Comprehensive**: Need lots of context
- **Fast**: Quick results

### Option 2: Custom Settings

1. Select a preset as starting point
2. Adjust sliders/inputs
3. Click "Start Generating!"

---

## Common Scenarios

### "I need very accurate, fact-based content"
→ Use **High Precision** preset

### "My report is missing important information"
→ Increase **Top K** to 10-15
→ Lower **Similarity Threshold** to 0.5

### "The AI is including irrelevant information"
→ Decrease **Top K** to 3
→ Increase **Similarity Threshold** to 0.8

### "Generation is too slow"
→ Use **Fast** preset
→ Or: Reduce Top K and Chunk Size

---

## Local Integration Checklist

✓ Upload reference documents
✓ Select report template
✓ Choose RAG preset (or customize)
✓ Click "Start Generating!"
✓ Review and download

---

## Need Help?

See full documentation: [RAG_INTEGRATION_GUIDE.md](./RAG_INTEGRATION_GUIDE.md)

---

**Pro Tip**: Start with Default preset, then adjust based on results!
