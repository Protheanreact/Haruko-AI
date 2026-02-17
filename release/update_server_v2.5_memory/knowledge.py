import os
import pickle
import numpy as np
from typing import List, Optional
import ollama
from pypdf import PdfReader

class KnowledgeBase:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb")
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_path = os.path.join(self.base_dir, "kb_index.pkl")
        self.docs = []
        # Use a good default embedding model
        self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self._load()
        # Auto-scan knowledge folder on init
        self.scan_directory()

    def scan_directory(self, directory="knowledge"):
        """Scans the directory for PDF, TXT, MD and Code files."""
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except: pass
            return

        print(f"[KB] Scanne '{directory}' nach Dokumenten...")
        
        # Supported extensions for code/technical docs
        code_exts = {'.py', '.js', '.ts', '.html', '.css', '.json', '.sh', '.bat', '.cpp', '.c', '.h', '.java', '.go', '.rs'}
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                doc_id = f"doc_{filename}"
                
                # Check if already indexed (by ID)
                # Optimization: Check modification time if possible, but for now ID check is fast
                if any(d.get('id') == doc_id for d in self.docs):
                    continue 
                
                text = ""
                ext = os.path.splitext(filename)[1].lower()
                
                try:
                    if ext == ".pdf":
                        print(f"[KB] Lese PDF: {filename}...")
                        reader = PdfReader(file_path)
                        for page in reader.pages:
                            extract = page.extract_text()
                            if extract: text += extract + "\n"
                    
                    elif ext == ".txt" or ext == ".md":
                        print(f"[KB] Lese Text/MD: {filename}...")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            
                    elif ext in code_exts:
                        print(f"[KB] Lese Code ({ext}): {filename}...")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Wrap code in markdown block for better LLM context
                            text = f"File: {filename}\n```{ext[1:]}\n{content}\n```"

                    if text.strip():
                        # Chunking for large files (Basic)
                        # If text is too long (> 4000 chars), split it
                        if len(text) > 4000:
                            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                            for i, chunk in enumerate(chunks):
                                chunk_id = f"{doc_id}_part{i+1}"
                                print(f"[KB] Indiziere Part {i+1} von {filename}...")
                                self.upsert(chunk, doc_id=chunk_id)
                        else:
                            print(f"[KB] Indiziere: {filename} ({len(text)} Zeichen)...")
                            self.upsert(text, doc_id=doc_id)
                            
                except Exception as e:
                    print(f"[KB] Fehler beim Lesen von {filename}: {e}")

    def _load(self):
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, "rb") as f:
                    self.docs = pickle.load(f)
        except Exception as e:
            print(f"[KB] Lade-Fehler: {e}")
            self.docs = []

    def _save(self):
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump(self.docs, f)
        except Exception as e:
            print(f"[KB] Speicher-Fehler: {e}")

    def _embed(self, text: str):
        try:
            # Use Ollama for local embeddings (free & private)
            res = ollama.embeddings(model=self.embed_model, prompt=text)
            vec = np.array(res["embedding"], dtype=np.float32)
            norm = np.linalg.norm(vec) + 1e-10
            return vec / norm
        except Exception as e:
            # Fallback or error log
            print(f"[KB] Embedding-Fehler (Modell '{self.embed_model}' vorhanden?): {e}")
            return None

    def upsert(self, text: str, doc_id: Optional[str] = None):
        emb = self._embed(text)
        if emb is None:
            return {"status": "failed", "reason": "embedding_error"}
        
        if doc_id is None:
            doc_id = f"doc_{len(self.docs)+1}"
            
        # Check replace
        replaced = False
        for i, d in enumerate(self.docs):
            if d["id"] == doc_id:
                self.docs[i] = {"id": doc_id, "text": text, "emb": emb}
                replaced = True
                break
        
        if not replaced:
            self.docs.append({"id": doc_id, "text": text, "emb": emb})
            
        self._save()
        return {"status": "ok", "id": doc_id, "replaced": replaced}

    def clear(self):
        self.docs = []
        self._save()
        return {"status": "ok"}

    def search(self, query: str, top_k: int = 3):
        if not self.docs:
            return []
        
        q = self._embed(query)
        if q is None:
            return []
            
        sims = []
        for d in self.docs:
            sims.append((d, float(np.dot(q, d["emb"]))))
            
        # Sort by similarity desc
        sims.sort(key=lambda x: x[1], reverse=True)
        
        # Return top K docs
        return [item[0] for item in sims[:top_k]]
