import os
import json
import faiss
from sentence_transformers import SentenceTransformer


class LandslideRetriever:

    def __init__(self):

        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        index_file = os.path.join(
            base_dir,
            "rag",
            "index",
            "landslide_events.index"
        )

        metadata_file = os.path.join(
            base_dir,
            "rag",
            "index",
            "metadata.json"
        )

        print("Loading RAG index...")

        self.index = faiss.read_index(index_file)

        with open(metadata_file, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("RAG retriever loaded.")

    def search(self, query, top_k=3):

        embedding = self.model.encode(
            [query],
            convert_to_numpy=True
        ).astype("float32")

        faiss.normalize_L2(embedding)

        scores, indices = self.index.search(
            embedding,
            min(top_k, self.index.ntotal)
        )

        results = []

        for score, idx in zip(scores[0], indices[0]):

            result = self.metadata[int(idx)].copy()

            result["similarity"] = float(score)

            results.append(result)

        return results


if __name__ == "__main__":

    retriever = LandslideRetriever()

    query = input(
        "\nEnter your query: "
    ).strip()

    results = retriever.search(query)

    print("\n========== RETRIEVED EVIDENCE ==========")

    for i, result in enumerate(results, start=1):

        print(f"\nResult {i}")
        print("Similarity:", round(
            result["similarity"], 4
        ))
        print("Event:", result["event_id"])
        print("State:", result["state"])
        print("District:", result["district"])
        print("Location:", result["location"])
        print("Trigger:", result["trigger"])
        print("Impact:", result["damage_or_impact"])
        print("Source:", result["source"])

    print("\n========================================")