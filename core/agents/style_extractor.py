import json
import logging
from typing import Any, Dict
from datetime import datetime
import os
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
import core.llm
from core.agents.state import DocumentPreparationState


logger = logging.getLogger(__name__)


style_extractor_prompt = PromptTemplate.from_template(
    """You are a skilled **Document Style Extractor Agent**.

    Your task is to analyze example documents and extract comprehensive style guidelines that can be used to generate similar documents.

    Instructions:
    - Analyze the document's writing style, tone, structure, and formatting patterns
    - Extract specific style characteristics including:
      * Tone and voice (formal, conversational, technical, persuasive, etc.)
      * Sentence structure patterns (length, complexity, active/passive voice)
      * Paragraph organization (length, flow, transitions)
      * Professional language patterns and terminology usage
      * Formatting preferences (headings, lists, emphasis)
      * Document structure and section organization
      * Content depth and detail level
      * Use of examples, statistics, or supporting evidence

    Output format should be a structured dictionary like:
    {{
        "writing_style": {{
            "tone": "Description of overall tone",
            "voice": "Description of voice characteristics",
            "formality_level": "formal/semi-formal/informal",
            "technical_complexity": "high/medium/low"
        }},
        "sentence_patterns": {{
            "average_length": "short/medium/long",
            "complexity": "simple/compound/complex",
            "voice_preference": "active/passive/mixed"
        }},
        "paragraph_style": {{
            "length": "short/medium/long",
            "organization": "Description of how paragraphs are structured",
            "transition_style": "Description of how ideas connect"
        }},
        "language_patterns": {{
            "terminology": ["List of key terms and phrases"],
            "professional_language": "Description of professional language use",
            "industry_specific": ["Industry-specific terms and concepts"]
        }},
        "formatting_preferences": {{
            "heading_style": "Description of heading patterns",
            "list_usage": "How lists are used (bullets, numbers, etc.)",
            "emphasis_methods": "How emphasis is applied (bold, italics, etc.)"
        }},
        "content_characteristics": {{
            "detail_level": "high/medium/low",
            "evidence_usage": "Description of how evidence is presented",
            "example_integration": "How examples are incorporated"
        }},
        "document_structure": {{
            "section_organization": "Description of how sections are organized",
            "flow_pattern": "Description of document flow",
            "conclusion_style": "How documents are concluded"
        }}
    }}

    --- START EXAMPLE DOCUMENT ---
    {example_text}
    --- END EXAMPLE DOCUMENT ---

    Analyze the document and provide the style guidelines as a valid JSON dictionary.
    End your response with: TERMINATE"""
)


style_extractor_agent = create_react_agent(
    core.llm.model,
    tools=[],
    prompt="""You are a skilled **Document Style Extractor Agent**.

    Your task is to analyze the full document content and extract **comprehensive style guidelines** that can be used to generate similar documents.

    Instructions:
    - Analyze writing style, tone, structure, and formatting patterns
    - Extract specific style characteristics
    - Output as a structured JSON dictionary
    - Focus on patterns that can be replicated in new documents
    - Be specific and actionable in your descriptions

    End your response with the word: TERMINATE"""
)


def parse_style_response(response_text: str) -> dict[str, Any]:
    """
    Parse the style extractor agent's response into a structured format.
    
    Args:
        response_text (str): Raw response from the style extractor agent
        
    Returns:
        dict[str, Any]: Parsed style guidelines
    """
    try:
        # Remove TERMINATE marker
        cleaned = response_text.split("TERMINATE")[0].strip()
        
        # Try to find and parse JSON content
        if "{" in cleaned and "}" in cleaned:
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}") + 1
            json_text = cleaned[start_idx:end_idx]
            
            # Parse as JSON
            parsed_dict = json.loads(json_text)
            return parsed_dict
        else:
            # Fallback: return raw analysis
            logger.warning("Could not parse style response as JSON")
            return {
                "raw_analysis": cleaned,
                "extraction_note": "Style analysis provided in text format"
            }
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "raw_analysis": response_text,
            "parse_error": str(e)
        }
    except Exception as e:
        logger.error(f"Error parsing style response: {e}")
        return {
            "raw_analysis": response_text,
            "error": str(e)
        }

def save_style_guidelines(style_guidelines: Dict[str, Any], filename: str = None) -> str:
    """
    Save extracted style guidelines to a JSON file.
    
    Args:
        style_guidelines (Dict[str, Any]): The style guidelines to save
        filename (str, optional): Custom filename, otherwise auto-generated
        
    Returns:
        str: Path to the saved file
    """
    output_dir = "outputs/style_guidelines"
    os.makedirs(output_dir, exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"style_guidelines_{timestamp}.json"
    
    if not filename.endswith('.json'):
        filename += '.json'
    
    filepath = os.path.join(output_dir, filename)
    
    # Add metadata
    style_data = {
        "extracted_at": datetime.now().isoformat(),
        "style_guidelines": style_guidelines
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(style_data, f, indent=2, ensure_ascii=False)
    
    return filepath
    
def style_extractor_node(state: DocumentPreparationState) -> dict[str, Any]:
    """
    LangGraph node that extracts style guidelines from an example document.
    
    Args:
        state (DocumentPreparationState): Current state with example_document_text
        
    Returns:
        dict: Updated state with style_guidelines
    """
    # Skip if no example document provided
    if not state.example_document_text or not state.example_document_text.strip():
        logger.info("No example document provided, skipping style extraction")
        return {"style_guidelines": None}
    
    logger.info("Extracting style guidelines from example document")
    
    # Create prompt
    message = style_extractor_prompt.format(
        example_text=state.example_document_text
    )
    
    logger.debug("Style extraction prompt: %s", message[:500])
    
    # Call style extractor agent
    response = style_extractor_agent.invoke({"messages": [("user", message)]})
    
    logger.debug("Style extractor response: %s", response)
    
    # Extract and parse the response
    style_text = response["messages"][-1].content
    style_guidelines = parse_style_response(style_text)
    
    logger.info("Style guidelines extracted: %s", list(style_guidelines.keys()))

    try:
        saved_path = save_style_guidelines(style_guidelines)
        logger.info("Style guidelines saved to: %s", saved_path)
    except Exception as e:
        logger.error("Failed to save style guidelines: %s", e)
    
    return {"style_guidelines": style_guidelines}

