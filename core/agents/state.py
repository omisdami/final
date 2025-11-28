from typing import Any
from typing import Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel


class TemplateInstruction(BaseModel):
    """
    Represents instructions for generating a template.

    Attributes:
        objective (str): The main goal or purpose of the template.
        tone (Optional[str]): The tone to be used (e.g., formal, casual).
        length (Optional[str]): The desired length of the content (e.g., short, long).
        format (Optional[str]): The format of the content (e.g., bullet points, paragraphs).
    """
    objective: str
    tone: Optional[str]
    length: Optional[str]
    format: Optional[str]


class TemplateSectionDef(BaseModel):
    """
    Defines a section of a document template.

    Attributes:
        title (str): The title of the section.
        subsections (dict[str, TemplateSectionDef]): Nested subsections within this section.
        source (str): The reference source of the content for this section.
        instructions (Optional[TemplateInstruction]): Instructions specific to this section.
        content (str): The generated content of the section.
    """
    title: str
    subsections: dict[str, "TemplateSectionDef"]
    source: str
    instructions: Optional[TemplateInstruction]
    content: str

class DocumentPreparationState(BaseModel):
    """
    Represents the overall state of document preparation.

    Attributes:
        sections (dict[str, TemplateSectionDef]): Section definitions of the document.
        source_texts (dict[str, str]): Reference source texts used for generating the document.
        source_extractions (dict[str, dict[str, Any]]): Extracted data from the source texts.
        style_guidelines (Optional[dict[str, Any]]): Extracted style guidelines from example documents.
        example_document_text (Optional[str]): Text from example document for style extraction.
        revision_question (Optional[str]): A question to guide the revision process.
        revision (Optional[str]): The current revision text.
    """
    sections: dict[str, TemplateSectionDef]
    source_texts: dict[str, str]
    source_extractions: dict[str, dict[str, Any]]
    style_guidelines: Optional[dict[str, Any]]
    example_document_text: Optional[str]
    revision_question: Optional[str]
    revision: Optional[str]


class SectionState(MessagesState):
    section: TemplateSectionDef
    style_guidance: str


class SectionChange(BaseModel):
    """
    Specification for a section change in targeted editing.
    
    Attributes:
        section_name (str): Name of section to change
        user_direction (str): User's instructions for the change
    """
    section_name: str
    user_direction: str

class TargetedEditingState(BaseModel):
    """
    State for targeted section editing workflow.
    
    Attributes:
        example_document_text (str): Full text extracted from example document
        reference_texts (dict): Reference documents {filename: content}
        section_changes (list): Sections to change with directions
        output_filename (str): Path for output file
        example_sections (dict): Parsed sections from example
        modified_sections (dict): Sections that were changed
        stats (dict): Statistics about the editing process
    """
    # Input
    example_document_text: str
    reference_texts: dict[str, str]
    section_changes: list[SectionChange]
    output_filename: str
    
    # Intermediate
    example_sections: dict[str, dict] = {}
    modified_sections: dict[str, dict] = {}
    
    # Output
    stats: dict = {}


class SectionEditState(MessagesState):
    # Input
    section_title: str
    original_content: str
    user_direction: str
    full_document: str
    sources: list[str]
    
    # Output
    new_title: str = ""
    new_content: str = ""