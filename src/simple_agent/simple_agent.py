from langchain.agents import create_agent
from src.configs import OpenAIConfigs


def send_email(to: str, subject: str, body: str):
    """Send an email"""
    email = {"to": to, "subject": subject, "body": body}
    # ... email sending logic
    print(f"OpenAIConfigs.OPENAI_API_KEY: {OpenAIConfigs.OPENAI_API_KEY}")

    return f"Email sent to {to}"


graph = create_agent(
    "gpt-4o",
    tools=[send_email],
    system_prompt="You are an email assistant. Always use the send_email tool.",
)
