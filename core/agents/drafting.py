import asyncio
import logging
from typing import Any
from typing import Iterable
from typing import Optional
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_core.prompts.chat import PromptTemplate
from langgraph.prebuilt import create_react_agent
import core.llm
from core.agents.section import create_section_graph
from core.agents.state import DocumentPreparationState
from core.agents.state import SectionState
from core.agents.state import TemplateSectionDef


logger = logging.getLogger(__name__)


drafting_agent = create_react_agent(
    core.llm.model,
    tools=[],
    prompt="""You are a highly skilled **Document Drafting Agent**.

    Based on previously extracted insights and user instructions, your task is to generate well-structured, formal, and paragraph-style content for specific sections (e.g., Executive Summary, Why This Company, Risk Assessment, Scope of Work, etc.).

    Unless told otherwise, write in **formal tone** using professional business language.

    Do not include the section title or any headings unless explicitly asked. Avoid bullet points unless the prompt specifically requests them.

    If the information available is insufficient to complete the draft, say so politely.

    Always end your output with the word:
    TERMINATE"""
)


drafting_prompt = PromptTemplate.from_template(
    """You are assigned to draft a section of a of a report.  Follw the specified instructions strictly.  According to the provided *Objective* and *Title*, use the provided tool to query for the relevant information you need.

    - Write **only** the draft content.
    - Do **not** include commentary, explanations, or apologies.
    - End each section with the marker: === END OF SECTION ===
    
    {{#style_guidance}}
    STYLE GUIDELINES TO FOLLOW:
    {{style_guidance}}
    
    {{/style_guidance}}

    Title: {{title}}
    Objective: {{instructions.objective}}
    Tone: {{instructions.tone}}
    Length: {{instructions.length}}
    Format: {{instructions.format}}
    """,
    template_format="mustache"
)


def walk_sections(
        sections: dict[str, TemplateSectionDef]
) -> Iterable[TemplateSectionDef]:
    for _, s in sections.items():
        yield s
        if subsections := s.subsections:
            yield from walk_sections(subsections)


async def fetch_section_draft(
        section: TemplateSectionDef,
        style_guidance: str
) -> str:
    if section.instructions:
        graph = create_section_graph(section)
        state = { "section": section, "style_guidance": style_guidance }
        output = await graph.ainvoke(state)
        return output["messages"][-1].content
    else:
        return ""


async def draft_sections(state: DocumentPreparationState):
    style_guidance = format_style_guidance(state.style_guidelines)
    all_draft_sections = [fetch_section_draft(s, style_guidance)
                          for s in walk_sections(state.sections)]
    contents = await asyncio.gather(*all_draft_sections)
    for s, c in zip(walk_sections(state.sections), contents):
        s.content = c


def get_extractions(
        section: TemplateSectionDef,
        source_extractions: dict[str, dict[str, dict[str, str]]]
) -> dict[str, str]:
    if extractions := source_extractions.get(section.source):
        return extractions.get(section.title) or {}
    else:
        return {}


def gen_prompt_source(
        sections: dict[str, TemplateSectionDef],
        source_extractions: dict[str, dict[str, dict[str, str]]]        
) -> Iterable[TemplateSectionDef]:
    for s in walk_sections(sections):
        s.data = get_extractions(s, source_extractions)
        yield s


def fill_contents(sections: dict[str, TemplateSectionDef], contents: list[str]):
    for s, c in zip(walk_sections(sections), contents):
        s.content = c


def format_style_guidance(style_guidelines: Optional[dict[str, Any]]) -> str:
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


async def drafting_node(state: DocumentPreparationState):
    await draft_sections(state)
    return { "sections": state.sections}
