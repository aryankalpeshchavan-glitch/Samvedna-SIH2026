import os
import json
import pandas as pd
import numpy as np
import faiss

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_FILE = os.path.join(
    BASE_DIR,
    "data",
    "landslide_events.csv"
)

INDEX_DIR = os.path.join(
    BASE_DIR,
    "rag",
    "index"
)

INDEX_FILE = os.path.join(
    INDEX_DIR,
    "landslide_events.index"
)

METADATA_FILE = os.path.join(
    INDEX_DIR,
    "metadata.json"
)


# ============================================================
# CREATE INDEX DIRECTORY
# ============================================================

os.makedirs(INDEX_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("Loading historical landslide data...")

df = pd.read_csv(CSV_FILE)

print("Rows:", len(df))
print("Columns:", list(df.columns))


# ============================================================
# CREATE TEXT DOCUMENTS
# ============================================================

print("\nCreating RAG documents...")

documents = []

for _, row in df.iterrows():

    text = f"""
Historical Landslide Event

Event ID: {row.get('event_id', '')}
Date: {row.get('date', '')}
State: {row.get('state', '')}
District: {row.get('district', '')}
Location: {row.get('area_or_location', '')}
Landslide Type: {row.get('landslide_type', '')}
Trigger: {row.get('trigger', '')}
Damage or Impact: {row.get('damage_or_impact', '')}
Source: {row.get('source', '')}
""".strip()

    documents.append(text)


print("Documents created:", len(documents))


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("\nLoading embedding model...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding model loaded.")


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

print("\nCreating embeddings...")

embeddings = model.encode(
    documents,
    show_progress_bar=True,
    convert_to_numpy=True
)

embeddings = embeddings.astype("float32")


# ============================================================
# NORMALIZE EMBEDDINGS
# ============================================================

faiss.normalize_L2(embeddings)


# ============================================================
# CREATE FAISS INDEX
# ============================================================

print("\nCreating FAISS index...")

dimension = embeddings.shape[1]

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)


# ============================================================
# SAVE INDEX
# ============================================================

faiss.write_index(index, INDEX_FILE)


# ============================================================
# SAVE METADATA
# ============================================================

metadata = []

for i, (_, row) in enumerate(df.iterrows()):

    metadata.append({
        "index": i,
        "event_id": str(row.get("event_id", "")),
        "date": str(row.get("date", "")),
        "state": str(row.get("state", "")),
        "district": str(row.get("district", "")),
        "location": str(row.get("area_or_location", "")),
        "landslide_type": str(row.get("landslide_type", "")),
        "trigger": str(row.get("trigger", "")),
        "damage_or_impact": str(row.get("damage_or_impact", "")),
        "source": str(row.get("source", "")),
        "text": documents[i]
    })


with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)


# ============================================================
# COMPLETE
# ============================================================

print("\n==========================================")
print("DAY 4 - RAG INDEX COMPLETE")
print("==========================================")

print("Documents:", len(documents))
print("Embedding dimension:", dimension)
print("FAISS index:", INDEX_FILE)
print("Metadata:", METADATA_FILE)

print("==========================================")