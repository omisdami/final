from langchain_core.prompts.chat import PromptTemplate
from langgraph.types import interrupt
from langgraph.prebuilt import create_react_agent
import core.llm
from core.agents.state import DocumentPreparationState
from core.agents.state import TemplateSectionDef


editor_agent = create_react_agent(
    core.llm.model,
    tools=[],
    prompt="""You are a highly capable document revision assistant. Your role is to apply user-specified corrections to an existing document or report.

    - Modify the document content according to the user's request.
    - Preserve all other content unless directly related to the change.
    - Return the **entire updated document as text**, preserving the original structure and formatting.
    - Do not explain your changes — only return the revised document.

    End your response with: TERMINATE"""
)


editor_prompt = PromptTemplate.from_template(
    """You are a document revision assistant. Your task is to revise the existing document content according to the user's request.

    Instructions:
    - Apply only the requested change. Do not modify unrelated content.
    - Return the **entire updated document** after applying the correction, but exclude any prompt markers like '--- DOCUMENT START ---' and '--- DOCUMENT END ---'.
    - Preserve the original document structure and formatting.
    - Do not explain your changes — only return the updated document as plain text.

    --- DOCUMENT START ---
    {document}
    --- DOCUMENT END ---

    User's question:
    {question}

    Return only the updated structured document.
    End your response with: TERMINATE"""
)


def human_revision_node(state: DocumentPreparationState):
    revision_request = interrupt({"text_to_revise": state.revision})
    return revision_request


def editor_node(state: DocumentPreparationState):
    prompt = editor_prompt.format(
        document=state.revision,
        question=state.revision_question
    )
    responses = editor_agent.invoke({"messages": [("user", prompt)]})
    revision = responses["messages"][-1].text()

    return { "revision": revision }
