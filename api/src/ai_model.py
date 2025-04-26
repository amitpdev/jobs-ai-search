from sentence_transformers import SentenceTransformer


model = SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> list[float]:
    embedding = model.encode(text)
    # convert numpy array to float array
    # TODO: should be an asyncpg proper syntax
    return embedding.astype(float).tolist()
