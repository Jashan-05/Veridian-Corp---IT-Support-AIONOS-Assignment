import streamlit as st
import os
from dotenv import load_dotenv
from data import REQUESTS
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env.local if present
load_dotenv(".env.local")

st.set_page_config(page_title="Veridian IT Support Agent", layout="wide")

# -- Configuration Sidebar --
with st.sidebar:
    st.title("⚙️ Configuration")
    api_provider = st.radio("LLM Provider", ["Google Gemini", "OpenAI"])
    
    if api_provider == "OpenAI":
        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4.5"])
    else:
        # 2026 Model endpoints
        model_name = st.selectbox("Model", ["gemini-3.6-flash", "gemini-3.6-pro", "gemini-1.5-pro", "gemini-1.5-flash"])
    
    os.environ["LLM_MODEL_NAME"] = model_name
    
    # Pre-fill from .env.local if available
    default_key = os.environ.get("GEMINI_API_KEY") if api_provider == "Google Gemini" else os.environ.get("OPENAI_API_KEY")
    api_key = st.text_input("API Key", type="password", value=default_key or "")
    
    if api_key:
        if api_provider == "OpenAI":
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ.pop("GOOGLE_API_KEY", None)
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GOOGLE_API_KEY"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ.pop("OPENAI_API_KEY", None)
            
    st.markdown("---")
    st.title("🕵️ Audit Trail")
    audit_container = st.container()

# -- Load Agent --
try:
    import agent
    import importlib
    importlib.reload(agent)
    agent_executor = agent.get_agent_executor()
    agent_ready = True
except ValueError as e:
    agent_ready = False
except Exception as e:
    agent_ready = False
    st.error(f"Error loading agent: {e}")

# -- Main UI --
st.title("Veridian Corp - IT Support")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []

# Scenario Selector
st.markdown("### Test Scenarios")
scenario_options = {req["id"]: f"{req['id']} ({req['employee']}): {req['request']}" for req in REQUESTS}
selected_scenario_id = st.selectbox("Select a scenario to simulate", options=[""] + list(scenario_options.keys()), format_func=lambda x: scenario_options.get(x, "Custom..."))

if st.button("Load Scenario"):
    if selected_scenario_id:
        req = next((r for r in REQUESTS if r["id"] == selected_scenario_id), None)
        if req:
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.session_state.audit_logs = []
            
            # Queue the conversation start
            intro = f"Hi, I'm {req['employee']} ({req['email']}). {req['request']}"
            st.session_state.trigger_prompt = intro
            st.rerun()

# Render Audit Trail in Sidebar
with audit_container:
    for log in st.session_state.audit_logs:
        with st.expander(f"Tool Call: {log['tool']}"):
            st.write("**Input:**", log['tool_input'])
            st.write("**Output:**", log['log'])

# Chat Display
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input & Execution
prompt = st.chat_input("Type your message here...")

if "trigger_prompt" in st.session_state:
    prompt = st.session_state.trigger_prompt
    del st.session_state.trigger_prompt

if not agent_ready:
    st.warning("Please configure an API Key in the sidebar to start.")
else:
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Only render the user message if it wasn't already rendered above
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = agent_executor.invoke(
                        {"messages": st.session_state.chat_history + [HumanMessage(content=prompt)]}
                    )
                    
                    messages = response["messages"]
                    output_message = messages[-1]
                    
                    # Handle raw string vs list of dicts (newer Gemini API formats)
                    raw_content = output_message.content
                    if isinstance(raw_content, list):
                        # Extract the 'text' fields from the blocks
                        output_text = "".join([block.get("text", "") for block in raw_content if isinstance(block, dict) and "text" in block])
                        if not output_text: # Fallback
                            output_text = str(raw_content)
                    else:
                        output_text = str(raw_content)
                    
                    # Extract tool calls for the audit trail
                    # We look at the messages added in this turn
                    for msg in messages:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                st.session_state.audit_logs.append({
                                    "tool": tool_call["name"],
                                    "tool_input": str(tool_call["args"]),
                                    "log": "See tool messages in graph..."
                                })
                        elif msg.__class__.__name__ == "ToolMessage":
                            # Attach the response to the last tool log
                            if st.session_state.audit_logs:
                                st.session_state.audit_logs[-1]["log"] = msg.content
                    
                    st.markdown(output_text)
                    st.session_state.messages.append({"role": "assistant", "content": output_text})
                    
                    # Update memory
                    st.session_state.chat_history.append(HumanMessage(content=prompt))
                    st.session_state.chat_history.append(AIMessage(content=output_text))
                    
                    st.rerun() # Refresh to show audit logs
                except Exception as e:
                    st.error(f"Agent Error: {e}")
