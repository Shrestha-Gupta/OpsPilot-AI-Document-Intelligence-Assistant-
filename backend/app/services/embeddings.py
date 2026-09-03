import hashlib
import math


class LightweightEmbeddings:
    """
    Lightweight local embeddings using feature hashing.
    Does not load PyTorch or sentence-transformers.
    Designed for low-memory deployment.
    """

    def __init__(self, dimension=256):
        self.dimension = dimension

    def _embed(self, text):
        vector = [0.0] * self.dimension

        words = text.lower().split()

        for word in words:
            index = int(
                hashlib.md5(word.encode("utf-8")).hexdigest(),
                16
            ) % self.dimension

            vector[index] += 1.0

        # Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vector))

        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)


class EmbeddingService:

    def __init__(self):
        self.embedding_model = LightweightEmbeddings()

    def get_model(self):
        return self.embedding_model
