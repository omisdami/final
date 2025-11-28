import logging
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_core.prompts.chat import PromptTemplate
from langgraph.graph import START
from langgraph.graph import END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import create_react_agent
import core.llm
import core.store
from core.agents.state import DocumentPreparationState
from core.agents.state import SectionState
from core.agents.state import TemplateSectionDef


logger = logging.getLogger(__name__)


QUERY_PROMPT = PromptTemplate.from_template(
    """You are a researcher for a specific section in a report.  According the the provided *Objective* and *Title*, formulate a query and apply the query to the tool provided to retrieve the information you need.
    Title: {{title}}
    Objective: {{objective}}
    """,
    template_format="mustache"
)


DRAFTING_PROMPT = PromptTemplate.from_template(
    """You are assigned to draft a section of a of a report.  Follw the *Instructions* strictly.  Use the *Content* as the sole source of information.  Write **only** the draft content.  Do **not** include commentary, explanations, or apologies.
    
    {{#style_guidance}}
    STYLE GUIDELINES TO FOLLOW:
    {{style_guidance}}
    
    {{/style_guidance}}

    Title: {{title}}
    Objective: {{instructions.objective}}
    Tone: {{instructions.tone}}
    Length: {{instructions.length}}
    Format: {{instructions.format}}

    # Content
    {{content}}
    """,
    template_format="mustache"
)


def format_style_guidance(style_guidelines: dict) -> str:
    """
    Format style guidelines into readable text for the drafting prompt.
    
    Args:
        style_guidelines (dict): Style guidelines dictionary
        
    Returns:
        str: Formatted style guidance text
    """
    if not style_guidelines:
        return ""
    
    def format_dict(d, indent=0):
        lines = []
        for key, value in d.items():
            label = key.replace('_', ' ').title()
            if isinstance(value, dict):
                lines.append(f"{'  ' * indent}{label}:")
                lines.extend(format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{'  ' * indent}{label}: {', '.join(str(v) for v in value[:5])}")
            else:
                lines.append(f"{'  ' * indent}{label}: {value}")
        return lines
    
    return "\n".join(format_dict(style_guidelines))


def create_query_agent(section: TemplateSectionDef, retriever_tool):
    agent = create_react_agent(
        core.llm.model,
        tools=[retriever_tool]
    )
    return agent


def query_node(state: SectionState):
    section = state["section"]
    logger.info("running query node: %s", section)
    retriever = core.store.as_retriever([section.source])
    if section.instructions:
        retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_relevant_information",
            "Search and return relavent information about the report"
        )
        agent = create_query_agent(section, retriever_tool)
        prompt = QUERY_PROMPT.format(
            title=section.title,
            objective=section.instructions.objective
        )
        response = agent.invoke({"messages": [("user", prompt)]})
        logger.debug("Query response: %s", response)
        return {"messages": [response["messages"][-1]]}
    else:
        raise TypeError("section instructions is None")


def drafting_node(state: SectionState):
    section = state["section"]
    logger.info("running drafting node: %s", section)
    prompt = DRAFTING_PROMPT.format(
        title=section.title,
        instructions=section.instructions,
        style_guidance=state["style_guidance"],
        content=state["messages"][-1].content
    )
    agent = create_react_agent(core.llm.model)
    response = agent.invoke({"messages": [{"user", prompt}]})
    logger.debug("Drafting response: %s", response)
    return {"messages": [response["messages"][-1]]}


def create_section_graph_limit_sources(sources: list[str]):
    retriever = core.store.as_retriever(sources)
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_relevant_information",
        "Search and return relavent information about the report"
    )

    workflow = StateGraph(SectionState)    
    workflow.add_node(query_node)
    workflow.add_node("retrieve", ToolNode([retriever_tool]))
    workflow.add_node(drafting_node)

    workflow.add_edge(START, "query_node")
    workflow.add_conditional_edges(
        "query_node",
        tools_condition,
        {
            "tools": "retrieve",
            END: END
        },
    )
    workflow.add_edge("retrieve", "drafting_node")
    workflow.add_edge("drafting_node", END)
    
    graph = workflow.compile()
    return graph


def create_section_graph(section: TemplateSectionDef):
    return create_section_graph_limit_sources([section.source])


if __name__ == "__main__":
    graph = create_section_graph_limit_sources([])
    chart = graph.get_graph().draw_mermaid()
    print(chart)
