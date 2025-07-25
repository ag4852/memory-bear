"""
Centralized configuration for Memory Bear MCP Server.
Contains user-configurable settings that can be set via environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Directory settings
NOTES_DIR = os.getenv("NOTES_DIR")
TEST_NOTES_DIR = os.getenv("TEST_NOTES_DIR")

# API credentials 
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Tool configuration 
CONTENT_TAGS = os.getenv("CONTENT_TAGS", "lecture,homework,exam,concepts,research").split(",")
CLASS_TAGS = os.getenv("CLASS_TAGS", "").split(",") if os.getenv("CLASS_TAGS") else []

# Application behavior settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TEST_MODE = os.getenv("TEST_MODE", "False").lower() == "true"
