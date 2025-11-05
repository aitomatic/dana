from rank_bm25 import BM25Okapi
import numpy as np


class BM25SearchEngine:
    def __init__(self, corpus: list[str]):
        self._original_corpus = corpus
        self.corpus = [self.text_to_words(text) for text in corpus]
        self.bm25 = BM25Okapi(self.corpus)

    @staticmethod
    def text_to_words(text: str) -> list[str]:
        return [word.lower() for word in text.split(" ")]

    def search(self, query: str, n: int = 1) -> list[str]:
        top_n = self.get_top_n_indices(query, n)
        return [self._original_corpus[i] for i in top_n]

    def get_top_n_indices(self, query: str, n: int = 1) -> list[int]:
        scores = self.bm25.get_scores(self.text_to_words(query))
        return np.argsort(scores)[::-1][:n].tolist()


if __name__ == "__main__":
    corpus = [
        "The quick brown fox jumps over the lazy dog",
        "The quick brown fox jumps over the lazy cat",
    ]
    search_engine = BM25SearchEngine(corpus)
    print(search_engine.get_top_n_indices("lazy cat"))
