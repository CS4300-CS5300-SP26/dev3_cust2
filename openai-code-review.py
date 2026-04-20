"""
    Contributed by Devin Haggitt
    Modified March 16, 2026

    Function: This script will conduct an AI
    code review for each pull request ran on the system.

    *** Currently limited to pull requests with diff files
    under 15000 characters. Need to expand the functionality
    for bigger pull requests to break up the diff file ***

    Used https://github.com/UCCS-SP25-CS4300-CS5300-1/
        Group-8-spring-2025/blob/main/ai-code-review.py
    as a resource for constructing
"""

import openai
from openai import OpenAI
import os
import shutil


""" Constants declared for efficiency """
FENCE = "```"
MAX_DIFF = 150000


""" Secret strings variable for diff scrubbing """
secret_strings = ["KEY =", "KEY=", "TOKEN =", "TOKEN="]


""" Function to remove potential secrets from diff """
def scrub_diff(diff_file):
    temp_file = diff_file + '.temp'
    with open(diff_file, 'r') as infile, open(temp_file, 'w') as outfile:
        for line in infile:
            if not any(s in line for s in secret_strings):
                outfile.write(line)

    # Replace the original diff with scrubbed diff
    shutil.move(temp_file, diff_file)


""" Read the diff """
if not os.path.exists("diff.txt"):
    raise RuntimeError('Failed to find diff file')
scrub_diff("diff.txt")
with open("diff.txt", "r") as file:
    diff = file.read()
# if len(diff) > MAX_DIFF:
#     raise ValueError(f"""Length of diff exceeds max size of
#       {MAX_DIFF} characters""")
#     print("Recommendation to break the diff into reviewable commits")
#     diff = diff[:MAX_DIFF]


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
    and apply the provided feedback. Also, provide details on the severity
    of the concern, so the student can understand areas of high risk.

    If possible, also provide an evaluation matrix on style, security, code
    efficiency, architectural stability, and Software Engineering standards so
    the student can pinpoint exact areas of concern. Don't provide a 
    grade/score, but provide a rating with categories like "Needs Fix, Minor,
    Moderate, and Good".

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
    feedback_message = openai_chat.output_text
    response_id = openai_chat.id
    print(f"Response ID: {response_id}")

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
code_review = f"## OpenAI Code Review\n{feedback_message.strip()}\n"
with open("feedback.md", "w") as file:
    file.write(code_review)
