"""
    Contributed by Devin Haggitt
    Created March 15, 2026

    Function: This script will conduct an AI
    code review for each pull request ran on the system

    Used https://github.com/UCCS-SP25-CS4300-CS5300-1/Group-8-spring-2025/blob/main/ai-code-review.py
    as a resource for constructing
"""

import openai
from openai import OpenAI
import os

""" Read the diff """
with open("diff.txt", "r") as file:
    diff = file.read()

""" Query ChatGPT """
client = OpenAI