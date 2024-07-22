
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_groq import ChatGroq
from openai import OpenAI
from langchain_community.utilities import SQLDatabase

from src.configs import OpenAIConfigs
from src.configs import GroqConfigs
from src.configs import PostgreConfigs


class LLMUtils:
    """The utility class for LLM."""

    OPENAI_CLIENT = OpenAI(api_key=OpenAIConfigs.OPENAI_API_KEY)
    GPT4_LLM_MODEL = ChatOpenAI(
        api_key=OpenAIConfigs.OPENAI_API_KEY,  # type: ignore
        model=OpenAIConfigs.OPENAI_GPT_4_TURBO_MODEL_NAME,
        temperature=OpenAIConfigs.OPENAI_TEMPERATURE,
        max_tokens=OpenAIConfigs.OPENAI_MAX_TOKENS,
    )

    GPT35_LLM_MODEL = ChatOpenAI(
        api_key=OpenAIConfigs.OPENAI_API_KEY,  # type: ignore
        model=OpenAIConfigs.OPENAI_GPT_35_TURBO_MODEL_NAME,
        temperature=OpenAIConfigs.OPENAI_TEMPERATURE,
        max_tokens=OpenAIConfigs.OPENAI_MAX_TOKENS,
    )

    GPT4O_LLM_MODEL = ChatOpenAI(
        api_key=OpenAIConfigs.OPENAI_API_KEY,  # type: ignore
        model=OpenAIConfigs.OPENAI_GPT_4O_MODEL_NAME,
        temperature=OpenAIConfigs.OPENAI_TEMPERATURE,
        max_tokens=OpenAIConfigs.OPENAI_MAX_TOKENS,
    )


class GroqUtils:
    """The utility class for Groq."""

    GROQ_CHAT_MISTAL_7B = ChatGroq(
        api_key=GroqConfigs.GROQ_API_KEY,  # type: ignore
        temperature=OpenAIConfigs.OPENAI_TEMPERATURE,
        model=GroqConfigs.MODEL_NAME_MIXTRAL,  # you can change another model you want.
    )

    GROQ_CHAT_LLAMA_70B = ChatGroq(
        api_key=GroqConfigs.GROQ_API_KEY,  # type: ignore
        temperature=OpenAIConfigs.OPENAI_TEMPERATURE,
        model=GroqConfigs.MODEL_NAME_LLAMA_70B,  # you can change another model you want.
    )


def select_llm_model(llm_model: str):
    match llm_model:
        case "gpt-4o":
            return LLMUtils.GPT4O_LLM_MODEL
        case "gpt-4-turbo":
            return LLMUtils.GPT4_LLM_MODEL
        case "gpt-3.5-turbo":
            return LLMUtils.GPT35_LLM_MODEL
        case "groq_mistal_7b":
            return GroqUtils.GROQ_CHAT_MISTAL_7B
        case "groq_llama_70b":
            return GroqUtils.GROQ_CHAT_LLAMA_70B
        case _:
            return LLMUtils.GPT35_LLM_MODEL


# class LangsmithUtils:
#     """The utility class for Langsmith."""

#     LANGSMITH_CLIENT = Client(api_key=LangsmithConfigs.LANGSMITH_API_KEY)


class EmbeddingUtils:
    """The utility class for Embedding."""

    OPENAI_EMBEDDING = OpenAIEmbeddings(api_key=OpenAIConfigs.OPENAI_API_KEY)  # type: ignore


class PostgreUtils:

    PG_DB = SQLDatabase.from_uri(
        database_uri=PostgreConfigs.DB_ENGINE_CONNECT_STR,
        # include_tables=["inventory", "orders", ],
    )
