# Pharmacy Assistant Multi-Agent Chatbot

A state-driven multi-agent system built with **LangGraph**, designed to handle complex, stateful, and multi-turn pharmacy consultations through agent collaboration.

## 🌟 Key Features

* **Multi-Agent Orchestration**: Utilizes LangGraph to manage seamless transitions between specialized agents (e.g., Pharmacologist, Prescription Checker, and Customer Support).
* **State Management**: Maintains conversation context across multiple turns, ensuring coherent and medically relevant interactions.
* **Tool Integration**: Equipped with custom tools for real-time drug information retrieval and pharmacy business logic simulation.
* **Modular Architecture**:
* `agents/`: Definitions of agent personas and logic.
* `core/`: LangGraph workflow and state schema definitions.
* `tools/`: Functional tools for agents to interact with external data.
* `data/`: Local drug databases or configuration files.



## 📁 Project Structure

```text
.
├── agents/             # Agent prompts and logic implementations
├── core/               # LangGraph workflow and state definitions
├── tools/              # Pharmacy-specific tool functions
├── data/               # Reference datasets and business data
├── agent_server.py     # Backend server for model orchestration
└── client.py           # Client script for simulating user interactions

```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/cagito-ymzhu42/Pharmacy-Assistant-Multi-Agent-Chatbot.git
cd Pharmacy-Assistant-Multi-Agent-Chatbot

```

### 2. Prerequisites

Ensure you have Python 3.9+ installed, then install the dependencies:

```bash
pip install -r requirements.txt

```

### 3. Environment Configuration

Create a `.env` file in the root directory and add your API key:

```env
OPENAI_API_KEY=your_api_key_here

```

### 4. Run the Application

Start the Agent Server:

```bash
python agent_server.py

```

In a separate terminal, run the client to test the chatbot:

```bash
python client.py

```

## 🛠️ Tech Stack

* **Framework**: [LangGraph](https://github.com/langchain-ai/langgraph) / [LangChain](https://github.com/langchain-ai/langchain)
* **Language**: Python
* **LLM**: Optimized for OpenAI GPT series (compatible with other LangChain-supported models)
