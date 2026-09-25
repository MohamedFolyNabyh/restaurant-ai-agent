import os

from dotenv import load_dotenv
from openai import OpenAI

from app.agent import Agent

from app.tools import (
    search_restaurants,
    get_restaurant_details,
    search_restaurants_by_cuisine
)

from app.schemas import (
    SearchRestaurantsInput,
    GetRestaurantDetailsInput,
    SearchRestaurantsByCuisineInput
)


# =====================================
# Load environment variables
# =====================================

load_dotenv()


# =====================================
# Tool Registry
# =====================================

tool_registry = {

    "search_restaurants": {
        "function": search_restaurants,
        "schema": SearchRestaurantsInput,
        "description": "Search for restaurants in a specific city."
    },

    "get_restaurant_details": {
        "function": get_restaurant_details,
        "schema": GetRestaurantDetailsInput,
        "description": "Get details about a specific restaurant."
    },

    "search_restaurants_by_cuisine": {
        "function": search_restaurants_by_cuisine,
        "schema": SearchRestaurantsByCuisineInput,
        "description": "Search for restaurants in a city by cuisine type."
    }

}


# =====================================
# OpenRouter Client
# =====================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)


# =====================================
# Create Agent
# =====================================

agent = Agent(
    client=client,
    model="openrouter/free",
    tool_registry=tool_registry
)


# =====================================
# User Input
# =====================================



while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    answer = agent.run(user_input)

    print("\nAgent:")
    print(answer)