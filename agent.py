import os
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from data import KNOWLEDGE_BASE, TICKETS

# Tools

@tool
def search_kb(query: str) -> str:
    """Search the Knowledge Base policies. Provide a query describing the issue."""
    # A simple keyword search for the prototype
    results = []
    query_words = query.lower().split()
    for kb in KNOWLEDGE_BASE:
        text = (kb["title"] + " " + kb["content"]).lower()
        if any(word in text for word in query_words):
            results.append(f"[{kb['id']}] {kb['title']}: {kb['content']}")
    
    if results:
        return "\n\n".join(results)
    return "No relevant policies found. Try different keywords."

@tool
def search_tickets(query: str) -> str:
    """Search the past ticket history for precedent. Provide a keyword query."""
    results = []
    query_words = query.lower().split()
    for tk in TICKETS:
        text = (tk["issue_summary"] + " " + tk["status"]).lower()
        if any(word in text for word in query_words):
            results.append(f"[{tk['id']}] {tk['issue_summary']} - Status: {tk['status']}")
    
    if results:
        return "\n".join(results)
    return "No matching tickets found."

@tool
def create_ticket(employee: str, email: str, issue_summary: str, status: str) -> str:
    """Create a structured ticket for the issue. 
    Status should be 'Resolved (closed)', 'Pending ... (active)', or 'Escalated to ... (active)'.
    """
    ticket_id = f"TK-{1052 + len(TICKETS)}" # Just a mock increment
    new_ticket = {
        "id": ticket_id,
        "employee": employee,
        "email": email,
        "issue_summary": issue_summary,
        "status": status
    }
    # In a real app we would append to TICKETS
    return f"Successfully created ticket: {json.dumps(new_ticket)}"

@tool
def escalate(reason: str) -> str:
    """Use this tool to explicitly escalate a risky or unclear request to a human/security."""
    return f"Issue escalated. Reason: {reason}"

tools = [search_kb, search_tickets, create_ticket, escalate]

# Prompt
system_prompt = """You are an internal IT Service Agent for Veridian Corp.
Your job is to:
1. Understand the employee's issue.
2. Find the relevant policy from the Knowledge Base (search_kb tool).
3. Check past ticket precedents if necessary (search_tickets tool).
4. Ask sensible follow-up questions if you need more information to resolve the request or create a ticket.
5. Resolve simple requests (e.g. password resets, standard approvals).
6. Escalate risky or unclear requests (e.g. non-catalog software, security/phishing) using the escalate tool.
7. Always create a structured ticket using the create_ticket tool before you finish the interaction.
8. ALWAYS show the KB source (e.g., KB-01) you used to determine your answer in your final response to the user.
9. Do not invent policies or information that isn't grounded in the KB.

You are currently talking to an employee.
"""

from langgraph.prebuilt import create_react_agent

def get_agent_executor():
    # Detect which API key is available
    llm = None
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        model_name = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0)
    elif os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.environ.get("LLM_MODEL_NAME", "gemini-1.5-pro") # Default to pro which is less likely to 404
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
    else:
        # Fallback to dummy or raise error
        raise ValueError("No API Key found. Please set OPENAI_API_KEY or GOOGLE_API_KEY in the environment.")

    # Using LangGraph's create_react_agent
    agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
    return agent_executor
