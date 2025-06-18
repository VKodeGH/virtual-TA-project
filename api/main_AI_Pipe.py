from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from api.rag_logic import RAGSystem
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from python_scripts.utils.image_description import describe_image_from_base64
import os
from dotenv import load_dotenv

# --- AI Pipe (OpenAI-compatible) imports ---
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://aipipe.org/openai/v1")  # Default to AI Pipe endpoint

# Configure OpenAI client for AI Pipe
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL
)

app = FastAPI()

# Allow CORS for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load RAG system
rag = RAGSystem()

class QuestionRequest(BaseModel):
    question: str
    image: str = ""  # Base64 string, default to empty string
    mime_type: str = ""  # e.g. "image/png", default to empty string

@app.post("/api/")
async def answer_question(request: QuestionRequest):
    try:
        # 1. Process image if present
        full_question = request.question
        if request.image and request.mime_type:
            image_desc = describe_image_from_base64(request.image, request.mime_type)
            full_question += f"\nImage context: {image_desc}"

        # 2. Embed the question
        question_embedding = rag.embedding_model.encode([full_question])[0]

        # 3. Retrieve relevant chunks
        relevant_chunks = rag.get_relevant_chunks(question_embedding, top_k=3)

        # 4. Prepare context for LLM
        context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
        prompt = f"""Answer the student's question using the context below.

Question: {full_question}

Context:
{context}

Answer (in plain text, no code block, no backticks):"""

        # 5. Generate answer using AI Pipe (OpenAI-compatible)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4o-mini" or any other supported model
            messages=[
                {"role": "system", "content": "You are a helpful teaching assistant. Answer clearly and concisely."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip()

        # 6. Collect reference links
        links = []
        for chunk in relevant_chunks:
            # Clean HTML and get plain text
            clean_text = rag.clean_html(chunk["text"])
            # Extract most relevant sentence to the question
            relevant_sentence = rag.get_most_relevant_sentence(
                clean_text,
                question_embedding
            )
            links.append({
                "url": chunk["url"],
                "text": relevant_sentence[:250] + ("..." if len(relevant_sentence) > 250 else "")
            })

        return {
            "answer": answer,
            "links": links
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
