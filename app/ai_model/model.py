from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from dotenv import load_dotenv
from .mode_schema import OrderExtraction, parser
from .prompts import prompt
import os

load_dotenv()

api_token = os.getenv("HUGGINGFACE_API_TOKEN")
model = os.getenv("HUGGINGFACE_MODEL")

_chain = None

def _get_chain():
    global _chain
    if _chain is None:
        endpoint = HuggingFaceEndpoint(
            repo_id=model,
            huggingfacehub_api_token=api_token,
            temperature=0.01,
            max_new_tokens=800,
        )

        llm = ChatHuggingFace(llm=endpoint)
        _chain = prompt | llm | parser
        
    return _chain


def extract_order_data(text: str) -> dict:
    try:
        result = _get_chain().invoke({
            "text": text
        })

        return result.model_dump()
    except Exception as e:
        print("Extraction error:", e)
        return OrderExtraction().model_dump()
    