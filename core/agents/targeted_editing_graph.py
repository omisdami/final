from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from core.agents.state import TargetedEditingState
from core.agents.targeted_editing_nodes import (
    parse_example_node,
    edit_sections_node,
    assemble_document_node
)


def get_targeted_editing_graph():
    """
    Build LangGraph workflow for targeted section editing.
    
    Returns:
        Compiled LangGraph instance with checkpointer
    """
    
    # Create state graph
    builder = StateGraph(TargetedEditingState)
    
    # Add nodes
    builder.add_node("parse_example", parse_example_node)
    builder.add_node("edit_sections", edit_sections_node)
    builder.add_node("assemble_document", assemble_document_node)
    
    # Define edges (linear pipeline)
    builder.add_edge(START, "parse_example")
    builder.add_edge("parse_example", "edit_sections")
    builder.add_edge("edit_sections", "assemble_document")
    builder.add_edge("assemble_document", END)
    
    # Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


if __name__ == "__main__":
    # Visualize the graph using Mermaid
    graph = get_targeted_editing_graph()
    print("Targeted Editing Graph:")
    print(graph.get_graph().draw_mermaid())


