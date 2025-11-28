# Example-based Style Guidance Feature

## Overview

The **Example-based Style Guidance** feature addresses **Limitation #2** by allowing users to upload example documents that the AI system analyzes to learn writing style, tone, and formatting patterns. The system then generates new documents that match the style of the provided examples.

## How It Works

### 1. Style Extraction Process

When a user uploads an example document, the system:

1. **Extracts text content** from the example document (PDF/DOCX)
2. **Analyzes writing patterns** using a specialized Style Extractor Agent
3. **Identifies key characteristics** including:
   - Writing tone and voice (formal, conversational, technical, etc.)
   - Sentence structure patterns (length, complexity, active/passive voice)
   - Paragraph organization and flow
   - Professional language patterns and terminology
   - Formatting preferences (headings, lists, emphasis)
   - Content depth and detail level

### 2. Style-Guided Generation

The extracted style guidelines are then applied to the document generation process:

1. **Enhanced Instructions**: Section instructions are augmented with style guidance
2. **Style-Aware Agent**: A specialized drafting agent incorporates the style patterns
3. **Consistent Application**: Style guidelines are applied across all document sections
4. **Quality Assurance**: The system maintains consistency with the learned style

## Technical Implementation

### Core Components

#### 1. Style Extractor Agent (`core/agents/style_extractor_agent.py`)
- Specialized AutoGen agent for analyzing document style
- Extracts structured style guidelines in JSON format
- Focuses on tone, voice, structure, and formatting patterns

#### 2. Style Utilities (`core/utils/style_utils.py`)
- `extract_document_style()`: Main style extraction function
- `apply_style_to_instructions()`: Enhances section instructions with style guidance
- `save_style_guidelines()` / `load_style_guidelines()`: Persistence functions
- `parse_style_response()`: Parses agent responses into structured format

#### 3. Style-Guided Generation Workflow (`core/workflows/style_guided_generation.py`)
- `extract_style_from_example()`: Complete style extraction workflow
- `generate_style_guided_report()`: Report generation with style guidance

#### 4. API Endpoints (`api/endpoints/document.py`)
- `POST /documents/extract-style/`: Extract style from uploaded example
- Enhanced `POST /documents/process/`: Accepts optional example file parameter

#### 5. Frontend Interface (`templates/generate_report.html`, `static/js/newreport.js`)
- Example document upload section
- Style analysis button and preview
- Integration with existing workflow

## Usage Guide

### Web Interface

1. **Navigate to the report generation page**
2. **Upload reference documents** as usual
3. **Upload an example document** in the "Style Example" section
4. **Click "Analyze Style"** to extract style guidelines
5. **Generate the report** - it will match the example's style

### API Usage

```python
# Extract style guidelines
response = requests.post(
    "http://localhost:8000/documents/extract-style/",
    files={"file": open("example.docx", "rb")}
)
style_guidelines = response.json()["style_guidelines"]

# Generate report with style guidance
form_data = {
    "files": [open("reference.pdf", "rb")],
    "template_name": "proposal_template.json",
    "example_file": open("example.docx", "rb")
}
response = requests.post(
    "http://localhost:8000/documents/process/",
    files=form_data
)
```

### Programmatic Usage

```python
from core.workflows.style_guided_generation import generate_report_with_example_style
from core.workflows.document_extraction import load_report_structure, extract_and_clean_text

# Load template and extract reference text
sections = load_report_structure("templates/proposal_template.json")
reference_text = {"file1.pdf": extract_and_clean_text("file1.pdf")}

# Generate with style guidance
report, full_text, style_guidelines = generate_report_with_example_style(
    sections=sections,
    extracted_text=reference_text,
    example_file_path="example.docx",
    filename="output_report.docx"
)
```

## Style Guidelines Structure

The extracted style guidelines follow this structured format:

```json
{
  "writing_style": {
    "tone": "Professional and persuasive",
    "voice": "Active and confident",
    "formality_level": "formal",
    "technical_complexity": "medium"
  },
  "sentence_patterns": {
    "average_length": "medium",
    "complexity": "compound",
    "voice_preference": "active"
  },
  "paragraph_style": {
    "length": "medium",
    "organization": "Topic sentence followed by supporting details",
    "transition_style": "Smooth logical flow between ideas"
  },
  "language_patterns": {
    "terminology": ["strategic", "implementation", "optimization"],
    "professional_language": "Industry-specific with clear explanations",
    "industry_specific": ["technical specifications", "compliance requirements"]
  },
  "formatting_preferences": {
    "heading_style": "Clear hierarchical structure",
    "list_usage": "Numbered lists for processes, bullets for features",
    "emphasis_methods": "Bold for key terms, italics for emphasis"
  },
  "content_characteristics": {
    "detail_level": "high",
    "evidence_usage": "Statistics and case studies integrated naturally",
    "example_integration": "Concrete examples support abstract concepts"
  },
  "document_structure": {
    "section_organization": "Executive summary first, detailed sections follow",
    "flow_pattern": "Problem-solution-benefits structure",
    "conclusion_style": "Action-oriented with clear next steps"
  }
}
```

## Benefits

### 1. **Consistency with Existing Documents**
- Maintains organizational writing standards
- Ensures brand voice consistency
- Matches client expectations

### 2. **Improved Quality**
- Learns from high-quality example documents
- Applies proven writing patterns
- Reduces need for manual editing

### 3. **Customization**
- Adapts to different document types
- Learns industry-specific language
- Matches client communication styles

### 4. **Efficiency**
- Reduces revision cycles
- Maintains style consistency automatically
- Speeds up document approval processes

## Testing

Run the included test script to verify functionality:

```bash
python test_style_extraction.py
```

The test script will:
1. Extract style guidelines from a sample document
2. Generate a report using the extracted style
3. Display the results and verify functionality

## File Storage

- **Style Guidelines**: Saved to `outputs/style_guidelines/`
- **Generated Reports**: Saved to `outputs/`
- **Caching**: Style guidelines are cached for reuse

## Error Handling

The system includes robust error handling:
- **Fallback to Standard Generation**: If style extraction fails, the system continues with normal generation
- **Graceful Degradation**: Missing style characteristics don't prevent generation
- **User Feedback**: Clear error messages guide users when issues occur

## Future Enhancements

Potential improvements for this feature:
1. **Multiple Example Support**: Learn from multiple example documents
2. **Style Templates**: Save and reuse common style patterns
3. **Advanced Style Metrics**: More sophisticated style analysis
4. **Real-time Preview**: Show style-guided content preview before full generation
5. **Style Comparison**: Compare generated content against example styles

## Troubleshooting

### Common Issues

1. **Style Extraction Fails**
   - Ensure example document has sufficient text content
   - Check that the document is readable (not image-only PDF)
   - Verify OpenAI API key is configured

2. **Generated Content Doesn't Match Style**
   - Example document may have inconsistent style
   - Try with a more representative example
   - Check that style guidelines were extracted correctly

3. **Performance Issues**
   - Style extraction adds processing time
   - Consider caching style guidelines for reuse
   - Use smaller example documents for faster processing

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed information about the style extraction and application process.
