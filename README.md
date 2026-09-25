# 🍽️ Restaurant AI Agent

A practical AI agent built to understand **LLM Function Calling / Tool Calling** by implementing the agent loop manually.

The agent can search for real restaurant information using **OpenStreetMap Nominatim** and **Overpass API**, validate tool arguments with **Pydantic**, execute the selected Python function, return the tool result to the LLM, and continue the conversation until a final answer is produced.

---

## 🚀 Project Overview

The main goal of this project was to understand what happens **under the hood when an LLM uses tools**.

Instead of using a complete agent framework to hide the process, the project manually implements:

* Tool registry
* Tool schemas
* LLM tool calling
* JSON argument parsing
* Pydantic validation
* Tool execution
* Tool result messages
* Conversation history
* Agent loop
* Duplicate tool-call prevention
* Maximum iteration control

The core flow is:

```text
User
  ↓
LLM
  ↓
Tool Call
  ↓
Parse JSON Arguments
  ↓
Pydantic Validation
  ↓
Execute Python Function
  ↓
Tool Result
  ↓
LLM
  ↓
Final Answer
```

---

# ✨ Main Features

## 🔎 Restaurant Search

The agent can search for restaurants in a city.

Example:

```text
Find restaurants in Cairo.
```

The agent can call:

```text
search_restaurants
```

The tool:

1. Converts the city name into coordinates using Nominatim.
2. Uses the coordinates in an Overpass query.
3. Searches for restaurants within a defined radius.
4. Returns restaurant information.

Returned information can include:

```text
name
cuisine
phone
website
```

---

## 🍝 Search by Cuisine

The agent can search for restaurants matching a cuisine.

Example:

```text
Find Italian restaurants in Cairo.
```

The agent can call:

```text
search_restaurants_by_cuisine
```

The tool filters restaurants using the OpenStreetMap `cuisine` tag.

---

## 🏠 Restaurant Details

The agent can retrieve details about a specific restaurant.

Example:

```text
Tell me more about Pizza House in Cairo.
```

The agent can call:

```text
get_restaurant_details
```

The result can contain:

```text
name
cuisine
phone
website
address
```

---

# 🤖 Function Calling

The LLM receives a list of available tools.

For example:

```python
{
    "type": "function",
    "function": {
        "name": "search_restaurants",
        "description": "...",
        "parameters": {...}
    }
}
```

The model does not directly execute the Python function.

Instead, it returns a tool call containing:

```text
function name
+
arguments
```

For example:

```json
{
    "name": "search_restaurants",
    "arguments": {
        "city": "Cairo"
    }
}
```

The Agent then handles the execution.

---

# 🧰 Tool Registry

The project uses a tool registry to keep each tool's information together.

Conceptually:

```python
tool_registry = {
    "search_restaurants": {
        "function": search_restaurants,
        "description": "Search restaurants",
        "schema": SearchRestaurantsInput
    }
}
```

Each registered tool contains:

```text
Function
Description
Pydantic Schema
```

This registry is then converted into the format expected by the LLM.

---

# 🧱 Building Tools for the LLM

The Agent uses:

```python
self.tools = self._build_tools()
```

during initialization.

The `_build_tools()` method converts the internal tool registry into LLM-compatible tool definitions.

For every tool it sends:

```text
name
description
JSON Schema
```

The schema is generated using:

```python
tool["schema"].model_json_schema()
```

This allows the LLM to understand which parameters each tool expects.

---

# ✅ Pydantic Validation

When the LLM returns tool arguments, they are first parsed from JSON.

Example:

```python
arguments = json.loads(
    tool_call.function.arguments
)
```

Then the arguments are validated using the corresponding Pydantic schema:

```python
validated_arguments = schema(**arguments)
```

This provides a validation layer between the LLM and the actual Python function.

If validation fails, the tool is not executed and an error is returned.

---

# 🔄 Agent Loop

The agent manually implements the LLM → Tool → LLM cycle.

Simplified:

```text
             ┌──────────────┐
             │     User     │
             └──────┬───────┘
                    ↓
             ┌──────────────┐
             │     LLM      │
             └──────┬───────┘
                    │
             Does it need a tool?
                /          \
              No            Yes
              ↓              ↓
       Final Answer      Tool Call
                              ↓
                       Execute Tool
                              ↓
                         Tool Result
                              ↓
                             LLM
                              ↓
                       Final Answer
```

The project limits the number of cycles using:

```python
max_iterations = 5
```

This prevents an endless agent loop.

---

# 🛡️ Duplicate Tool-Call Prevention

The project also keeps track of already executed tool calls:

```python
seen_tool_calls = set()
```

A unique key is created from:

```text
tool name
+
tool arguments
```

If the same call is requested again, it can be skipped.

This is a simple mechanism to prevent unnecessary repeated tool execution.

---

# 🧠 Conversation History

The Agent stores messages in:

```python
self.messages
```

The history contains:

```text
system messages
user messages
assistant messages
tool messages
```

For example:

```text
System
  ↓
User
  ↓
Assistant → Tool Call
  ↓
Tool → Result
  ↓
Assistant → Final Answer
```

This allows the LLM to use information from previous turns when generating the next response.

---

# 🌍 Real-World Data Sources

The project uses OpenStreetMap services for restaurant data.

## Nominatim

Nominatim is used for geocoding:

```text
City name
   ↓
Latitude + Longitude
```

Endpoint:

```text
https://nominatim.openstreetmap.org/search
```

## Overpass API

Overpass is used to query OpenStreetMap data for restaurants.

Endpoint:

```text
https://overpass-api.de/api/interpreter
```

The project sends an application-specific User-Agent:

```python
HEADERS = {
    "User-Agent": "RestaurantAIAgent/1.0"
}
```

This identifies the application when making requests to the public service.

Before deploying beyond a small demo, review the current usage policies and rate limits for the public OpenStreetMap services.

---

# 🏗️ Architecture

```text
                    User
                      │
                      ▼
                Restaurant Agent
                      │
                      ▼
                     LLM
                      │
              ┌───────┴────────┐
              │                │
              ▼                ▼
        Tool Call         Final Answer
              │
              ▼
       Tool Registry
              │
      ┌───────┼──────────────┐
      │       │              │
      ▼       ▼              ▼
 search    search by      restaurant
restaurants cuisine         details
      │       │              │
      └───────┼──────────────┘
              │
              ▼
       External APIs
              │
       ┌──────┴──────┐
       ▼             ▼
   Nominatim      Overpass
       │             │
       └──────┬──────┘
              ▼
        Real Restaurant Data
              │
              ▼
             LLM
              │
              ▼
         Final Answer
```

---

# 📁 Project Structure

```text
restaurant-ai-agent/
│
├── app/
│   ├── agent.py
│   ├── tools.py
│   ├── schemas.py
│   └── ...
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY>
```

Move into the project directory:

```bash
cd restaurant-ai-agent
```

---

## 2. Create a Virtual Environment

Using Conda:

```bash
conda create -n restaurant-agent python=3.11
```

Activate it:

```bash
conda activate restaurant-agent
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Typical dependencies include:

```text
openai
pydantic
requests
python-dotenv
```

The exact versions are defined in:

```text
requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file for the LLM provider configuration.

Example:

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=your-compatible-base-url
```

Do not commit secrets to GitHub.

Add:

```text
.env
```

to `.gitignore`.

---

# ▶️ Running the Agent

Run the main application file used by the repository.

For example:

```bash
python main.py
```

Then interact with the agent from the terminal.

Example:

```text
User: Find restaurants in Cairo
```

The Agent may:

```text
1. Ask the LLM what to do
2. Receive a tool call
3. Parse the tool arguments
4. Validate the arguments
5. Execute the tool
6. Send the tool result back to the LLM
7. Generate the final answer
```

---

# 💬 Example Conversations

## Restaurant Search

```text
User:
Find restaurants in Cairo.
```

Possible tool:

```text
search_restaurants
```

---

## Cuisine Search

```text
User:
Find Italian restaurants in Cairo.
```

Possible tool:

```text
search_restaurants_by_cuisine
```

---

## Restaurant Details

```text
User:
Tell me more about Pizza House in Cairo.
```

Possible tool:

```text
get_restaurant_details
```

---

# 🧩 Important Concepts Learned

This project was mainly built to understand these concepts practically.

### Tool Calling

The LLM decides whether a tool should be used and generates the required arguments.

### Tool Schema

The schema tells the LLM:

```text
What the tool does
+
What parameters it expects
```

### Pydantic Validation

The LLM output is treated as untrusted input and validated before the Python function runs.

### Agent Loop

The Agent can repeatedly move through:

```text
LLM → Tool → Result → LLM
```

until it reaches a final response.

### Conversation State

The Agent keeps previous messages so the LLM can use earlier context.

---

# 🆚 Why Build the Agent Loop Manually?

Frameworks such as LangGraph can manage agent state, routing, tool execution, and graph workflows.

This project intentionally implements the basic mechanism manually to make the underlying process easier to understand.

The goal was not to replace frameworks, but to understand what happens underneath them.

In this project, the Agent itself manages:

```text
LLM requests
Tool calls
Argument parsing
Validation
Function execution
Tool results
Conversation history
Iteration limits
```

---

# 🚧 Future Improvements

Possible improvements include:

* Streaming LLM responses
* Persistent conversation history
* Better restaurant ranking
* Distance-based search
* Opening-hours support
* Additional restaurant data sources
* Caching geocoding results
* More robust error handling
* LangGraph version of the same agent
* FastAPI API layer
* Streamlit interface

---

# 📌 Project Status

Current implementation includes:

* ✅ Manual Agent Loop
* ✅ OpenAI-compatible LLM client
* ✅ Function Calling
* ✅ Tool Registry
* ✅ Dynamic Tool Schemas
* ✅ JSON Argument Parsing
* ✅ Pydantic Validation
* ✅ Real Restaurant Search
* ✅ Cuisine-based Search
* ✅ Restaurant Details
* ✅ Nominatim Geocoding
* ✅ Overpass Queries
* ✅ Conversation History
* ✅ Duplicate Tool-Call Prevention
* ✅ Maximum Iteration Control

---

# 👨‍💻 Author

**Mohamed Foly**

AI / ML Engineer

GitHub:

https://github.com/MohamedFolyNabyh

---

# ⭐ Main Learning Goal

The main objective of this project was to understand the complete lifecycle of an LLM tool call:

```text
User Request
    ↓
LLM Decision
    ↓
Tool Call
    ↓
JSON Parsing
    ↓
Pydantic Validation
    ↓
Python Function
    ↓
External API
    ↓
Tool Result
    ↓
LLM
    ↓
Final Answer
```

The project demonstrates that an AI Agent is not just an LLM generating text. The LLM can act as the decision-maker while external tools perform the actual operations and provide real-world information.
