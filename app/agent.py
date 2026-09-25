import json
from typing import Any, Dict, List
from pydantic import ValidationError

from .prompt import prompt


class Agent:
    def __init__(self, client: Any, model: str, tool_registry: Dict[str, Any]):
        self.client = client
        self.model = model
        self.tool_registry = tool_registry
        self.tools = self._build_tools()

        self.messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": prompt
            }
        ]

    # =====================================
    # Build tools for LLM
    # =====================================

    def _build_tools(self) -> List[Dict[str, Any]]:
        tools = []

        for name, tool in self.tool_registry.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["schema"].model_json_schema(),
                },
            })

        return tools

    # =====================================
    # Execute one tool
    # =====================================

    def execute_tool(self, tool_call: Any) -> Any:

        function_name = tool_call.function.name

        # Get tool from registry
        tool = self.tool_registry.get(function_name)

        if tool is None:
            return {
                "error": f"Tool '{function_name}' does not exist."
            }

        function = tool["function"]
        schema = tool["schema"]

        # Parse arguments
        try:
            arguments = json.loads(
                tool_call.function.arguments
            )
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON arguments."
            }

        print(f"\nFunction selected: {function_name}")
        print(f"Arguments: {arguments}")

        # Validate arguments using Pydantic
        try:
            validated_arguments = schema(**arguments)

        except ValidationError as e:
            return {
                "error": "Invalid tool arguments.",
                "details": e.errors(),
            }

        print(
            f"Validated arguments: {validated_arguments}"
        )

        # Execute target function
        try:
            result = function(
                **validated_arguments.model_dump()
            )

        except Exception as e:
            print(f"\nTOOL ERROR: {type(e).__name__}: {e}")
            return {
                "error": "Tool execution failed.",
                "details": str(e),
            }

        print(f"Function Result: {result}")

        return result

    # =====================================
    # Run Agent
    # =====================================

    def run(self, user_input: str) -> str:

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        max_iterations = 3
        seen_tool_calls = set()

        # Agent Execution Loop
        for iteration in range(max_iterations):

            print(
                f"\n--- Agent iteration {iteration + 1} ---"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools,
            )

            message = response.choices[0].message

            print(f"\nMODEL USED: {response.model}")
            print(f"RAW MODEL MESSAGE: {message}")
            print(f"CONTENT: {message.content}")
            print(f"TOOL CALLS: {message.tool_calls}")

            # =====================================
            # Case 1: Final Text Response
            # =====================================

            if not message.tool_calls:

                if message.content is None:
                    return "The model returned an empty response."

                self.messages.append({
                    "role": "assistant",
                    "content": message.content
                })

                return message.content

            # =====================================
            # Case 2: Tool Calls Requested
            # =====================================

            tool_calls = []

            for tool_call in message.tool_calls:

                tool_call_data = {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }

                # =====================================
                # IMPORTANT FOR GEMINI 3
                # Preserve thought_signature
                # =====================================

                if getattr(tool_call, "extra_content", None):

                    tool_call_data["extra_content"] = (
                        tool_call.extra_content
                    )

                tool_calls.append(tool_call_data)

            self.messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls,
            })

            # =====================================
            # Execute each called tool
            # =====================================

            for tool_call in message.tool_calls:

                call_key = (
                    tool_call.function.name,
                    tool_call.function.arguments,
                )

                # Skip duplicate calls in same run
                if call_key in seen_tool_calls:

                    print(
                        f"\nDuplicate tool call skipped: "
                        f"{tool_call.function.name}"
                    )

                    continue

                seen_tool_calls.add(call_key)

                # Execute tool
                result = self.execute_tool(tool_call)

                # Save result back to conversation
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False
                    ),
                })

        return (
            "The agent reached the maximum number of iterations "
            "without producing a final answer."
        )