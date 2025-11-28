import logging
import re
import json
from core.agents.state import SectionEditState
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_core.prompts.chat import PromptTemplate
from core.llm import model
import core.store

logger = logging.getLogger(__name__)


QUERY_PROMPT_FOR_EDITING = PromptTemplate.from_template(
    """You are a researcher helping to rewrite a section of a document. 
    
    Section Title: {section_title}
    User's Editing Direction: {user_direction}
    
    Formulate a query and use the retrieval tool to find relevant information that will help rewrite this section according to the user's direction.
    """,
    template_format="mustache"
)


EDIT_SECTION_WITH_LLM_PROMPT = PromptTemplate.from_template(
    """You are rewriting the "{section_title}" section of a document. Your goal is to preserve the section's ORIGINAL PURPOSE and STRUCTURE while updating the content.

    **RETRIEVED REFERENCE MATERIALS:**
    {retrieved_content}

    **CHANGE DIRECTION:**
    {user_direction}

    **ORIGINAL SECTION TO REWRITE:**
    Section: {section_title}
    ```
    {original_content}
    ```

    **STRUCTURAL REQUIREMENTS (MUST PRESERVE):**
    - Original section length: ~{original_length} words (maintain similar length ±20%)
    - Number of paragraphs: {paragraph_count} (maintain same paragraph structure)
    {format_requirement}
    - Section's role: This section serves a specific purpose in the document - preserve that purpose while updating content

    **FULL DOCUMENT CONTEXT:**
    ```
    {document_context}
    ```

    **INSTRUCTIONS:**
    1. **Identify the purpose**: What is this section trying to accomplish in the original document?
    2. **Preserve the structure**: Keep the same format (paragraphs, lists, organization)
    3. **Maintain the role**: Ensure the rewritten section serves the same purpose as the original
    4. **Update content**: Apply the change direction: {user_direction}
    5. **Use references**: Draw new content from the reference materials provided
    6. **Match tone**: Keep the same level of formality and writing style as the original
    7. **Keep length**: Aim for similar word count (~{original_length} words)

    **OUTPUT REQUIREMENTS:**
    - Output a JSON object with two fields: "title" and "content"
    - "title": Update the section title based on the rewritten content
    - "content": The rewritten section content (no title, no explanations)
    - Preserve the original format (lists, paragraphs, etc.)
    - Maintain similar length and structure
    - Ensure the section still serves its original purpose in the document
    - Match the writing style of the full document

    {{
    "title": "Updated Section Title",
    "content": "Rewritten section content here..."
    }}

    Output (JSON only, no other text):
    """,
    template_format="mustache"
)


def create_section_editing_graph(sources: list[str]):
    """
    Create a LangGraph workflow for editing a single section.
    
    This graph performs RAG-based section editing:
    1. Query node: Formulates search query based on user direction
    2. Retrieve node: Fetches relevant documents from vector store
    3. Edit node: Rewrites section using retrieved context
    
    Args:
        sources: List of source filenames to limit RAG retrieval
        
    Returns:
        Compiled LangGraph for section editing
    """
    retriever = core.store.as_retriever(sources)
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_relevant_information",
        "Search and return relavent information about the report"
    )
    workflow = StateGraph(SectionEditState)
    workflow.add_node("query", query_node_for_section_editing)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node("edit_section_with_llm_node", edit_section_with_llm_node)

    workflow.add_edge(START, "query")
    workflow.add_conditional_edges(
        "query",
        tools_condition,
        {
            "tools": "retrieve",
            END: END
        },
    )
    workflow.add_edge("retrieve", "edit_section_with_llm_node")
    workflow.add_edge("edit_section_with_llm_node", END)

    graph = workflow.compile()
    return graph



def create_query_agent_for_editing(retriever_tool):
    """Create a ReAct agent with retrieval tool for query formulation."""
    agent = create_react_agent(
        model,
        tools=[retriever_tool]
    )
    return agent


def query_node_for_section_editing(state: SectionEditState):
    """
    Node that formulates a search query based on the editing task.
    
    Uses a ReAct agent to determine what information is needed from
    the reference documents to complete the editing task.
    """
    logger.info(f"Running query node for section: {state['section_title']}")
    retriever = core.store.as_retriever(state["sources"])
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_relevant_information",
        "Search and return relavent information about the report"
    )
    agent = create_query_agent_for_editing(retriever_tool)
    prompt = QUERY_PROMPT_FOR_EDITING.format(
        section_title=state["section_title"],
        user_direction=state["user_direction"]
    )
    
    response = agent.invoke({"messages": [("user", prompt)]})
    
    return {"messages": [response["messages"][-1]]}


def edit_section_with_llm_node(state: SectionEditState) -> dict:
    """
    Edit a section using LLM based on user direction and reference materials.
    
    Enhanced to preserve the original section's purpose and structure while
    updating the content based on retrieved reference materials.
    
    Args:
        state: SectionEditState containing section info and retrieved content
        
    Returns:
        dict with new_title and new_content
    """
    section_title = state["section_title"]
    original_content = state["original_content"]
    user_direction = state["user_direction"]
    full_document = state["full_document"]
    retrieved_content = state["messages"][-1].content
    
    # Analyze original section structure
    original_length = len(original_content.split())
    has_bullets = '•' in original_content or '-' in original_content or '*' in original_content
    has_numbers = any(line.strip().startswith(tuple(str(i) + '.' for i in range(1, 10))) for line in original_content.split('\n'))
    paragraph_count = len([p for p in original_content.split('\n\n') if p.strip()])
    
    # Pre-compute template values
    if has_bullets or has_numbers:
        format_requirement = "- Contains bullet points or lists (preserve this format)"
    else:
        format_requirement = "- Written in paragraph form (maintain this style)"
    
    document_context = full_document[:5000] + ("..." if len(full_document) > 5000 else "")
    
    prompt = EDIT_SECTION_WITH_LLM_PROMPT.format(
        section_title=section_title,
        original_content=original_content,
        user_direction=user_direction,
        retrieved_content=retrieved_content,
        original_length=original_length,
        format_requirement=format_requirement,
        document_context=document_context,
        paragraph_count=paragraph_count
    )
    
    # Call LLM
    logger.debug(f"Calling LLM for section: {section_title}")
    response = model.invoke(prompt)
    response_text = response.content if hasattr(response, 'content') else str(response)
    
    # Clean up response (remove markdown, explanations) and extract JSON
    cleaned_text = clean_llm_response(response_text)
    result = json.loads(cleaned_text)
    new_title = result.get("title", section_title)  # Fallback to original if missing
    new_content = result.get("content", "")

    if not new_content:
        logger.warning(f"Empty content in LLM response for section '{section_title}'")
        new_content = original_content  # Fallback to original
    
    # Validate output preserves structure
    new_length = len(new_content.split())
    length_ratio = new_length / original_length if original_length > 0 else 1.0
    
    # Log quality metrics
    logger.info(f"  Section '{section_title}' editing complete:")
    logger.info(f"    Original length: {original_length} words")
    logger.info(f"    New length: {new_length} words ({length_ratio:.1%} of original)")
    
    # Warn if length differs significantly
    if length_ratio < 0.5 or length_ratio > 2.0:
        logger.warning(f"Length changed significantly ({length_ratio:.1%})")
        logger.warning(f"Consider refining user direction or regenerating")
    
    # Warn if structure appears to have changed
    new_paragraph_count = len([p for p in new_content.split('\n\n') if p.strip()])
    if abs(new_paragraph_count - paragraph_count) > 2:
        logger.warning(f"Paragraph structure changed ({paragraph_count} → {new_paragraph_count})")
    
    return {
        "new_title": new_title,
        "new_content": new_content
    }


def clean_llm_response(text: str) -> str:
    """
    Clean up LLM response to extract JSON content.
    
    Handles various formats:
    - Plain JSON
    - JSON in code blocks (```json ... ```)
    - JSON with extra explanatory text
    
    Args:
        text: Raw LLM response text
        
    Returns:
        Cleaned JSON string
    """
    # First, try to find JSON object in the text using regex
    # Look for {...} pattern (JSON object)
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        # Try to parse it to validate it's valid JSON
        try:
            json.loads(json_str)  # Validate it's valid JSON
            return json_str.strip()
        except json.JSONDecodeError:
            pass  # Continue to other methods
    
    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    
    # Remove common prefixes that might appear before JSON
    prefixes = [
        "Here is the result:",
        "Here's the output:",
        "Output:",
        "Result:",
        "JSON:",
        "Here is the rewritten section:",
        "Rewritten section:",
        "Here's the updated content:",
        "Updated content:",
        "Here is the modified section:",
    ]
    for prefix in prefixes:
        if text.strip().lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
    
    # Try to find JSON object again after cleaning
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(0)
        try:
            json.loads(json_str)  # Validate
            return json_str.strip()
        except json.JSONDecodeError:
            pass
    
    # If no JSON found, return cleaned text (might be plain JSON)
    cleaned = text.strip()
    
    # Try to parse as-is to validate
    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        # If it's not valid JSON, log warning and return as-is
        logger.warning("Could not extract valid JSON from LLM response, returning cleaned text")
        return cleaned

