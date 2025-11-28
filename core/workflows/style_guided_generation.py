from core.config.llm_config import get_llm_config
from core.agents.extractor_agent import get_extractor_agent
from core.agents.drafting_agent import get_drafting_agent
from core.agents.style_extractor_agent import get_style_extractor_agent
from core.agents.user_proxy_agent import get_user_proxy_agent
from core.utils.style_utils import (
    extract_document_style, 
    apply_style_to_instructions, 
    save_style_guidelines,
    load_style_guidelines
)
from core.workflows.document_extraction import extract_and_clean_text
from core.workflows.document_pipeline import generate_report
from typing import Dict, List, Tuple, Optional
import os

def extract_style_from_example(example_file_path: str, save_guidelines: bool = True) -> Dict:
    """
    Extract style guidelines from an example document.
    
    Args:
        example_file_path (str): Path to the example document
        save_guidelines (bool): Whether to save the extracted guidelines
        
    Returns:
        Dict: Extracted style guidelines
    """
    # Initialize agents
    llm_config = get_llm_config()
    style_extractor_agent = get_style_extractor_agent(llm_config)
    user_proxy = get_user_proxy_agent(llm_config)
    
    # Extract text from example document
    example_text = extract_and_clean_text(example_file_path)
    
    if not example_text.strip():
        raise ValueError("Could not extract text from example document")
    
    # Extract style guidelines
    print(f"[Style Extraction] Analyzing example document: {os.path.basename(example_file_path)}")
    style_guidelines = extract_document_style(example_text, style_extractor_agent, user_proxy)
    
    # Save guidelines if requested
    if save_guidelines and style_guidelines:
        saved_path = save_style_guidelines(
            style_guidelines, 
            f"example_{os.path.splitext(os.path.basename(example_file_path))[0]}"
        )
        print(f"[Style Extraction] Style guidelines saved to: {saved_path}")
    
    return style_guidelines

def generate_style_guided_report(
    sections: dict, 
    extracted_text: dict, 
    style_guidelines: Dict, 
    filename: str
) -> Tuple[dict, str]:
    """
    Generate a report using extracted style guidelines.
    
    Args:
        sections (dict): Report structure and instructions
        extracted_text (dict): Extracted text from reference documents
        style_guidelines (Dict): Style guidelines from example document
        filename (str): Output filename
        
    Returns:
        Tuple[dict, str]: Generated report structure and full text
    """
    print("[Style-Guided Generation] Applying style guidelines to section instructions")
    
    # Enhance section instructions with style guidelines
    enhanced_sections = apply_style_guidelines_to_sections(sections, style_guidelines)
    
    # Use the enhanced sections in the standard report generation pipeline
    return generate_report(enhanced_sections, extracted_text, filename)

def apply_style_guidelines_to_sections(sections: dict, style_guidelines: Dict) -> dict:
    """
    Apply style guidelines to all sections in the report structure.
    
    Args:
        sections (dict): Original section structure
        style_guidelines (Dict): Extracted style guidelines
        
    Returns:
        dict: Enhanced section structure with style guidance
    """
    enhanced_sections = {}
    
    for section_key, section_data in sections.items():
        enhanced_section = section_data.copy()
        
        # Handle sections with subsections
        if "subsections" in section_data:
            enhanced_subsections = {}
            for sub_key, sub_data in section_data["subsections"].items():
                enhanced_sub = sub_data.copy()
                if "instructions" in enhanced_sub:
                    enhanced_sub["instructions"] = apply_style_to_instructions(
                        enhanced_sub["instructions"], 
                        style_guidelines
                    )
                enhanced_subsections[sub_key] = enhanced_sub
            enhanced_section["subsections"] = enhanced_subsections
        
        # Handle top-level sections
        else:
            if "instructions" in enhanced_section:
                enhanced_section["instructions"] = apply_style_to_instructions(
                    enhanced_section["instructions"], 
                    style_guidelines
                )
        
        enhanced_sections[section_key] = enhanced_section
    
    return enhanced_sections


def generate_report_with_example_style(
    sections: dict, 
    extracted_text: dict, 
    example_file_path: str, 
    filename: str,
    use_cached_style: bool = True
) -> Tuple[dict, str, Dict]:
    """
    Complete workflow to generate a report using style from an example document.
    
    Args:
        sections (dict): Report structure
        extracted_text (dict): Reference document content
        example_file_path (str): Path to example document
        filename (str): Output filename
        use_cached_style (bool): Whether to use cached style guidelines if available
        
    Returns:
        Tuple[dict, str, Dict]: Report structure, full text, and style guidelines used
    """
    # Check for cached style guidelines
    example_name = os.path.splitext(os.path.basename(example_file_path))[0]
    cache_path = f"outputs/style_guidelines/example_{example_name}.json"
    
    style_guidelines = {}
    
    if use_cached_style and os.path.exists(cache_path):
        print(f"[Style-Guided] Loading cached style guidelines from: {cache_path}")
        style_guidelines = load_style_guidelines(cache_path)
    
    if not style_guidelines:
        print(f"[Style-Guided] Extracting new style guidelines from: {example_file_path}")
        style_guidelines = extract_style_from_example(example_file_path, save_guidelines=True)
    
    if not style_guidelines:
        print("[Style-Guided] Warning: No style guidelines extracted, using standard generation")
        return generate_report(sections, extracted_text, filename), {}
    
    # Generate report with style guidelines
    print("[Style-Guided] Generating report with extracted style guidelines")
    report_structure, full_text = generate_style_guided_report(
        sections, extracted_text, style_guidelines, filename
    )
    
    return report_structure, full_text, style_guidelines
