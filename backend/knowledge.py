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
                
                # Check if already indexed and up-to-date
                file_mtime = os.path.getmtime(file_path)
                
                # Check for exact match or parts (chunked files)
                existing_parts = [d for d in self.docs if d.get('id') == doc_id or d.get('id', '').startswith(doc_id + "_part")]
                
                if existing_parts:
                    # Check mtime of the first found part
                    last_mtime = existing_parts[0].get('mtime', 0)
                    if file_mtime <= last_mtime:
                        continue # Skip if up-to-date
                    print(f"[KB] Datei aktualisiert: {filename} (Re-Indiziere...)")
                    
                    # Remove old parts before re-indexing to avoid duplicates
                    self.docs = [d for d in self.docs if d.get('id') != doc_id and not d.get('id', '').startswith(doc_id + "_part")]
                
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

                    if not text.strip():
                        print(f"[KB] WARNUNG: Kein Text aus '{filename}' extrahiert. (Eventuell gescanntes PDF oder leer?)")
                    
                    else:
                        # Chunking for large files (Optimized for Embeddings)
                        # 1500 chars is approx 300-400 tokens, safe for most models (2048/8192 limit)
                        CHUNK_SIZE = 1500
                        
                        if len(text) > CHUNK_SIZE:
                            chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
                            for i, chunk in enumerate(chunks):
                                chunk_id = f"{doc_id}_part{i+1}"
                                print(f"[KB] Indiziere Part {i+1}/{len(chunks)} von {filename}...")
                                self.upsert(chunk, doc_id=chunk_id, mtime=file_mtime)
                        else:
                            print(f"[KB] Indiziere: {filename} ({len(text)} Zeichen)...")
                            self.upsert(text, doc_id=doc_id, mtime=file_mtime)
                            
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

    def upsert(self, text: str, doc_id: Optional[str] = None, mtime: float = 0):
        emb = self._embed(text)
        if emb is None:
            return {"status": "failed", "reason": "embedding_error"}
        
        if doc_id is None:
            doc_id = f"doc_{len(self.docs)+1}"
            
        # Check replace
        replaced = False
        new_entry = {"id": doc_id, "text": text, "emb": emb, "mtime": mtime}
        
        for i, d in enumerate(self.docs):
            if d["id"] == doc_id:
                self.docs[i] = new_entry
                replaced = True
                break
        
        if not replaced:
            self.docs.append(new_entry)
            
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