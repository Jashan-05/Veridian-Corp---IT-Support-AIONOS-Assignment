# Veridian Corp - Internal Service Agent (IT Support)

This repository contains the prototype for **Assignment 2: Internal Service Agent**, designed to convert employee IT requests into actionable resolutions and structured tickets.

## 🚀 Features

*   **Interactive Chat Interface:** Built with Streamlit for a responsive, modern user experience.
*   **Agentic Tool Use:** Powered by LangGraph, the agent intelligently decides when to:
    *   Search the IT Knowledge Base (`search_kb`).
    *   Look up historical tickets for precedent (`search_tickets`).
    *   Escalate risky/unclear requests to Security/Human agents (`escalate`).
    *   Generate a structured ticket upon resolution (`create_ticket`).
*   **Audit Trail:** A dedicated sidebar automatically expands to show the exact tools invoked, their inputs, and the data retrieved, ensuring full transparency.
*   **Test Scenarios Integration:** The 15 provided employee requests are pre-loaded and selectable via a dropdown for rapid testing.

## 🏗️ Architecture & Process Flow

```mermaid
flowchart TD
    %% Entities
    U([Employee]) -->|Natural Language Request| UI[Streamlit UI]
    UI -->|Forwards Request| A{LangGraph ReAct Agent\n(Gemini 3.6 Flash)}
    
    %% Agent actions
    A -->|1. Missing Context?| T1[search_kb Tool]
    T1 -.->|Returns Policies| A
    
    A -->|2. Needs Precedent?| T2[search_tickets Tool]
    T2 -.->|Returns Past Tickets| A
    
    %% Decision Node
    A -->|3. Evaluate Rules| D{Decision Engine}
    
    %% Branches
    D -->|Violation / Risk| E[escalate Tool]
    D -->|Standard Issue| R[Resolve internally]
    D -->|Missing Data| Q[Ask Employee]
    
    %% Finalization
    E --> TC[create_ticket Tool]
    R --> TC
    
    TC -.->|Returns Ticket ID| A
    A -->|Final Response + Source citation| UI
    UI --> U
    
    %% Database layer
    subgraph Mock Database (data.py)
        T1 --> KB[(IT Knowledge Base)]
        T2 --> TK[(Ticket History)]
        TC --> TK
    end
```

## 📋 Inputs, Sources, and Assumptions

*   **Inputs:** Simulated employee requests (REQ-01 to REQ-15) as specified in the assignment pack.
*   **Sources:** The exact Knowledge Base (KB-01 to KB-10) and Asset Management Policy provided in the Assignment 2 Data Pack. No external policies were invented.
*   **Assumptions:** 
    *   A conversational interface is preferred for initial triage over static IT forms.
    *   Ticket IDs can be auto-incremented safely in this prototype.
    *   The backend operates statelessly per conversation thread but uses a moving conversation history for multi-turn follow-ups.

## 🛠️ AI Tools Used

1.  **LangChain / LangGraph:** Used as the core orchestration framework to handle the ReAct agent loop, tool binding, and system prompting.
2.  **Streamlit:** Used to rapidly deploy the frontend "clickable prototype" and visualize the internal Agent steps via an Audit Trail.
3.  **Google Gemini (gemini-3.6-flash):** The foundational LLM powering the reasoning, intent classification, and tool-invocation logic, selected for cost-efficiency and low latency.

## 💻 Run it locally

1.  Clone this repository:
    ```bash
    git clone https://github.com/yourusername/veridian-it-agent.git
    cd veridian-it-agent
    ```
2.  Install dependencies:
    ```bash
    pip install streamlit langchain langgraph langchain-openai langchain-google-genai python-dotenv
    ```
3.  Set up your environment variables:
    *   Create a `.env.local` file in the root directory.
    *   Add your API key: `GEMINI_API_KEY="your-api-key-here"`
4.  Run the application:
    ```bash
    streamlit run app.py
    ```
5.  Open `http://localhost:8501` in your browser, select a scenario, and hit **Load Scenario**!
