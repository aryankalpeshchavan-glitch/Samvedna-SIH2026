import os
import json
import faiss

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INDEX_FILE = os.path.join(
    BASE_DIR,
    "rag",
    "index",
    "landslide_events.index"
)

METADATA_FILE = os.path.join(
    BASE_DIR,
    "rag",
    "index",
    "metadata.json"
)


# ============================================================
# LOAD
# ============================================================

print("Loading RAG index...")

index = faiss.read_index(INDEX_FILE)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

print("RAG loaded successfully.")


# ============================================================
# QUERY
# ============================================================

query = input("\nEnter your question: ").strip()

query_embedding = model.encode(
    [query],
    convert_to_numpy=True
).astype("float32")

faiss.normalize_L2(query_embedding)


# ============================================================
# SEARCH
# ============================================================

scores, indices = index.search(
    query_embedding,
    min(3, index.ntotal)
)


# ============================================================
# RESULTS
# ============================================================

print("\n========== RAG RESULTS ==========")

for rank, (score, idx) in enumerate(
    zip(scores[0], indices[0]),
    start=1
):

    result = metadata[idx]

    print(f"\nResult {rank}")
    print("Similarity:", round(float(score), 4))
    print("Event ID:", result["event_id"])
    print("State:", result["state"])
    print("District:", result["district"])
    print("Location:", result["location"])
    print("Trigger:", result["trigger"])
    print("Impact:", result["damage_or_impact"])
    print("Source:", result["source"])

print("\n=================================")