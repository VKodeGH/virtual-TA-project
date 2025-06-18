import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
import re

class RAGSystem:
    def __init__(self):
        # Load embeddings and metadata
        self.data = np.load("data/embeddings/context_embeddings.npz", allow_pickle=True)
        self.embeddings = self.data["embeddings"]
        self.chunks = self.data["chunks"]
        self.metadata = self.data["metadata"]
        
        # Load embedding model (MUST match the one used for data)
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def get_relevant_chunks(self, query_embedding, top_k=5):
        # Compute similarity scores
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get top-k indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        # Collect results
        results = []
        for idx in top_indices:
            results.append({
                "text": self.chunks[idx],
                "url": self.metadata[idx]["url"],
                "score": similarities[idx]
            })
        return results
    def clean_html(self, html):
        """Convert HTML to clean plain text."""
        soup = BeautifulSoup(html, "html.parser")
        # Remove code blocks and images (already processed)
        for elem in soup.find_all(['pre', 'code', 'img']):
            elem.decompose()
        return soup.get_text(separator=" ", strip=True)

    def get_most_relevant_sentence(self, text, question_embedding):
        """Extract the sentence most relevant to the question."""
        # Split into sentences (simple regex-based approach)
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        
        if not sentences:
            return text[:200] + "..."  # Fallback
        
        # Embed all sentences
        sentence_embeddings = self.embedding_model.encode(sentences)
        
        # Find most similar sentence to the question
        similarities = cosine_similarity([question_embedding], sentence_embeddings)[0]
        best_idx = similarities.argmax()
        
        return sentences[best_idx].strip()