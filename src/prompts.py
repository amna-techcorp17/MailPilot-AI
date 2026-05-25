from langchain_core.prompts import PromptTemplate


EMAIL_CATEGORIES = [
    "Support Request",
    "Complaint",
    "Meeting Request",
    "Sales Inquiry",
    "Follow-up",
    "Casual",
]

URGENCY_LEVELS = ["Urgent", "Medium", "Low Priority"]

TONES = ["Professional", "Friendly", "Formal", "Casual", "Corporate"]


CLASSIFICATION_PROMPT = PromptTemplate.from_template(
    """
Analyze the email and classify it into one of the following categories:

- Support Request
- Complaint
- Meeting Request
- Sales Inquiry
- Follow-up
- Casual

Email:
{email}

Return only the category.
"""
)


URGENCY_PROMPT = PromptTemplate.from_template(
    """
Analyze the email and classify its urgency as one of:

- Urgent
- Medium
- Low Priority

Consider deadlines, escalation language, business impact, and urgency keywords.

Email:
{email}

Return only the urgency label.
"""
)


SUMMARY_PROMPT = PromptTemplate.from_template(
    """
Summarize the following email professionally.

Requirements:
- concise
- include key points
- identify sender intent

Email:
{email}
"""
)


REPLY_PROMPT = PromptTemplate.from_template(
    """
You are a professional executive assistant.

Generate a professional email reply.

Requirements:
- contextual
- polite
- clear
- use the selected tone
- avoid inventing facts that are not present in the email

Tone:
{tone}

Tone guidance:
{tone_guidance}

Original Email:
{email}

Summary:
{summary}
"""
)


FOLLOWUP_PROMPT = PromptTemplate.from_template(
    """
Suggest a practical follow-up plan for the email below.

Requirements:
- include when to follow up
- include what the follow-up should say or request
- keep it concise

Email:
{email}

Summary:
{summary}
"""
)


TASK_PROMPT = PromptTemplate.from_template(
    """
Extract action items and deadlines from the email.

Email:
{email}

Return bullet points only. If there are no clear action items, return:
- No clear action items found.
"""
)
