import logging
import logging.config
import traceback
import yaml
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from core.workflows.document_pipeline import save_all_report_formats
from core.workflows.document_extraction import save_uploaded_file, extract_and_clean_text, load_report_structure
from core.workflows.document_drafting import flatten_report_sections
from core.workflows.document_editor import save_updated_outputs
from core.utils.text_extractor import extract_text
import os
import json
import uuid
from typing import List
from typing import Optional
import core.document

with open('logging.yaml', 'r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)
    print("logging configed with %s", config)

router = APIRouter()
load_dotenv()

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """
    Pydantic model for chat requests to the `/chat/` endpoint.

    Attributes:
        document_content (str): Full document text the user wants to ask about or modify.
        question (str): The user's specific question, instruction, or correction request.
    """
    document_content: str
    question: str

class FeedbackPayload(BaseModel):
    """
    Pydantic model for feedback submitted via the `/feedback/` endpoint.

    Attributes:
        uuid (str): Unique identifier of the processed document.
        rating (int): User rating from 1 to 5 (validated with Pydantic).
        feedback_type (str, optional): Auto-assigned type ("up", "down", or "neutral").
        document_content (str): Content of the document the feedback refers to.
        template_name (str): Name of the template used to generate the report.
        timestamp (str): Time when the feedback was submitted.
    """
    uuid: str
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = ""
    document_content: str
    template_name: str
    timestamp: str

@router.get("/templates/")
async def list_templates():
    """
    Lists all available JSON template files stored in the `templates` directory.

    Returns:
        dict: A dictionary containing either:
            - "available_templates": List of JSON template filenames
            - "error": Error message if directory listing fails
    """
    logger.info("Getting templates")
    template_dir = "templates"
    try:
        files = os.listdir(template_dir)    # Get all files from the templates directory
        json_files = [f for f in files if f.endswith(".json")]  # Filter only .json template files
        return {"available_templates": json_files}
    except Exception as e:
        return {"error": str(e)}    # Return error instead of raising HTTPException for template listing


@router.post("/process/")
async def process_document(
    files: List[UploadFile] = File(...),
    template_name: str = Form("proposal_template.json"),
    example_file: Optional[UploadFile] = File(None)
):
    """
    Accepts multiple PDF or DOCX files, extracts their content,
    and generates a structured report using the LangChain/LangGraph pipeline.

    Args:
        files (List[UploadFile]): Uploaded reference documents to process
        template_name (str): Name of the JSON template (default: "proposal_template.json")
        example_file (Optional[UploadFile]): Example document for style extraction and saving

    Returns:
        JSONResponse: Includes message, report, flattened sections, output paths
    """
    logger.info(f"Processing documents with template: {template_name}")
    
    # Validate template
    template_dir = "templates"
    try:
        template_files = os.listdir(template_dir)
        json_files = [f for f in template_files if f.endswith(".json")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

    if template_name not in json_files:
        raise HTTPException(status_code=400, detail="Invalid template name")

    try:
        # 1. Save all uploaded reference files and extract their text
        logger.info(f"Processing {len(files)} reference document(s)")
        extracted_texts = {}
        for file in files:
            file_path = save_uploaded_file(file)
            text = extract_and_clean_text(file_path)
            extracted_texts[file.filename] = text
            logger.info(f"Extracted {len(text)} chars from {file.filename}")

        # 2. Load JSON-based report structure template
        sections = load_report_structure(f"templates/{template_name}")

        # 3. Handle style guidance
        if example_file:
            example_file_path = save_uploaded_file(example_file)
            try:
                example_text = extract_text(example_file_path)
                os.unlink(example_file_path)
                logger.info(f"Extracted {len(example_text)} chars from example")
                                
            except Exception as e:
                logger.warning(f"Failed to extract style from example: {e}")
                if os.path.exists(example_file_path):
                    os.unlink(example_file_path)
                example_text = None
        else:
            example_text = None


        # 4. Generate report
        
        report_sections = await core.document.generate(
            sections,
            extracted_texts,
            example_document_text=example_text
        )
        
        # Convert Pydantic models to dictionaries for backward compatibility
        aggregated_report = {k: s.model_dump() for k, s in report_sections.items()}
        logger.info("Document generation completed")

        # 5. Generate document ID
        document_id = str(uuid.uuid4())

        # 6. Save the report in different formats
        output_paths = save_all_report_formats(
            aggregated_report,
            "multiple_files_combined.docx"
        )

        # 7. Flatten report for frontend
        flattened = flatten_report_sections(aggregated_report)

        response_data = {
            "message": "Full report successfully generated",
            "uuid": document_id,
            "report_sections": aggregated_report,
            "flattened_sections": flattened,
            **output_paths
        }
        
        
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@router.post("/chat/")
async def chat_about_document(data: ChatRequest):
    """
    Sends the document content and user instruction to the Editor AI agent for
    review, corrections, or improvements. Returns the AI-generated response
    and updated output files.

    Args:
        data (ChatRequest): Pydantic model containing:
            - document_content (str): Full document content for review
            - question (str): User's instruction or query for the document

    Returns:
        dict: Contains:
            - "answer" (str): AI editor's response
            - "uuid" (str): New unique document identifier
            - Paths to updated outputs

    Raises:
        HTTPException: If any error occurs during the chat process.
    """

    try:
        response = core.document.edit(data.question, data.document_content)

        # Save updated content to output formats
        output_paths = save_updated_outputs(response)

        # Generate new document UUID for tracking
        new_uuid = str(uuid.uuid4())

        return {
            "answer": response,
            "uuid": new_uuid,
            **output_paths
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

@router.post("/feedback/")
async def save_feedback(feedback: FeedbackPayload):
    """
    Saves user feedback about generated reports to a JSON log file.
    Feedback includes ratings, document content, and template used.

    Args:
        feedback (FeedbackPayload): Contains:
            - uuid (str): Document UUID
            - rating (int): 1 to 5 star rating
            - document_content (str): Content of the reviewed document
            - template_name (str): Template used for report generation
            - timestamp (str): Time feedback was submitted

    Returns:
        dict: Success message on successful feedback save.

    Raises:
        HTTPException: If writing to the feedback file fails.
    """
    try:
        feedback_dir = "feedback_data"  # Ensure feedback directory exists
        os.makedirs(feedback_dir, exist_ok=True)

        feedback_file = os.path.join(feedback_dir, "feedback_log.json")

        new_entry = feedback.dict() # Convert Pydantic model to dictionary

        # Map numeric rating to feedback type
        rating = new_entry.get("rating", 3)
        if rating in [4, 5]:
            new_entry["feedback_type"] = "up"
        elif rating in [1, 2]:
            new_entry["feedback_type"] = "down"
        else:
            new_entry["feedback_type"] = "neutral"

        # Load existing feedback if file exists
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        existing_data.append(new_entry) # Append new feedback entry

        # Save updated feedback log
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)

        return {"message": "Feedback recorded successfully."}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {e}")

@router.post("/targeted-edit/")
async def targeted_edit_document(
    example_file: UploadFile = File(...),
    reference_files: List[UploadFile] = File(...),
    section_changes: str = Form(...)  # JSON array
):
    """
    Edit specific sections of an example document using targeted editing.    
    Args:
        example_file (UploadFile): Base document to modify (PDF/DOCX)
        reference_files (List[UploadFile]): Reference materials for new content (PDF/DOCX)
        section_changes (str): JSON array of section modifications:
            [
                {
                    "section_name": "Section name to modify",
                    "user_direction": "How to change this section"
                }
            ]    
    Returns:
        JSONResponse: Contains:
            - message (str): Success message
            - output_file (str): Path to edited document
            - stats (dict): Editing statistics
                - total_sections (int): Total sections in document
                - modified (int): Sections that were changed
                - unchanged (int): Sections kept as-is
    
    """
    import traceback
    from datetime import datetime
    
    try:
        logger.info("Starting targeted editing workflow")
        
        # Save and extract example file (preserve structure for heading detection)
        example_path = save_uploaded_file(example_file)
        example_text = extract_and_clean_text(example_path, preserve_structure=True)
        logger.info(f"Loaded example document: {example_file.filename} ({len(example_text)} chars)")
        
        # Save and extract reference files (preserve structure)
        reference_texts = {}
        reference_paths = []  # Track paths for cleanup
        for ref_file in reference_files:
            ref_path = save_uploaded_file(ref_file)
            reference_paths.append(ref_path)
            reference_texts[ref_file.filename] = extract_and_clean_text(ref_path, preserve_structure=True)
            logger.info(f"Loaded reference document: {ref_file.filename}")
        
        # Parse section changes
        changes = json.loads(section_changes)
        logger.info(f"Received {len(changes)} section change requests")
        
        # Validate section changes
        if not changes or len(changes) == 0:
            raise HTTPException(status_code=400, detail="No section changes specified")
        
        for change in changes:
            if "section_name" not in change or "user_direction" not in change:
                raise HTTPException(
                    status_code=400,
                    detail="Each section change must have 'section_name' and 'user_direction'"
                )
        
        # Generate output filename
        base_name = os.path.splitext(example_file.filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"outputs/targeted_edit_{base_name}_{timestamp}.docx"
        
        # Run targeted editing workflow
        logger.info("Executing targeted editing pipeline...")
        result = await core.document.targeted_edit(
            example_document_text=example_text,
            reference_texts=reference_texts,
            section_changes=changes,
            output_filename=output_filename
        )
        
        # Cleanup temp files
        try:
            os.unlink(example_path)
            for ref_path in reference_paths:
                if os.path.exists(ref_path):
                    os.unlink(ref_path)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup error: {cleanup_error}")
        
        logger.info(f"Targeted editing complete: {output_filename}")
        logger.info(f"Stats: {result['stats']['modified']} modified, {result['stats']['unchanged']} unchanged")
        
        return JSONResponse(content={
            "message": "Document sections edited successfully",
            "output_file": output_filename,
            "stats": result["stats"],
            "sections_modified": result["stats"]["modified"],
            "sections_unchanged": result["stats"]["unchanged"],
            "total_sections": result["stats"]["total_sections"]
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in section_changes: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON format in section_changes: {str(e)}")
        
    except Exception as e:
        logger.error(f"Targeted editing failed: {e}", exc_info=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Targeted editing failed: {str(e)}")
