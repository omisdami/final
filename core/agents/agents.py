from langchain.chat_models import init_chat_model
from langchain_core.prompts.chat import PromptTemplate
from langgraph.prebuilt import create_react_agent


model = model.init_chat_model(
    "gpt-4.1",
    temperature=0
)


drafting_prompt = PromptTemplate.from_template(
    """You are assigned to draft multiple sections of a report. For each section, follow the specified instructions strictly and use only the structured data provided.

    For every section:
    - Write **only** the draft content.
    - Do **not** include commentary, explanations, or apologies.
    - End each section with the marker: === END OF SECTION ===
    
    {{#sections}}
    SECTION: {{title}}
    {{#instructions}}
    Objective: {{objective}}
    Tone: {{tone}}
    Length: {{length}}
    Format: {{format}}
    {{/instructions}}

    Structured Data:
      {{data}}

    === END OF SECTION ===
    {{/sections}}
    """,
    template_format="mustache"
)


drafting_agent = create_react_agent(
    model,
    prompt: """You are a skilled **Document Extractor Agent**.

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
