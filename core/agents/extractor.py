import json
import logging
from typing import Any
from typing import Iterable
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
import core.llm
from core.agents.state import DocumentPreparationState
from core.agents.state import TemplateSectionDef


logger = logging.getLogger(__name__)


extractor_prompt = PromptTemplate.from_template(
    """You are a skilled **Document Extractor Agent**.

    You are provided with a document and a list of section titles.

    Your task is to extract relevant information from the document and organize it by section title, following these rules:

    1. Always provide a dictionary for **every section title**, even if the document does not have a literal matching heading.
    2. If the section does not explicitly exist in the document, **infer its content** using the most relevant facts that fulfill its intent.  
       - Example: "Why Company A" can be inferred from company overview, differentiators, proven impact, or any content that explains why the company is a strong partner.
    3. Structure the output as JSON-style, like:
       {
         "Section Title 1": {
           "Company Name": "Value",
           "Key Fact": "Value",
           ...
         },
         ...
       }
    4. Always include `"Company Name"` in every section.
    5. Only include facts from the document (no outside knowledge).
    6. End your message with **TERMINATE**.

    Section Titles:
    {{#titles}}
      {{.}}
    {{/titles}}

    --- START DOCUMENT ---
    {{source_text}}
    --- END DOCUMENT ---
    """,
    template_format="mustache"
)


extractor_agent = create_react_agent(
    core.llm.model,
    tools=[],
    prompt="""You are a skilled **Document Extractor Agent**.

    Your task is to analyze the full document content and extract **structured, factual information** organized by predefined section titles.

    Instructions:
    - For each section title provided, extract **relevant facts only** from the document.
    - Use dictionary format like: 
    {
      "Section Title": {
      "Company Name": "Value",
      "Key Fact": "Value",
      ...
      },
      ...
    }
    - Always include a Company Name key and value in every section for future reference.
    - If a section has no relevant information, return an empty object for that section.
    - Do NOT summarize or interpret — only extract direct facts and values.

    End your response with the word: TERMINATE"""
)


def collect_titles_with_same_source(
        sections: dict[str, TemplateSectionDef],
        source_file_name: str
) -> Iterable[str]:
    for _, s in sections.items():
        if s.source == source_file_name:
            yield s.title
        yield from collect_titles_with_same_source(
            s.subsections,
            source_file_name
        )
    
    
def extract_key_data(
        sections: dict[str, TemplateSectionDef],
        source_file_name: str,
        source_text: str
) -> dict[str, dict[str, Any]]:
    titles = collect_titles_with_same_source(sections, source_file_name)
    message = extractor_prompt.format(
        titles=titles,
        source_text=source_text
    )
    logger.debug("Extractor message: %s", message)
    response = extractor_agent.invoke({"messages": [("user", message)]})
    logger.debug("Extractor response: %s", response)
    extractions = response["messages"][-1].text()
    return json.loads(extractions.split("TERMINATE")[0])


def extractor_node(
        state: DocumentPreparationState
) -> dict[str, dict[str, Any]]:
    extractions = { source: extract_key_data(state.sections, source, text)
                    for source, text in state.source_texts.items() }
    logger.debug("Extraction key data: %s", extractions)
    return { "source_extractions": extractions }
