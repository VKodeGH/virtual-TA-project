from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from api.rag_logic import RAGSystem
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from python_scripts.utils.image_description import describe_image_from_base64
import google.generativeai as genai
import base64
import os
from dotenv import load_dotenv

# Load environment variables and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-2.0-flash")  # Or "gemini-1.5-flash"

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
        # --- System prompt defining the TA's persona ---
        system_prompt = (
            "You are a Virtual Teaching Assistant (Virtual TA) for the Tools in Data Science (TDS) course at IITM. "
            "Your job is to help students with course content and forum discussions from Jan 1 to April 14, 2025. "
            "If you don't know something, say so honestly. Do not make up information."
        )
        contents = [system_prompt]

        # --- Check for common FAQ questions ---
        FAQ = {
            "who are you": "I am the Virtual TA for the Tools in Data Science (TDS) course at IITM. I help students with course-related questions using data from Jan 1 to April 14, 2025.",
            "what is tds": "TDS stands for Tools in Data Science, a course covering essential data science tools and concepts, it's one of the diploma level courses in the BS degree programme in Data Science and it's application at IIT Madras.",
            "what is your knowledge range": "I have knowledge of the TDS course and forum discussions from January 1 to April 14, 2025. I cannot answer questions outside this period."
        }
        user_question = request.question.lower().strip()
        for key in FAQ:
            if key in user_question:
                return {"answer": FAQ[key], "links": []}

        # --- Check for out-of-scope dates ---
        if any(year in user_question for year in ["2022", "2023", "2024", "2026"]):
            return {
                "answer": "I only have knowledge of the TDS course from Jan 1 to April 14, 2025. I cannot answer questions outside this period.",
                "links": []
            }

        # --- Handle image input ---
        if request.image and request.mime_type:
            try:
                image_bytes = base64.b64decode(request.image)
                contents.append({
                    "mime_type": request.mime_type,
                    "data": image_bytes
                })
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")
            # Use explicit prompt for image-only questions
            if not request.question.strip():
                question_text = (
                    "This image contains a question. Carefully read all visible text, "
                    "transcribe the question, and answer it in detail. If unclear, explain what you can see."
                )
            else:
                question_text = request.question
            contents.append(question_text)
            # For RAG retrieval
            image_desc = describe_image_from_base64(request.image, request.mime_type)
            full_question = image_desc if not request.question.strip() else request.question + f"\nImage context: {image_desc}"
        else:
            full_question = request.question
            contents.append(request.question)

        # --- RAG retrieval ---
        question_embedding = rag.embedding_model.encode([full_question])[0]
        relevant_chunks = rag.get_relevant_chunks(question_embedding, top_k=3)
        context = "\n\n".join([chunk["text"] for chunk in relevant_chunks])
        contents.append(
            f"""Use the following context to answer the question. If unsure, say so.

Context:
{context}

Answer (plain text, no markdown):"""
        )

        # --- Gemini answer generation ---
        response = gemini_model.generate_content(contents)
        answer = response.text.strip()

        # --- Reference links ---
        links = []
        for chunk in relevant_chunks:
            clean_text = rag.clean_html(chunk["text"])
            relevant_sentence = rag.get_most_relevant_sentence(clean_text, question_embedding)
            links.append({
                "url": chunk["url"],
                "text": relevant_sentence[:250] + ("..." if len(relevant_sentence) > 250 else "")
            })

        return {"answer": answer, "links": links}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
