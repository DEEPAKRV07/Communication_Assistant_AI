from pathlib import Path
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SimpleRAG:
    def __init__(self, kb_dir: str):
        self.kb_dir = Path(kb_dir)
        self.docs = []
        self.doc_names = []
        for p in self.kb_dir.glob("*.md"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            self.docs.append(text)
            self.doc_names.append(p.name)
        if self.docs:
            self.vec = TfidfVectorizer(stop_words="english")
            self.mat = self.vec.fit_transform(self.docs)
        else:
            self.vec = None
            self.mat = None

    def top_k(self, query: str, k: int = 3) -> List[Tuple[str, str, float]]:
        if not self.docs or not self.vec:
            return []
        q_vec = self.vec.transform([query or ""])
        sims = cosine_similarity(q_vec, self.mat)[0]
        order = sims.argsort()[::-1][:k]
        out = []
        for idx in order:
            out.append((self.doc_names[idx], self.docs[idx], float(sims[idx])))
        return out
