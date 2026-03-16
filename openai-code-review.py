"""
    Contributed by Devin Haggitt
    Modified March 16, 2026

    Function: This script will conduct an AI
    code review for each pull request ran on the system

    Used https://github.com/UCCS-SP25-CS4300-CS5300-1/
        Group-8-spring-2025/blob/main/ai-code-review.py
    as a resource for constructing
"""

import openai
from openai import OpenAI
import os
import requests


""" Constants declared for efficiency """
FENCE = "```"
MAX_DIFF = 15000


""" Read the diff """
if not os.path.exists("diff.txt"):
    raise RuntimeError('Failed to find diff file')
with open("diff.txt", "r") as file:
    diff = file.read()[:MAX_DIFF]


""" Assign the OpenAI API key to a variable """
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError(
        "No API key found. Set the OPENAI_API_KEY environment variable.")


""" Query ChatGPT for a client """
client = OpenAI(api_key=openai_key)


""" Initialize the Instruction and Input request messages """
instructions_content = """
    You are an industry expert in Advanced Software Engineering teaching a
    class to future software engineers in a University. You are preparing
    a code review for a select group of students on their Django project.

    This project aims to implement a production-level website that provides
    Software-as-a-Service (SaaS), that could be used in commercial environments
    and provide an extensive example in each student's portfolio.

    Provide concise, actionable feedback, as if you were the supervisor
    of a team containing these students.
    """

input_content = f"""
    Provide concise, actionable feedback in Markdown format
    (do not create a file), with specific attention to pre-established
    Django convention, security, and code efficency.

    For each suggestion, provide the file name and line number best
    associated with that suggestion, so a student can immediately reference
    and apply the provided feedback.

    If possible, also provide a graded rubric on style, security,
    code efficiency, and architecture stability so the student
    can pinpoint areas of concern.

    Use the provided pull request diff: \n{diff}
    """


""" Attempt to query a response from ChatGPT """
feedback_message = ""
try:
    openai_chat = client.responses.create(
        model="gpt-5.1-codex-mini",
        instructions=instructions_content,
        input=input_content
    )
    print(openai_chat.output_text)
    feedback_message = openai_chat.output_text

    
    """ Pulls the rate limits of the response using curl """
    url = f'https://api.openai.com/responses/{openai_chat.id}'
    auth = {"Authorization": f"Bearer {openai_key}"}
    response = requests.get(url, headers=auth)
    print("Response Rate Limits:")
    for header_name, header_value in response.headers.items():
        print(f"* {header_name}: {header_value}")

except openai.APITimeoutError as e:
    print(f"""OpenAI API request took too long to complete:
        {e}""")
    feedback_message = (
        f"""Open AI API request took too long to complete:
        {e}""")

except openai.AuthenticationError as e:
    print(f"""OpenAI API request failed to authenticate the API Key:
        {e}""")
    feedback_message = (
        f"""Open AI API request failed to authenticate the API Key:
        {e}""")

except openai.BadRequestError as e:
    print(f"""OpenAI API request was malformed or is missing parameters:
        {e}""")
    feedback_message = (
        f"""Open AI API request was malformed or is missing parameters:
        {e}""")

except openai.InternalServerError as e:
    print(f"""OpenAI API request reached an Internal Server Error:
        {e}""")
    feedback_message = (
        f"""Open AI API request reached an Internal Server Error:
        {e}""")

except openai.RateLimitError as e:
    print(f"""OpenAI API request has exceeded the Rate Limit:
        {e}""")
    feedback_message = (
        f"""Open AI API request has exceeded the Rate Limit:
        {e}""")


""" Remove any leading file details if present using list slicing """
if feedback_message.startswith("```markdown"):
    feedback_message = feedback_message[len("```markdown"):]
elif feedback_message.startswith(FENCE):
    feedback_message = feedback_message[len(FENCE):]


""" Remove trailing code fence if present """
feedback_message = feedback_message.rstrip()  # Removes trailing whitespace
if feedback_message.endswith(FENCE):
    feedback_message = feedback_message[:len(feedback_message) - len(FENCE)]


""" Writes feedback to markdown file """
code_review = f"""## OpenAI Code Review
    {feedback_message}
    """
with open("feedback.md", "w") as file:
    file.write(code_review)
