import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from dotenv import load_dotenv

class VirtualTA:
    def __init__(self):
        with open("../data/processed_data.pkl", "rb") as f:
            self.data = pickle.load(f)
        self.vectorizer = self.data["vectorizer"]
        self.tfidf_matrix = self.data["tfidf_matrix"]
        self.documents = self.data["documents"]
        load_dotenv()
        self.ai_pipe_key = os.getenv("AI_PIPE_KEY")
        self.ai_pipe_url = "https://aipipe.org/openrouter/v1/chat/completions"  # ← Correct URL
  # Use the real endpoint provided by your professor

    def find_relevant_docs(self, question, top_n=5):
        question_vec = self.vectorizer.transform([question])
        similarities = cosine_similarity(question_vec, self.tfidf_matrix)
        top_indices = np.argsort(similarities[0])[-top_n:][::-1]
        return [self.documents[i] for i in top_indices]

    def call_ai_pipe(self, question, context):
        headers = {
            "Authorization": f"Bearer {self.ai_pipe_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            f"You are a helpful teaching assistant for the TDS course. "
            f"Answer the following student question using the provided context from course content and Discourse posts. "
            f"If you cite any Discourse post, include the link.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}\n"
        )
        payload = {
            "model": "gpt-3.5-turbo",  # or whatever model your AI Pipe supports
            "messages": [
                {"role": "system", "content": "You are a helpful teaching assistant for the TDS course."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.2
        }
        response = requests.post(self.ai_pipe_url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return "Sorry, I couldn't generate an answer due to an API error."

    def generate_answer(self, question):
        relevant_docs = self.find_relevant_docs(question)
        # Combine the most relevant context
        context = "\n\n".join([doc["text"][:500] for doc in relevant_docs])
        answer = self.call_ai_pipe(question, context)
        links = [
            {"url": doc["metadata"], "text": doc["text"][:100]}
            for doc in relevant_docs if doc["source"] == "discourse"
        ]
        return {
            "answer": answer,
            "links": links[:3]
        }

# Test the logic
if __name__ == "__main__":
    ta = VirtualTA()
    question = "How do I calculate token costs for GPT-3.5-turbo?"
    response = ta.generate_answer(question)
    print(response)
