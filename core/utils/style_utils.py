import json
import os
from datetime import datetime
from typing import Dict, Any
from ast import literal_eval

def extract_document_style(document_text: str, style_extractor_agent, user_proxy) -> Dict[str, Any]:
    """
    Extract style guidelines from an example document using the style extractor agent.
    
    Args:
        document_text (str): The full text content of the example document
        style_extractor_agent: The AutoGen style extractor agent
        user_proxy: The user proxy agent for chat management
        
    Returns:
        Dict[str, Any]: Structured style guidelines extracted from the document
    """
    
    style_extraction_prompt = f"""
        Analyze the following document and extract comprehensive style guidelines that can be used to generate similar documents.
        
        Focus on identifying patterns in:
        - Writing tone and voice
        - Sentence and paragraph structure
        - Professional language usage
        - Formatting and organization
        - Content depth and presentation style
        
        --- START EXAMPLE DOCUMENT ---
        {document_text}
        --- END EXAMPLE DOCUMENT ---
        
        Please provide a detailed style analysis following the structured format specified in your instructions.
    """
    
    chat = user_proxy.initiate_chat(
        style_extractor_agent,
        message={"content": style_extraction_prompt},
        human_input_mode="NEVER"
    )
    
    # Extract the agent's response
    final_texts = [
        msg["content"].strip()
        for msg in chat.chat_history
        if msg.get("name") == "style_extractor_agent" and msg["content"].strip() != "TERMINATE"
    ]
    
    if not final_texts:
        return {}
    
    final_output = final_texts[-1]
    
    try:
        # Clean and parse the style guidelines
        cleaned_output = final_output.split("TERMINATE")[0].strip()
        # Try to extract JSON-like structure from the response
        style_guidelines = parse_style_response(cleaned_output)
        return style_guidelines
    except Exception as e:
        print(f"Error parsing style guidelines: {e}")
        return {"raw_analysis": final_output}

def parse_style_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the style extractor agent's response into a structured format.
    
    Args:
        response_text (str): Raw response from the style extractor agent
        
    Returns:
        Dict[str, Any]: Parsed style guidelines
    """
    try:
        # Try to find and parse dictionary-like content
        if "{" in response_text and "}" in response_text:
            # Extract the dictionary portion
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            dict_text = response_text[start_idx:end_idx]
            
            # Attempt to parse as literal
            parsed_dict = literal_eval(dict_text)
            return parsed_dict
        else:
            # If no structured format found, create a basic structure
            return {
                "raw_analysis": response_text,
                "extraction_note": "Style analysis provided in text format"
            }
    except Exception:
        # Fallback: parse manually by looking for key patterns
        return parse_text_style_analysis(response_text)

def parse_text_style_analysis(text: str) -> Dict[str, Any]:
    """
    Manually parse style analysis from text format.
    
    Args:
        text (str): Text-based style analysis
        
    Returns:
        Dict[str, Any]: Structured style guidelines
    """
    style_dict = {
        "writing_style": {},
        "sentence_patterns": {},
        "paragraph_style": {},
        "language_patterns": {},
        "formatting_preferences": {},
        "content_characteristics": {},
        "document_structure": {}
    }
    
    # Simple keyword-based extraction
    lines = text.lower().split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identify sections
        if 'tone' in line and 'writing' in line:
            current_section = 'writing_style'
        elif 'sentence' in line:
            current_section = 'sentence_patterns'
        elif 'paragraph' in line:
            current_section = 'paragraph_style'
        elif 'language' in line or 'terminology' in line:
            current_section = 'language_patterns'
        elif 'format' in line or 'heading' in line:
            current_section = 'formatting_preferences'
        elif 'content' in line or 'detail' in line:
            current_section = 'content_characteristics'
        elif 'structure' in line or 'organization' in line:
            current_section = 'document_structure'
        
        # Extract key insights
        if current_section and ':' in line:
            key_value = line.split(':', 1)
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()
                style_dict[current_section][key] = value
    
    # Add raw text for reference
    style_dict["raw_analysis"] = text
    
    return style_dict

def apply_style_to_instructions(base_instructions: Dict[str, Any], style_guidelines: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance base section instructions with extracted style guidelines.
    
    Args:
        base_instructions (Dict[str, Any]): Original section instructions
        style_guidelines (Dict[str, Any]): Extracted style guidelines
        
    Returns:
        Dict[str, Any]: Enhanced instructions with style guidance
    """
    enhanced_instructions = base_instructions.copy()
    
    # Extract style characteristics
    writing_style = style_guidelines.get("writing_style", {})
    sentence_patterns = style_guidelines.get("sentence_patterns", {})
    paragraph_style = style_guidelines.get("paragraph_style", {})
    language_patterns = style_guidelines.get("language_patterns", {})
    content_characteristics = style_guidelines.get("content_characteristics", {})
    
    # Build style guidance text
    style_guidance = []
    
    if writing_style.get("tone"):
        style_guidance.append(f"Use a {writing_style['tone']} tone")
    
    if writing_style.get("formality_level"):
        style_guidance.append(f"Maintain {writing_style['formality_level']} language")
    
    if sentence_patterns.get("complexity"):
        style_guidance.append(f"Use {sentence_patterns['complexity']} sentence structures")
    
    if paragraph_style.get("length"):
        style_guidance.append(f"Write {paragraph_style['length']} paragraphs")
    
    if language_patterns.get("professional_language"):
        style_guidance.append(f"Professional language style: {language_patterns['professional_language']}")
    
    if content_characteristics.get("detail_level"):
        style_guidance.append(f"Provide {content_characteristics['detail_level']} level of detail")
    
    # Add style guidance to instructions
    if style_guidance:
        style_text = "Style Guidelines: " + "; ".join(style_guidance) + ". "
        
        # Add to existing instructions
        if isinstance(enhanced_instructions, dict):
            if "objective" in enhanced_instructions:
                enhanced_instructions["objective"] = style_text + enhanced_instructions["objective"]
            else:
                enhanced_instructions["style_guidance"] = style_text
        
        # Add terminology if available
        if language_patterns.get("terminology"):
            terminology_text = f"Use professional terminology including: {', '.join(language_patterns['terminology'][:5])}. "
            if "objective" in enhanced_instructions:
                enhanced_instructions["objective"] += terminology_text
    
    return enhanced_instructions

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

def load_style_guidelines(filepath: str) -> Dict[str, Any]:
    """
    Load style guidelines from a JSON file.
    
    Args:
        filepath (str): Path to the style guidelines file
        
    Returns:
        Dict[str, Any]: Loaded style guidelines
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("style_guidelines", {})
    except Exception as e:
        print(f"Error loading style guidelines: {e}")
        return {}

def merge_style_guidelines(primary_style: Dict[str, Any], secondary_style: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two sets of style guidelines, with primary taking precedence.
    
    Args:
        primary_style (Dict[str, Any]): Primary style guidelines
        secondary_style (Dict[str, Any]): Secondary style guidelines to merge
        
    Returns:
        Dict[str, Any]: Merged style guidelines
    """
    merged = secondary_style.copy()
    
    for key, value in primary_style.items():
        if key in merged and isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update(value)
        else:
            merged[key] = value
    
    return merged