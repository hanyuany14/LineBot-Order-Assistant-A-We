import os
from urllib.parse import quote as urlquote
from dotenv import load_dotenv

if not os.getenv("IS_HEROKU", False):
    load_dotenv("dotenv/.env.local")


class OpenAIConfigs:
    """The configuration for OpenAI.

    models list in openai: https://platform.openai.com/docs/models/overview
    """

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_GPT_4_TURBO_MODEL_NAME = "gpt-4-turbo"
    OPENAI_GPT_35_TURBO_MODEL_NAME = "gpt-3.5-turbo"
    OPENAI_GPT_4O_MODEL_NAME = "gpt-4o"

    OPENAI_GPT_5_1_MINI_MODEL_NAME = "gpt-5-mini"

    OPENAI_MAX_TOKENS = 5000
    OPENAI_TEMPERATURE = 0.1



class QDrantConfigs:
    """The configuration for QDrant."""

    preffix = "Formal"
    QDRANT_URL = os.environ.get("QDRANT_URL")
    QDRANT_FEW_SHOT_EXAMPLES_COLLECTION_NAME = f"{preffix}_few_shot_examples"
    QDRANT_NOUNS_MAP_COLLECTION_NANME = f"{preffix}_nouns_map"
    NOUNS_MAP_TOP_K = 10
    NOUNS_MAP_TOP_SCORE_THRESHOLD = 0.2
    FEW_SHOT_EXAMPLE_TOP_K = 10


class LanchainConfigs:
    """The configuration for SQL agent."""

    SQL_AGENT_MAX_ITERATION = 6
    SQL_AGENT_MAX_EXECUTION_TIME = 20.0  # we limit the agent only run for 20 seconds.
    SQL_AGENT_EARLY_STOPPING_METHOD = "force"  # if the agent is not able to generate a query, it will stop but will still return full msgs for user.
    SQL_AGENT_TYPE = "openai-tools"


class LangsmithConfigs:
    """The configuration for Langsmith.

    We can refer: https://docs.ragas.io/en/latest/howtos/integrations/langchain.html
    """

    LANGSMITH_API_KEY = os.environ.get("LANGCHAIN_API_KEY")
    LANGSMITH_EVALUATOR_DATASET_BASE_NAME = "Evaluating dataset"


class GroqConfigs:
    """The configuration for Groq.
    other models: https://console.groq.com/docs/models

    """

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    MODEL_NAME_MIXTRAL = "mixtral-8x7b-32768"
    MODEL_NAME_LLAMA_70B = "llama3-70b-8192"


class PostgreConfigs:
    """The configuration for Postgre."""

    # DB_INFO = {
    #     "HOST": os.environ.get("POSTGRES_HOST"),
    #     "PORT": os.environ.get("POSTGRES_PORT"),
    #     "NAME": os.environ.get("POSTGRES_DB"),
    #     "USER": os.environ.get("POSTGRES_USER"),
    #     "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
    # }
    # DB_ENGINE_CONNECT_STR = f"postgresql+psycopg2://{DB_INFO['USER']}:{urlquote(str(DB_INFO['PASSWORD']))}@{DB_INFO['HOST']}:{DB_INFO['PORT']}/{DB_INFO['NAME']}"

    # DB_URI = "postgresql://postgres.rctzefmdhuptrryaizqc:WXj6x39-ku8$y$y@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
    # DB_URI = "postgresql://postgres.rctzefmdhuptrryaizqc:WXj6x39-ku8$y$y@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"
    DB_ENGINE_CONNECT_STR = f"""postgresql://postgres:{os.environ.get("SUPABASE_DATABASE_PASSWORD")}@db.rctzefmdhuptrryaizqc.supabase.co:5432/postgres"""


class LineBotConfigs:
    """The configuration for Line bot."""

    line_channel_id = os.environ.get("LINE_CHANNEL_ID")
    line_channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
    line_channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    line_user_id = os.environ.get("LINE_USER_ID")
