from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter


load_dotenv()


rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.05
)

model = init_chat_model(
    "gpt-4.1",
    temperature=0
)
