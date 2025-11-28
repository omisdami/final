from langgraph.graph import START
from langgraph.graph import END
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from core.agents.extractor import extractor_node
from core.agents.style_extractor import style_extractor_node
from core.agents.drafting import drafting_node
from core.agents.editor import human_revision_node
from core.agents.editor import editor_node
from core.agents.state import DocumentPreparationState


def should_extract_style(state: DocumentPreparationState) -> str:
    """
    Conditional edge function to determine if style extraction should be performed.
    
    Args:
        state (DocumentPreparationState): Current state
        
    Returns:
        str: "style_extractor_node" if example document exists, else "drafting_node"
    """
    if state.example_document_text and state.example_document_text.strip():
        return "style_extractor_node"
    return "drafting_node"


def get_graph():
    """
    Build the LangGraph workflow for document preparation.
    Uses conditional routing to optionally include style extraction based on state.
    
    Returns:
        Compiled LangGraph instance
    """
    revision_required = lambda s: bool(s.revision_question)

    builder = StateGraph(DocumentPreparationState)
    
    # Add all nodes
    builder.add_node(extractor_node)
    builder.add_node(style_extractor_node)
    builder.add_node(drafting_node)
    builder.add_node(human_revision_node)
    builder.add_node(editor_node)
    
    # Define the workflow with conditional routing
    builder.add_edge(START, "extractor_node")
    
    # After extraction, conditionally go to style extraction or drafting
    builder.add_conditional_edges(
        "extractor_node",
        should_extract_style,
        {
            "style_extractor_node": "style_extractor_node",
            "drafting_node": "drafting_node"
        }
    )
    
    # Style extraction leads to drafting
    builder.add_edge("style_extractor_node", "drafting_node")
    
    # Rest of the workflow
    builder.add_edge("drafting_node", "human_revision_node")
    builder.add_conditional_edges("human_revision_node", revision_required, {
        True: "editor_node",
        False: END
    })
    builder.add_edge("editor_node", "human_revision_node")
    
    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    return graph


if __name__ == "__main__":
    # Display the graph with conditional routing
    print("=== Document Preparation Graph (with conditional style extraction) ===")
    graph_instance = get_graph().get_graph().draw_mermaid()
    print(graph_instance)
    print("\nNote: The graph conditionally routes to style_extractor_node if example_document_text is provided.")
