import json

from pydantic import ValidationError


class Agent:

    def __init__(
        self,
        client,
        model,
        tool_registry
    ):

        self.client = client
        self.model = model
        self.tool_registry = tool_registry

        self.tools = self._build_tools()

        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a restaurant assistant. "
                    "Use the available tools to find real restaurant information. "
                    "When the user asks about a specific restaurant, "
                    "use get_restaurant_details. "
                    "When the user asks to find restaurants in a city, "
                    "use search_restaurants. "
                    "When the user asks for restaurants by cuisine, "
                    "use search_restaurants_by_cuisine. "
                    "Use information from previous conversation turns when relevant."
                )
            }
        ]

    # =====================================
    # Build tools for LLM
    # =====================================

    def _build_tools(self):

        tools = []

        for name, tool in self.tool_registry.items():

            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["schema"].model_json_schema()
                }
            })

        return tools

    # =====================================
    # Execute one tool
    # =====================================

    def execute_tool(self, tool_call):

        function_name = tool_call.function.name

        # =====================================
        # Get tool
        # =====================================

        tool = self.tool_registry.get(function_name)

        if tool is None:

            return {
                "error": f"Tool '{function_name}' does not exist."
            }

        function = tool["function"]
        schema = tool["schema"]

        # =====================================
        # Parse arguments
        # =====================================

        try:

            arguments = json.loads(
                tool_call.function.arguments
            )

        except json.JSONDecodeError:

            return {
                "error": "Invalid JSON arguments."
            }

        print("\nFunction selected:")
        print(function_name)

        print("\nArguments:")
        print(arguments)

        # =====================================
        # Validate arguments
        # =====================================

        try:

            validated_arguments = schema(**arguments)

        except ValidationError as e:

            return {
                "error": "Invalid tool arguments.",
                "details": e.errors()
            }

        print("\nValidated arguments:")
        print(validated_arguments)

        # =====================================
        # Execute function
        # =====================================

        try:

            result = function(
                **validated_arguments.model_dump()
            )

        except Exception as e:

            return {
                "error": "Tool execution failed.",
                "details": str(e)
            }

        print("\nFunction Result:")
        print(result)

        return result

    # =====================================
    # Run Agent
    # =====================================

    def run(self, user_input):

        self.messages.append({
            "role": "user",
            "content": user_input
        })

        # Maximum number of LLM -> Tool -> Result cycles
        max_iterations = 5

        # Prevent duplicate tool calls
        seen_tool_calls = set()

        # =====================================
        # Agent Loop
        # =====================================

        for iteration in range(max_iterations):

            print(
                f"\n--- Agent iteration {iteration + 1} ---"
            )

            # =====================================
            # Ask LLM
            # =====================================

            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=self.tools
            )

            # =====================================
            # Get assistant message
            # =====================================

            message = response.choices[0].message

            # =====================================
            # No tools
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
            # Add assistant message
            # =====================================

            self.messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                    for tool_call in message.tool_calls
                ]
            })

            # =====================================
            # Execute tools
            # =====================================

            for tool_call in message.tool_calls:

                # Create unique key for this tool call
                call_key = (
                    tool_call.function.name,
                    tool_call.function.arguments
                )

                # =====================================
                # Skip duplicate tool call
                # =====================================

                if call_key in seen_tool_calls:

                    print("\nDuplicate tool call skipped:")
                    print(tool_call.function.name)

                    continue

                seen_tool_calls.add(call_key)

                # =====================================
                # Execute tool
                # =====================================

                result = self.execute_tool(tool_call)

                # =====================================
                # Add tool result
                # =====================================

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        # =====================================
        # Maximum iterations reached
        # =====================================

        return (
            "The agent reached the maximum number "
            "of iterations without producing a final answer."
        )