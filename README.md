# 🍽️ Restaurant AI Agent

A practical AI agent built to understand **LLM Function Calling / Tool Calling** by implementing the agent loop manually.

The agent can search for real restaurant information using **OpenStreetMap Nominatim** and a public **Overpass API** instance, validate tool arguments with **Pydantic**, execute the selected Python function, return the tool result to the LLM, and continue the conversation until a final answer is produced.

The project uses **Gemini through its OpenAI-compatible API** while keeping the Agent loop implemented manually in Python.

---

## 🚀 Project Overview

The main goal of this project was to understand what happens **under the hood when an LLM uses tools**.

Instead of relying on a complete agent framework to hide the process, the project manually implements:

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
* Gemini `thought_signature` preservation
* City coordinate caching

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
2. Restricts geocoding results to Egypt.
3. Uses the coordinates in an Overpass query.
4. Searches for restaurants within a 10 km radius.
5. Returns available restaurant information.

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

For example, Gemini can generate:

```json
{
  "city": "Cairo",
  "cuisine": "italian"
}
```

The external OpenStreetMap data is then queried using that value.

---

## 🏠 Restaurant Details

The agent can retrieve details about a specific restaurant.

Example:

```text
Tell me more about Maison Thomas in Cairo.
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

The address can include:

```text
street
housenumber
postcode
city
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

The Agent receives this information and executes the corresponding Python function.

---

# 🧰 Tool Registry

The project uses a tool registry to keep each tool's information together.

Conceptually:

```python
tool_registry = {
    "search_restaurants": {
        "function": search_restaurants,
        "description": "Search for restaurants in a specific city.",
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

The registry is then converted into the format expected by the LLM.

---

# 🧱 Building Tools for the LLM

The Agent builds the tool definitions during initialization:

```python
self.tools = self._build_tools()
```

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

This allows the LLM to understand what each tool does and which parameters it expects.

---

# ✅ Pydantic Validation

Tool arguments returned by the LLM are first parsed from JSON:

```python
arguments = json.loads(
    tool_call.function.arguments
)
```

Then they are validated using the corresponding Pydantic schema:

```python
validated_arguments = schema(**arguments)
```

Only validated arguments are passed to the actual Python function.

The function is executed using:

```python
result = function(
    **validated_arguments.model_dump()
)
```

This provides a validation layer between the LLM and the actual Python code.

If validation fails, the tool is not executed and an error is returned.

---

# 🔄 Agent Loop

The Agent manually implements the LLM → Tool → LLM cycle.

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

The current Agent uses:

```python
max_iterations = 3
```

This limits the number of LLM cycles and prevents an endless tool-calling loop.

For example, a multi-step request can work like:

```text
User
 ↓
LLM
 ↓
search_restaurants_by_cuisine
 ↓
Restaurant Results
 ↓
LLM
 ↓
get_restaurant_details
 ↓
Restaurant Details
 ↓
LLM
 ↓
Final Answer
```

---

# 🧠 Gemini Tool Calling and `thought_signature`

The project uses Gemini through Google's OpenAI-compatible endpoint.

Gemini can return an additional tool-call field containing a:

```text
thought_signature
```

When the Agent continues the conversation after a tool call, this information must be preserved.

The Agent therefore keeps the returned `extra_content` when rebuilding the assistant tool-call message:

```python
if getattr(tool_call, "extra_content", None):
    tool_call_data["extra_content"] = tool_call.extra_content
```

This allows the Agent to preserve information such as:

```python
{
    "google": {
        "thought_signature": "..."
    }
}
```

Without preserving this information, Gemini can reject the next tool-calling request.

This was especially important when implementing the manual multi-step Agent loop with Gemini.

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

Example:

```python
call_key = (
    tool_call.function.name,
    tool_call.function.arguments,
)
```

If the same tool call is requested again during the same `run()` execution, it can be skipped.

This is a simple mechanism to reduce unnecessary repeated tool execution.

---

# 🧠 Conversation History

The Agent stores conversation messages in:

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

A typical tool interaction looks like:

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

The history allows the LLM to use the previous tool result when generating the next step.

This is especially important for multi-step requests.

---

# ⚡ City Coordinate Caching

The project uses a simple in-memory cache:

```python
city_cache = {}
```

When a city is requested for the first time, Nominatim is called and the coordinates are stored.

For later requests for the same city, the cached coordinates are returned.

Conceptually:

```text
First request

Cairo
 ↓
Nominatim
 ↓
Latitude + Longitude
 ↓
Cache


Next request

Cairo
 ↓
Cache
 ↓
Latitude + Longitude
```

This avoids repeatedly geocoding the same city.

The cache is stored in memory, so it is cleared whenever the application restarts.

---

# 🌍 Real-World Data Sources

The project does not use a private restaurant database.

Restaurant information is retrieved from **OpenStreetMap services**.

## Nominatim

Nominatim is used for geocoding:

```text
City Name
   ↓
Latitude + Longitude
```

Endpoint:

```text
https://nominatim.openstreetmap.org/search
```

The project restricts geocoding to Egypt using:

```python
"countrycodes": "eg"
```

This helps prevent ambiguous city names such as `Alexandria` from resolving to an unintended location outside Egypt.

The request also uses:

```python
"addressdetails": 1
```

so the application can verify the returned country.

The project sends an application-specific User-Agent:

```python
HEADERS = {
    "User-Agent": "RestaurantAIAgent/1.0"
}
```

---

## Overpass API

Overpass is used to query OpenStreetMap data for restaurants.

Current public endpoint:

```text
https://overpass.private.coffee/api/interpreter
```

The project uses Overpass queries such as:

```text
[out:json][timeout:50];
```

The HTTP request uses:

```python
timeout=60
```

This gives the external query up to 50 seconds while allowing a small additional window for the HTTP request.

The current configuration is:

```text
Nominatim HTTP timeout: 10 seconds

Overpass query timeout: 50 seconds

Overpass HTTP timeout: 60 seconds
```

The project uses a public Overpass service for learning and demonstration purposes. Before using public OpenStreetMap services at larger scale, review the current usage policies, service limits, and availability.

---

# 🏗️ Architecture

```text
                         User
                           │
                           ▼
                  Restaurant AI Agent
                           │
                           ▼
                          LLM
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
           Tool Call             Final Answer
                │
                ▼
          Tool Registry
                │
       ┌────────┼───────────────┐
       │        │               │
       ▼        ▼               ▼
    search   search by      restaurant
 restaurants  cuisine          details
       │        │               │
       └────────┼───────────────┘
                │
                ▼
         External Services
                │
         ┌──────┴──────┐
         ▼             ▼
     Nominatim       Overpass
         │             │
         └──────┬──────┘
                ▼
       Real OpenStreetMap Data
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
│   ├── prompt.py
│   └── ...
│
├── streamlit_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/MohamedFolyNabyh/restaurant-ai-agent.git
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
streamlit
```

The exact versions are defined in:

```text
requirements.txt
```

---

# 🔑 Environment Variables

The project uses Gemini through the OpenAI-compatible API.

Create a `.env` file:

```env
GEMINI_API_KEY=your-gemini-api-key
```

The application creates the client using:

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
```

The current model is configured as:

```python
model = "gemini-3.5-flash-lite"
```

Do not commit your `.env` file or API keys to GitHub.

Add:

```text
.env
```

to `.gitignore`.

---

# ▶️ Running the Application

The current project includes a Streamlit interface.

Run:

```bash
streamlit run streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

The interface allows you to interact with the Restaurant AI Agent directly.

---

# 💬 Example Conversations

## Restaurant Search

```text
User:

عايز مطاعم ايطالية في القاهرة
```

Possible tool:

```text
search_restaurants_by_cuisine
```

Expected flow:

```text
User
 ↓
Gemini
 ↓
search_restaurants_by_cuisine
 ↓
Overpass
 ↓
Restaurant Results
 ↓
Gemini
 ↓
Final Answer
```

---

## Restaurant Details

```text
User:

Maison Thomas عنوان ده فين
```

Possible tool:

```text
get_restaurant_details
```

Expected flow:

```text
User
 ↓
Gemini
 ↓
get_restaurant_details
 ↓
Overpass
 ↓
Restaurant Details
 ↓
Gemini
 ↓
Final Answer
```

---

## Multi-Step Example

```text
User:

دورلي على مطاعم ايطالي في القاهرة وبعدها هات تفاصيل أول مطعم
```

The Agent can perform:

```text
Iteration 1
    ↓
search_restaurants_by_cuisine
    ↓
Restaurant Results
    ↓
Iteration 2
    ↓
get_restaurant_details
    ↓
Restaurant Details
    ↓
Iteration 3
    ↓
Final Answer
```

This demonstrates that the LLM can use the result of one tool call to decide the next action.

---

# 🧩 Important Concepts Learned

This project was mainly built to understand these concepts practically.

## Tool Calling

The LLM decides whether a tool should be used and generates the required arguments.

## Tool Schema

The schema tells the LLM:

```text
What the tool does
+
What parameters it expects
```

## Tool Registry

The registry keeps:

```text
Function
Description
Schema
```

together in one place.

## Pydantic Validation

The LLM output is treated as untrusted input and validated before the actual Python function runs.

## Agent Loop

The Agent manually manages:

```text
LLM
 ↓
Tool
 ↓
Tool Result
 ↓
LLM
```

until a final answer is produced or the maximum iteration count is reached.

## Conversation State

The Agent stores all relevant messages in:

```python
self.messages
```

so the LLM can use previous results.

## External API Integration

The tools connect the LLM to real-world data through:

```text
Nominatim
OpenStreetMap
Overpass API
```

## Caching

City coordinates are cached in memory to avoid repeated geocoding requests.

## Error Handling

Tool execution errors are caught and returned to the LLM rather than crashing the entire Agent loop.

---

# 🆚 Why Build the Agent Loop Manually?

Frameworks such as LangGraph can manage agent state, routing, tool execution, and graph workflows.

This project intentionally implements the basic mechanism manually to make the underlying process easier to understand.

The goal is not to replace frameworks.

The goal is to understand what happens underneath them.

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
Duplicate call prevention
Gemini thought signatures
```

Once this mechanism is understood, frameworks such as LangGraph become easier to understand because the developer can see what abstraction they are providing.

---

# 🚧 Future Improvements

Possible improvements include:

* Streaming LLM responses
* Persistent conversation history
* Better restaurant ranking
* Distance-based search
* Opening-hours support
* Additional restaurant data sources
* More advanced caching
* More robust external API fallback handling
* LangGraph version of the same Agent
* FastAPI API layer
* Additional Streamlit features

---

# 📌 Project Status

Current implementation includes:

* ✅ Manual Agent Loop
* ✅ Gemini LLM
* ✅ OpenAI-compatible Gemini client
* ✅ Function Calling
* ✅ Tool Registry
* ✅ Dynamic Tool Schemas
* ✅ JSON Argument Parsing
* ✅ Pydantic Validation
* ✅ Real Restaurant Search
* ✅ Cuisine-based Search
* ✅ Restaurant Details
* ✅ Nominatim Geocoding
* ✅ Egypt Country Restriction
* ✅ Overpass Queries
* ✅ City Coordinate Caching
* ✅ Conversation History
* ✅ Duplicate Tool-Call Prevention
* ✅ Maximum Iteration Control
* ✅ Gemini `thought_signature` Preservation
* ✅ Error Handling
* ✅ Streamlit Interface

---

# 🎥 Demo

The current Streamlit demo can be tested with examples such as:

```text
عايز مطاعم ايطالية في القاهرة
```

and:

```text
Maison Thomas عنوان ده فين
```

These demonstrate:

```text
LLM
 ↓
Tool Selection
 ↓
Function Calling
 ↓
Pydantic Validation
 ↓
External API
 ↓
Tool Result
 ↓
Final Answer
```

A multi-step query can also demonstrate:

```text
دورلي على مطاعم ايطالي في القاهرة وبعدها هات تفاصيل أول مطعم
```

which shows the Agent moving through multiple tool calls before producing the final answer.

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
Conversation History
      ↓
LLM
      ↓
Final Answer
```

The project demonstrates that an AI Agent is not just an LLM generating text.

The LLM can act as the **decision-maker**, while external Python tools perform the actual operations and provide real-world information.

The main purpose of building this project manually was to understand the mechanism behind **Function Calling and Tool-Using Agents** before relying on higher-level frameworks.
