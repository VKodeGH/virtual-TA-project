import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# File paths
ROOT = Path(__file__).resolve().parent.parent
COURSE_FILE = ROOT / "data" / "course-content" / "course_content.json"
DISCOURSE_FILE = ROOT / "data" / "discourse-posts" / "discourse_posts.json"
EMBED_DIR = ROOT / "data" / "embeddings"
EMBED_DIR.mkdir(parents=True, exist_ok=True)
EMBED_FILE = EMBED_DIR / "context_embeddings.npz"

# Chunking parameters
CHUNK_SIZE = 500  # words (approximate)
CHUNK_OVERLAP = 100  # words

# Load data
with open(COURSE_FILE, "r", encoding="utf-8") as f:
    course_data = json.load(f)
with open(DISCOURSE_FILE, "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Combine and tag sources
all_docs = []
for item in course_data:
    all_docs.append({
        "text": item["content"],
        "source": "course",
        "url": item["github_url"]
    })
for item in discourse_data:
    all_docs.append({
        "text": item["content"],
        "source": "discourse",
        "url": item["url"]
    })

# Chunking function
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks

# Prepare chunks and metadata
all_chunks = []
all_metadata = []

for doc in tqdm(all_docs, desc="Chunking documents"):
    chunks = chunk_text(doc["text"])
    for chunk in chunks:
        all_chunks.append(chunk)
        all_metadata.append({
            "source": doc["source"],
            "url": doc["url"]
        })

print(f"Total chunks: {len(all_chunks)}")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings
embeddings = model.encode(all_chunks, show_progress_bar=True, convert_to_numpy=True)

# Save embeddings and metadata
np.savez_compressed(
    EMBED_FILE,
    embeddings=embeddings,
    chunks=np.array(all_chunks),
    metadata=np.array(all_metadata, dtype=object)
)

print(f"✅ Embeddings saved to {EMBED_FILE}")
