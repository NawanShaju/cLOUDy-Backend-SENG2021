from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from .mode_schema import OrderExtraction, parser
from .prompts import prompt
import os

load_dotenv()

api_token = os.getenv("HUGGINGFACE_API_TOKEN")
model = os.getenv("HUGGINGFACE_MODEL")

endpoint = HuggingFaceEndpoint(
    repo_id=model,
    huggingfacehub_api_token=api_token,
    temperature=0.01,
    max_new_tokens=800,
)

llm = ChatHuggingFace(llm=endpoint)

chain = prompt | llm | parser

def extract_order_data(text: str) -> dict:
    try:
        result = chain.invoke({
            "text": text
        })

        return result.model_dump()
    except Exception as e:
        print("Extraction error:", e)
        return OrderExtraction().model_dump()
    