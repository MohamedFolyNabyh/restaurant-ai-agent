import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from app.agent import Agent

from app.tools import (
    search_restaurants,
    search_restaurants_by_cuisine,
    get_restaurant_details
)

from app.schemas import (
    SearchRestaurantsInput,
    SearchRestaurantsByCuisineInput,
    GetRestaurantDetailsInput
)


# =====================================
# Load environment variables
# =====================================

load_dotenv()


# =====================================
# Page configuration
# =====================================

st.set_page_config(
    page_title="Restaurant AI Agent",
    page_icon="🍽️",
    layout="centered"
)


# =====================================
# Tool Registry
# =====================================

tool_registry = {

    "search_restaurants": {
        "function": search_restaurants,
        "schema": SearchRestaurantsInput,
        "description": (
            "Search for real restaurants in a specific city."
        )
    },

    "search_restaurants_by_cuisine": {
        "function": search_restaurants_by_cuisine,
        "schema": SearchRestaurantsByCuisineInput,
        "description": (
            "Search for real restaurants in a city "
            "by cuisine type."
        )
    },

    "get_restaurant_details": {
        "function": get_restaurant_details,
        "schema": GetRestaurantDetailsInput,
        "description": (
            "Get detailed information about a specific restaurant "
            "in a city."
        )
    }
}


# =====================================
# OpenRouter Client
# =====================================

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


# =====================================
# Create Agent
# =====================================

if "agent" not in st.session_state:

    st.session_state.agent = Agent(
        client=client,
        model="gemini-3.5-flash-lite",
        tool_registry=tool_registry
    )


# =====================================
# Chat History
# =====================================

if "messages" not in st.session_state:

    st.session_state.messages = []


# =====================================
# Page Title
# =====================================

st.title("🍽️ Restaurant AI Agent")

st.write(
    "Ask me to find restaurants or get restaurant details."
)


# =====================================
# Display previous messages
# =====================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# =====================================
# User Input
# =====================================

prompt = st.chat_input(
    "Ask me about restaurants..."
)


# =====================================
# Process User Message
# =====================================

if prompt:

    # ---------------------------------
    # Display user message
    # ---------------------------------

    st.chat_message("user").write(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })


    # ---------------------------------
    # Run Agent
    # ---------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            answer = st.session_state.agent.run(prompt)

        st.write(answer)


    # ---------------------------------
    # Save assistant response
    # ---------------------------------

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })