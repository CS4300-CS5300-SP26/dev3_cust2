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


""" Code Fence constant """
FENCE = "```"


""" Read the diff """
with open("diff.txt", "r") as file:
    diff = file.read()


""" Query ChatGPT """
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


""" Initialize System and User request messages """
system_content = """
    You are an industry expert in Advanced Software Engineering teaching a 
    class to future software engineers in a University. You are preparing
    a code review for a select group of students on their Django project. 
    
    This project aims to implement a production-level website that provides
    Software-as-a-Service (SaaS), that could be used in commercial environments
    and provide an extensive example in each student's portfolio. 
    
    Provide concise, actionable feedback, as if you were the supervisor 
    of a team containing these students.
    """

user_content = f"""
    Provide concise, actionable feedback in Markdown format (do not create a file), with 
    specific attention to pre-established Django convention, security, and code efficency. 
    
    For each suggestion, provide the file name and line number best associated with that suggestion,
    so a student can immediately reference and apply the provided feedback.

    If possible, also provide a graded rubric on style, security, code efficiency, and
    architecture stability so the student can pinpoint areas of concern.

    Use the provided pull request diff: \n{diff}
    """



""" Attempt to query a response from ChatGPT """
try:
    openai_chat = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        model="gpt-5.1-codex-mini"
    )

    feedback_message = openai_chat.choices[0].message.user_content

except openai.RateLimitError:
    print("ChatGPT Quota Exceeded")
    feedback_message = """
        **ChatGPT Quota Exceeded**
        No OpenAI Code Review available at this time
        """


""" Remove any leading file details if present using list slicing """
if feedback_message.startswith("```markdown"):
    feedback_message = feedback_message[len("```markdown"):]
elif feedback_message.startswith(FENCE):
    feedback_message = feedback_message[len(FENCE):]


""" Remove trailing code fence if present """
feedback_message = feedback_message.rstrip() # Removes trailing whitespace
if feedback_message.endswith(FENCE):
    feedback_message = feedback_message[:len(feedback_message) - len(FENCE)]


""" Writes feedback to markdown file """
code_review = f"""
    ## OpenAI Code Review
    {feedback_message}
    """
with open("feedback.md", "w") as file:
    file.write(code_review)