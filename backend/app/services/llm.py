from langchain_groq import ChatGroq
from app.config import settings


class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model=settings.LLM_MODEL,
            temperature=0.2,
        )

    def get_llm(self):
        return self.llm