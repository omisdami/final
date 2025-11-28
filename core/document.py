import json
import logging
from typing import Any
from typing import Optional
from langgraph.types import Command
from core.agents.state import TemplateInstruction
from core.agents.state import TemplateSectionDef
from core.agents.state import DocumentPreparationState
from core.agents.graph import get_graph
from core.agents.style_extractor import style_extractor_agent, style_extractor_prompt, parse_style_response
import core.store


logger = logging.getLogger(__name__)


# Single graph with conditional style extraction routing
graph = get_graph()


def get_agent_config():
    return {"configurable": {"thread_id": "1"}}


def to_instruction(source: dict[str, str]) -> TemplateInstruction:
    return TemplateInstruction(
        objective=source.get("objective", ""),
        tone=source.get("tone", ""),
        length=source.get("length", ""),
        format=source.get("format", "")
    )


def to_section_def(section: dict[str, Any]) -> TemplateSectionDef:
    subsections = section.get("subsections", {})
    instructions = section.get("instructions", {})
    return TemplateSectionDef(
        title=section["title"],
        subsections={ k: to_section_def(s) for k, s in subsections.items() },
        source=section.get("source", ""),
        instructions=to_instruction(instructions) if instructions else None,
        content=""
    )


async def generate(
        sections: dict[str, Any],
        source_texts: dict[str, str],
        example_document_text: Optional[str] = None,
        rag_params: Optional[Any] = None
) -> dict[str, TemplateSectionDef]:
    """
    Generate a document using the LangGraph pipeline with optional style guidance.

    Args:
        sections (dict): Section structure and instructions
        source_texts (dict): Reference documents for data extraction
        example_document_text (Optional[str]): Example document for style extraction
        rag_params (Optional[RagParameters]): RAG configuration parameters

    Returns:
        dict[str, TemplateSectionDef]: Generated section definitions
    """
    logger.info("Generating document %s", sections)
    section_defs = { k: to_section_def(s) for k, s in sections.items()}

    # Clear vector store to prevent contamination from previous runs
    core.store.clear_store()

    if rag_params:
        logger.info(f"Using custom RAG parameters: threshold={rag_params.similarity_threshold}, "
                   f"top_k={rag_params.top_k}, chunk_size={rag_params.chunk_size}, "
                   f"overlap={rag_params.overlap}%")

    logger.info(f"Loading {len(source_texts)} source document(s) into vector store")
    core.store.add_sources(source_texts, rag_params=rag_params)
    
    # Create state - graph will conditionally route based on example_document_text
    if example_document_text and example_document_text.strip():
        logger.info("Example document provided - will extract style during generation")
    else:
        logger.info("No example document - standard generation")
    
    state = DocumentPreparationState(
        sections=section_defs,
        source_texts=source_texts,
        source_extractions={},
        style_guidelines=None,
        example_document_text=example_document_text,
        revision_question="",
        revision=""
    )

    # Single graph with conditional routing based on state
    # current using thread_id value of 1,
    # it should be dynamically generated for each user
    report_state = await graph.ainvoke(state, config=get_agent_config())
    return report_state["sections"]


def edit(question: str, content: str):
    values = {
        "revision_question": question,
        "revision": content
    }

    # Was interrupt for human revision, resume now
    edited_state = graph.invoke(
        Command(resume=values),
        config=get_agent_config()
    )
    return edited_state["revision"]


async def targeted_edit(
    example_document_text: str,
    reference_texts: dict[str, str],
    section_changes: list[dict],
    output_filename: str,
    rag_params: Optional[Any] = None
) -> dict:
    """
    Run targeted section editing workflow using LangGraph.

    This function takes an example document and selectively modifies specified
    sections based on user directions and reference materials, while keeping
    all other sections unchanged.

    Args:
        example_document_text (str): Full text of the example document
        reference_texts (dict[str, str]): Reference documents {filename: content}
        section_changes (list[dict]): List of sections to change, each with:
            - section_name (str): Name of the section to modify
            - user_direction (str): Instructions for how to change it
        output_filename (str): Path where the edited document will be saved
        rag_params (Optional[RagParameters]): RAG configuration parameters

    Returns:
        dict: Final state containing:
            - stats (dict): Statistics about the editing process
                - total_sections (int): Total number of sections
                - modified (int): Number of sections that were changed
                - unchanged (int): Number of sections kept as-is
    """
    from core.agents.targeted_editing_graph import get_targeted_editing_graph
    from core.agents.state import TargetedEditingState, SectionChange

    logger.info("Starting targeted editing workflow")
    logger.info(f"Sections to modify: {len(section_changes)}")

    # Convert section changes to SectionChange objects
    changes = [
        SectionChange(
            section_name=change["section_name"],
            user_direction=change["user_direction"]
        )
        for change in section_changes
    ]

    # Clear vector store to prevent contamination from previous runs
    core.store.clear_store()

    if rag_params:
        logger.info(f"Using custom RAG parameters for targeted editing")

    logger.info(f"Loading {len(reference_texts)} source document(s) into vector store")
    core.store.add_sources(reference_texts, rag_params=rag_params)
    
    # Create initial state
    initial_state = TargetedEditingState(
        example_document_text=example_document_text,
        reference_texts=reference_texts,
        section_changes=changes,
        output_filename=output_filename
    )
    
    # Build and run graph
    graph = get_targeted_editing_graph()
    config = {"configurable": {"thread_id": "targeted_edit"}}
    
    logger.info("Executing targeted editing pipeline...")
    final_state = await graph.ainvoke(initial_state, config=config)
    
    logger.info("Targeted editing complete")
    logger.info(f"Modified: {final_state['stats']['modified']}, Unchanged: {final_state['stats']['unchanged']}")
    
    return final_state