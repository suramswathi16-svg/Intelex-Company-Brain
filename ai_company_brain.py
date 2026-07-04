"""
================================================================================
 AI COMPANY BRAIN — Enterprise Knowledge Platform
================================================================================
100% free / open-source, runs fully locally (CPU is fine).

Stack:
  - Embeddings ......... sentence-transformers (all-MiniLM-L6-v2)
  - Vector DB .......... FAISS (in-process, persisted to disk)
  - Knowledge Graph .... NetworkX (in-memory, persisted to disk)
                         (drop-in Neo4jGraph class included, toggle with env var)
  - LLM ................ HuggingFace transformers (google/flan-t5-base, local)
  - Org Memory DB ...... SQLite (swap connection string for PostgreSQL any time)
  - API ................ FastAPI + Uvicorn
  - Orchestration ...... hand-rolled multi-agent router (Retrieval / Synthesis /
                         Decision agents) — no paid frameworks required.

--------------------------------------------------------------------------------
SETUP
--------------------------------------------------------------------------------
    pip install -r requirements.txt
    python ai_company_brain.py
    # or:  uvicorn ai_company_brain:app --reload --port 8000

Open http://127.0.0.1:8000/docs for interactive Swagger UI.

First run will download the embedding model (~90MB) and the LLM (~250MB) from
HuggingFace Hub — after that everything works fully offline.

--------------------------------------------------------------------------------
QUICK TEST (curl)
--------------------------------------------------------------------------------
    curl -F "file=@handbook.pdf" http://127.0.0.1:8000/ingest/document

    curl -X POST http://127.0.0.1:8000/chat \
         -H "Content-Type: application/json" \
         -d '{"question": "What is our remote work policy?"}'

    curl -X POST http://127.0.0.1:8000/memory/add \
         -H "Content-Type: application/json" \
         -d '{"type":"sop","title":"Deployment SOP","content":"Always run tests before deploy.","tags":["devops"]}'

    curl -X POST http://127.0.0.1:8000/decision \
         -H "Content-Type: application/json" \
         -d @sample_decision_request.json
================================================================================
"""

import os
import re
import json
import uuid
import sqlite3
import datetime as dt
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import faiss
import networkx as nx
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from transformers import pipeline as hf_pipeline

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field
import uvicorn

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False


# ==============================================================================
# CONFIG
# ==============================================================================
class Config:
    DATA_DIR = Path(__file__).parent / "data"
    INDEX_PATH = DATA_DIR / "faiss.index"
    META_PATH = DATA_DIR / "meta.json"
    GRAPH_PATH = DATA_DIR / "graph.json"
    DB_PATH = DATA_DIR / "org_memory.db"

    EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBED_DIM = 384  # dimension of the model above

    LLM_MODEL = os.environ.get("LLM_MODEL", "google/flan-t5-base")

    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 80
    TOP_K = 4

    USE_NEO4J = os.environ.get("USE_NEO4J", "false").lower() == "true"
    NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")


Config.DATA_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# 1. DOCUMENT INGESTION & CHUNKING
# ==============================================================================
class DocumentProcessor:
    """Loads PDF / plain-text files and splits them into overlapping chunks,
    keeping page-level provenance for citations."""

    def __init__(self, chunk_size: int = Config.CHUNK_SIZE, overlap: int = Config.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        if LANGCHAIN_AVAILABLE:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
        else:
            self.splitter = None

    def _split(self, text: str) -> List[str]:
        text = text.strip()
        if not text:
            return []
        if self.splitter is not None:
            return self.splitter.split_text(text)
        # fallback naive splitter
        chunks, start = [], 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.overlap
        return chunks

    def load_pdf(self, filepath: str) -> List[Dict[str, Any]]:
        """Returns list of {text, page} for each page of the PDF."""
        reader = PdfReader(filepath)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"text": text, "page": i + 1})
        return pages

    def load_text(self, filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return [{"text": f.read(), "page": 1}]

    def process_file(self, filepath: str, doc_title: str) -> List[Dict[str, Any]]:
        """Returns list of chunk dicts ready for embedding:
        {id, doc_title, page, chunk_index, text}"""
        ext = Path(filepath).suffix.lower()
        if ext == ".pdf":
            pages = self.load_pdf(filepath)
        else:
            pages = self.load_text(filepath)

        chunks = []
        for page in pages:
            for idx, chunk_text in enumerate(self._split(page["text"])):
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "doc_title": doc_title,
                    "page": page["page"],
                    "chunk_index": idx,
                    "text": chunk_text,
                })
        return chunks


# ==============================================================================
# 2. EMBEDDINGS
# ==============================================================================
class EmbeddingManager:
    def __init__(self, model_name: str = Config.EMBED_MODEL):
        print(f"[EmbeddingManager] loading {model_name} ...")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        vecs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        # normalize for cosine similarity via inner product
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        return (vecs / norms).astype("float32")


# ==============================================================================
# 3. VECTOR STORE (FAISS)
# ==============================================================================
class VectorStore:
    """Flat inner-product FAISS index + parallel metadata list, persisted to disk.
    Swappable for Qdrant by replacing this class with a QdrantClient wrapper that
    implements the same add()/search()/save() interface."""

    def __init__(self, dim: int = Config.EMBED_DIM):
        self.dim = dim
        self.metadata: List[Dict[str, Any]] = []
        if Config.INDEX_PATH.exists() and Config.META_PATH.exists():
            self.index = faiss.read_index(str(Config.INDEX_PATH))
            self.metadata = json.loads(Config.META_PATH.read_text())
            print(f"[VectorStore] loaded {len(self.metadata)} vectors from disk")
        else:
            self.index = faiss.IndexFlatIP(dim)

    def add(self, vectors: np.ndarray, metadatas: List[Dict[str, Any]]):
        self.index.add(vectors)
        self.metadata.extend(metadatas)
        self.save()

    def search(self, query_vector: np.ndarray, k: int = Config.TOP_K) -> List[Tuple[float, Dict[str, Any]]]:
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        scores, idxs = self.index.search(query_vector.reshape(1, -1), k)
        results = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx == -1:
                continue
            results.append((float(score), self.metadata[idx]))
        return results

    def save(self):
        faiss.write_index(self.index, str(Config.INDEX_PATH))
        Config.META_PATH.write_text(json.dumps(self.metadata))


# ==============================================================================
# 4. KNOWLEDGE GRAPH
# ==============================================================================
STOPWORDS = {"The", "This", "That", "These", "Those", "It", "In", "On", "At", "A", "An"}
ENTITY_PATTERN = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){0,3})\b")


def extract_entities(text: str, max_entities: int = 15) -> List[str]:
    """Lightweight, dependency-free entity extraction using capitalization
    heuristics. Swap for spaCy NER if higher accuracy is needed."""
    found = []
    for match in ENTITY_PATTERN.findall(text):
        first_word = match.split()[0]
        if first_word in STOPWORDS or len(match) < 3:
            continue
        if match not in found:
            found.append(match)
        if len(found) >= max_entities:
            break
    return found


class KnowledgeGraphNX:
    """In-memory / on-disk knowledge graph using NetworkX.
    Node types: document, entity, project, employee, memory_item
    """

    def __init__(self):
        self.g = nx.MultiDiGraph()
        if Config.GRAPH_PATH.exists():
            data = json.loads(Config.GRAPH_PATH.read_text())
            self.g = nx.node_link_graph(data, directed=True, multigraph=True)
            print(f"[KnowledgeGraph] loaded {self.g.number_of_nodes()} nodes from disk")

    def add_document(self, doc_id: str, title: str):
        self.g.add_node(doc_id, type="document", title=title)

    def link_entities(self, doc_id: str, entities: List[str]):
        for ent in entities:
            ent_id = f"entity::{ent.lower()}"
            self.g.add_node(ent_id, type="entity", name=ent)
            self.g.add_edge(doc_id, ent_id, relation="mentions")

    def add_memory_item(self, item_id: str, title: str, tags: List[str]):
        self.g.add_node(item_id, type="memory_item", title=title)
        for tag in tags:
            tag_id = f"tag::{tag.lower()}"
            self.g.add_node(tag_id, type="tag", name=tag)
            self.g.add_edge(item_id, tag_id, relation="tagged_with")

    def related(self, entity_name: str) -> List[Dict[str, Any]]:
        ent_id = f"entity::{entity_name.lower()}"
        if ent_id not in self.g:
            return []
        out = []
        for neighbor in nx.all_neighbors(self.g, ent_id):
            data = self.g.nodes[neighbor]
            out.append({"id": neighbor, **data})
        return out

    def save(self):
        data = nx.node_link_data(self.g)
        Config.GRAPH_PATH.write_text(json.dumps(data, default=str))


class KnowledgeGraphNeo4j:
    """Optional Neo4j-backed graph with the same interface as KnowledgeGraphNX.
    Enable with env var USE_NEO4J=true and `pip install neo4j`."""

    def __init__(self):
        from neo4j import GraphDatabase  # imported lazily
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI, auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

    def add_document(self, doc_id: str, title: str):
        with self.driver.session() as s:
            s.run("MERGE (d:Document {id:$id}) SET d.title=$title", id=doc_id, title=title)

    def link_entities(self, doc_id: str, entities: List[str]):
        with self.driver.session() as s:
            for ent in entities:
                s.run(
                    """
                    MERGE (e:Entity {name:$name})
                    WITH e
                    MATCH (d:Document {id:$doc_id})
                    MERGE (d)-[:MENTIONS]->(e)
                    """,
                    name=ent, doc_id=doc_id,
                )

    def add_memory_item(self, item_id: str, title: str, tags: List[str]):
        with self.driver.session() as s:
            s.run("MERGE (m:MemoryItem {id:$id}) SET m.title=$title", id=item_id, title=title)
            for tag in tags:
                s.run(
                    """
                    MERGE (t:Tag {name:$tag})
                    WITH t
                    MATCH (m:MemoryItem {id:$id})
                    MERGE (m)-[:TAGGED_WITH]->(t)
                    """,
                    tag=tag, id=item_id,
                )

    def related(self, entity_name: str) -> List[Dict[str, Any]]:
        with self.driver.session() as s:
            result = s.run(
                "MATCH (e:Entity {name:$name})--(n) RETURN n", name=entity_name
            )
            return [dict(r["n"]) for r in result]

    def save(self):
        pass  # Neo4j persists automatically


def get_knowledge_graph():
    if Config.USE_NEO4J:
        try:
            return KnowledgeGraphNeo4j()
        except Exception as e:
            print(f"[KnowledgeGraph] Neo4j unavailable ({e}), falling back to in-memory graph")
    return KnowledgeGraphNX()


# ==============================================================================
# 5. ORGANIZATIONAL MEMORY (SQLite — swap for PostgreSQL via psycopg2/SQLAlchemy)
# ==============================================================================
class OrgMemoryStore:
    """Stores projects, meeting notes, SOPs, best practices, reports.
    Each item is also embedded + indexed in the vector store + linked in the KG
    so it becomes searchable through the same RAG pipeline as documents."""

    VALID_TYPES = {"project", "meeting_note", "sop", "best_practice", "report"}

    def __init__(self, vector_store: VectorStore, embedder: EmbeddingManager, kg):
        self.vector_store = vector_store
        self.embedder = embedder
        self.kg = kg
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()

    def add_item(self, item_type: str, title: str, content: str, tags: Optional[List[str]] = None) -> str:
        if item_type not in self.VALID_TYPES:
            raise ValueError(f"type must be one of {self.VALID_TYPES}")
        tags = tags or []
        item_id = str(uuid.uuid4())
        created_at = dt.datetime.utcnow().isoformat()

        self.conn.execute(
            "INSERT INTO memory_items (id, type, title, content, tags, created_at) VALUES (?,?,?,?,?,?)",
            (item_id, item_type, title, content, json.dumps(tags), created_at),
        )
        self.conn.commit()

        # index into vector store for semantic search / RAG
        vec = self.embedder.encode([content])
        self.vector_store.add(vec, [{
            "id": item_id,
            "doc_title": f"[{item_type}] {title}",
            "page": 1,
            "chunk_index": 0,
            "text": content,
            "source": "org_memory",
        }])

        # index into knowledge graph
        self.kg.add_memory_item(item_id, title, tags)
        entities = extract_entities(content)
        self.kg.link_entities(item_id, entities) if hasattr(self.kg, "link_entities") else None
        self.kg.save()

        return item_id

    def list_items(self, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if item_type:
            cur = self.conn.execute("SELECT * FROM memory_items WHERE type=? ORDER BY created_at DESC", (item_type,))
        else:
            cur = self.conn.execute("SELECT * FROM memory_items ORDER BY created_at DESC")
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def keyword_search(self, query: str) -> List[Dict[str, Any]]:
        like = f"%{query}%"
        cur = self.conn.execute(
            "SELECT * FROM memory_items WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC",
            (like, like),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


# ==============================================================================
# 6. LOCAL LLM (no paid API — HuggingFace transformers, CPU-friendly)
# ==============================================================================
class LocalLLM:
    def __init__(self, model_name: str = Config.LLM_MODEL):
        print(f"[LocalLLM] loading {model_name} ...")
        self.pipe = hf_pipeline("text2text-generation", model=model_name)

    def generate(self, prompt: str, max_new_tokens: int = 300) -> str:
        out = self.pipe(prompt, max_new_tokens=max_new_tokens, do_sample=False)
        return out[0]["generated_text"].strip()


# ==============================================================================
# 7. RAG PIPELINE WITH CITATIONS
# ==============================================================================
class RAGPipeline:
    def __init__(self, vector_store: VectorStore, embedder: EmbeddingManager, llm: LocalLLM):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm = llm

    def retrieve(self, query: str, k: int = Config.TOP_K) -> List[Tuple[float, Dict[str, Any]]]:
        qvec = self.embedder.encode([query])[0]
        return self.vector_store.search(qvec, k=k)

    @staticmethod
    def _build_context(results: List[Tuple[float, Dict[str, Any]]]) -> Tuple[str, List[Dict[str, Any]]]:
        context_lines = []
        citations = []
        for i, (score, meta) in enumerate(results, start=1):
            tag = f"[{i}]"
            context_lines.append(f"{tag} (source: {meta['doc_title']}, page {meta.get('page', 1)}):\n{meta['text']}")
            citations.append({
                "ref": tag,
                "doc_title": meta["doc_title"],
                "page": meta.get("page", 1),
                "score": round(score, 4),
            })
        return "\n\n".join(context_lines), citations

    def answer(self, query: str, k: int = Config.TOP_K) -> Dict[str, Any]:
        results = self.retrieve(query, k=k)
        if not results:
            return {
                "answer": "I couldn't find anything relevant in the knowledge base yet. "
                          "Try ingesting some documents first.",
                "citations": [],
            }
        context, citations = self._build_context(results)
        prompt = (
            "You are an enterprise knowledge assistant. Answer the question ONLY using "
            "the provided context. Cite sources inline using the [n] markers shown in "
            "the context. If the answer isn't in the context, say you don't know.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        answer_text = self.llm.generate(prompt)
        return {"answer": answer_text, "citations": citations}


# ==============================================================================
# 8. MULTI-AGENT ORCHESTRATION
# ==============================================================================
class RetrievalAgent:
    """Responsible for fetching relevant chunks + related KG entities."""

    def __init__(self, rag: RAGPipeline, kg):
        self.rag = rag
        self.kg = kg

    def run(self, query: str) -> Dict[str, Any]:
        results = self.rag.retrieve(query)
        entities = extract_entities(query)
        related = []
        for ent in entities:
            related.extend(self.kg.related(ent))
        return {"results": results, "related_entities": related}


class SynthesisAgent:
    """Responsible for turning retrieved context into a cited, natural-language answer."""

    def __init__(self, rag: RAGPipeline):
        self.rag = rag

    def run(self, query: str, retrieval_output: Dict[str, Any]) -> Dict[str, Any]:
        results = retrieval_output["results"]
        if not results:
            return {"answer": "No relevant information found in the knowledge base.", "citations": []}
        context, citations = self.rag._build_context(results)
        prompt = (
            "You are an enterprise knowledge assistant. Answer the question ONLY using "
            "the provided context, citing sources inline with [n] markers.\n\n"
            f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        )
        answer_text = self.rag.llm.generate(prompt)
        return {"answer": answer_text, "citations": citations}


class DecisionAgent:
    """Rule-based workforce/project decision assistant, with an LLM-generated
    executive summary layered on top of deterministic calculations."""

    def __init__(self, llm: LocalLLM):
        self.llm = llm

    @staticmethod
    def _days_until(deadline_str: str) -> int:
        try:
            deadline = dt.datetime.fromisoformat(deadline_str).date()
        except Exception:
            return 30  # default assumption if unparsable
        return max((deadline - dt.date.today()).days, 0)

    def analyze(self, employees: List[Dict], projects: List[Dict], tasks: List[Dict]) -> Dict[str, Any]:
        recommendations = []

        # --- Employee workload analysis ---
        emp_by_id = {e["id"]: e for e in employees}
        for e in employees:
            capacity = e.get("weekly_capacity_hours", 40)
            workload = e.get("current_workload_hours", 0)
            utilization = workload / capacity if capacity else 0
            if utilization >= 0.9:
                recommendations.append({
                    "type": "reduce_workload",
                    "target": e["name"],
                    "detail": f"{e['name']} is at {utilization*100:.0f}% capacity "
                              f"({workload}h / {capacity}h). Recommend reassigning tasks "
                              f"or reducing scope to avoid burnout.",
                    "priority": "high" if utilization >= 1.0 else "medium",
                })

        # --- Project feasibility & staffing analysis ---
        for p in projects:
            required_skills = set(p.get("required_skills", []))
            remaining_hours = p.get("remaining_hours", 0)
            days_left = self._days_until(p.get("deadline", ""))
            weeks_left = max(days_left / 7.0, 0.1)

            # find employees with matching skills and spare capacity
            candidates = []
            for e in employees:
                skills = set(e.get("skills", []))
                if not required_skills or skills & required_skills:
                    capacity = e.get("weekly_capacity_hours", 40)
                    workload = e.get("current_workload_hours", 0)
                    spare_per_week = max(capacity - workload, 0)
                    available_hours = spare_per_week * weeks_left
                    candidates.append({
                        "employee": e["name"],
                        "match": len(skills & required_skills),
                        "available_hours": available_hours,
                    })

            total_available = sum(c["available_hours"] for c in candidates)
            candidates.sort(key=lambda c: (-c["match"], -c["available_hours"]))

            if total_available < remaining_hours:
                gap = remaining_hours - total_available
                recommendations.append({
                    "type": "recruit",
                    "target": p["name"],
                    "detail": f"Project '{p['name']}' needs ~{remaining_hours}h before its "
                              f"deadline in {days_left} days, but only {total_available:.0f}h of "
                              f"matching capacity is available (gap of {gap:.0f}h). "
                              f"Recommend hiring or contracting staff with skills: "
                              f"{', '.join(required_skills) if required_skills else 'general'}.",
                    "priority": "high" if days_left < 14 else "medium",
                })
            else:
                top = candidates[:3]
                if top:
                    names = ", ".join(c["employee"] for c in top)
                    recommendations.append({
                        "type": "allocate",
                        "target": p["name"],
                        "detail": f"Project '{p['name']}' can be resourced internally. "
                                  f"Recommend allocating: {names} (best skill/capacity match).",
                        "priority": "low",
                    })

        # --- LLM executive summary ---
        summary_prompt = (
            "Summarize the following workforce/project recommendations for an executive "
            "in 3-5 concise sentences, prioritizing the most urgent items:\n\n"
            + "\n".join(f"- ({r['priority']}) {r['detail']}" for r in recommendations)
        )
        try:
            executive_summary = self.llm.generate(summary_prompt, max_new_tokens=200) if recommendations else \
                "No risks or staffing gaps detected with the current data."
        except Exception:
            executive_summary = "Summary unavailable (LLM error); see itemized recommendations."

        return {"recommendations": recommendations, "executive_summary": executive_summary}


class Orchestrator:
    """Routes an incoming chat message to the right agent(s)."""

    DECISION_KEYWORDS = ["recommend", "allocate", "recruit", "workload", "staffing",
                         "hire", "reassign", "deadline risk", "capacity"]

    def __init__(self, retrieval_agent: RetrievalAgent, synthesis_agent: SynthesisAgent):
        self.retrieval_agent = retrieval_agent
        self.synthesis_agent = synthesis_agent

    def route_chat(self, query: str) -> Dict[str, Any]:
        retrieval_output = self.retrieval_agent.run(query)
        synthesis_output = self.synthesis_agent.run(query, retrieval_output)
        synthesis_output["related_entities"] = retrieval_output["related_entities"]
        return synthesis_output


# ==============================================================================
# 9. GLOBAL SINGLETONS
# ==============================================================================
print("=" * 60)
print("Initializing AI Company Brain ...")
print("=" * 60)

embedder = EmbeddingManager()
vector_store = VectorStore()
kg = get_knowledge_graph()
doc_processor = DocumentProcessor()
llm = LocalLLM()
org_memory = OrgMemoryStore(vector_store, embedder, kg)
rag_pipeline = RAGPipeline(vector_store, embedder, llm)

retrieval_agent = RetrievalAgent(rag_pipeline, kg)
synthesis_agent = SynthesisAgent(rag_pipeline)
decision_agent = DecisionAgent(llm)
orchestrator = Orchestrator(retrieval_agent, synthesis_agent)

print("Ready.")


# ==============================================================================
# 10. API MODELS
# ==============================================================================
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    related_entities: List[Dict[str, Any]] = []


class MemoryAddRequest(BaseModel):
    type: str = Field(..., description="project | meeting_note | sop | best_practice | report")
    title: str
    content: str
    tags: List[str] = []


class Employee(BaseModel):
    id: str
    name: str
    skills: List[str] = []
    weekly_capacity_hours: float = 40
    current_workload_hours: float = 0


class Project(BaseModel):
    id: str
    name: str
    required_skills: List[str] = []
    deadline: str  # ISO date, e.g. "2026-08-15"
    priority: int = 3
    remaining_hours: float = 0


class Task(BaseModel):
    id: str
    project_id: str
    assigned_employee_id: Optional[str] = None
    estimated_hours: float = 0
    status: str = "pending"


class DecisionRequest(BaseModel):
    employees: List[Employee]
    projects: List[Project]
    tasks: List[Task] = []


# ==============================================================================
# 11. FASTAPI APP
# ==============================================================================
app = FastAPI(
    title="AI Company Brain",
    description="RAG search + knowledge graph + multi-agent orchestration for enterprise knowledge.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "vectors_indexed": vector_store.index.ntotal,
        "graph_nodes": kg.g.number_of_nodes() if hasattr(kg, "g") else "n/a (neo4j)",
    }


# ---- Document ingestion ----
@app.post("/ingest/document")
async def ingest_document(file: UploadFile = File(...)):
    tmp_path = Config.DATA_DIR / f"upload_{uuid.uuid4().hex}_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    try:
        chunks = doc_processor.process_file(str(tmp_path), doc_title=file.filename)
        if not chunks:
            raise HTTPException(status_code=400, detail="No extractable text found in file.")

        texts = [c["text"] for c in chunks]
        vectors = embedder.encode(texts)
        vector_store.add(vectors, chunks)

        doc_id = f"doc::{file.filename}"
        kg.add_document(doc_id, file.filename)
        for c in chunks:
            entities = extract_entities(c["text"])
            kg.link_entities(doc_id, entities)
        kg.save()

        return {
            "filename": file.filename,
            "chunks_indexed": len(chunks),
            "status": "success",
        }
    finally:
        tmp_path.unlink(missing_ok=True)


# ---- AI Chat (RAG + agents) ----
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = orchestrator.route_chat(req.question)
    return result


# ---- Organizational memory ----
@app.post("/memory/add")
def memory_add(req: MemoryAddRequest):
    item_id = org_memory.add_item(req.type, req.title, req.content, req.tags)
    return {"id": item_id, "status": "stored"}


@app.get("/memory/list")
def memory_list(type: Optional[str] = Query(None)):
    return org_memory.list_items(type)


@app.get("/memory/search")
def memory_search(q: str):
    keyword_hits = org_memory.keyword_search(q)
    semantic_hits = rag_pipeline.retrieve(q)
    return {
        "keyword_matches": keyword_hits,
        "semantic_matches": [{"score": s, **m} for s, m in semantic_hits],
    }


# ---- Knowledge graph exploration ----
@app.get("/graph/entity/{name}")
def graph_entity(name: str):
    return {"entity": name, "related": kg.related(name)}


# ---- AI Decision Assistant ----
@app.post("/decision")
def decision(req: DecisionRequest):
    result = decision_agent.analyze(
        employees=[e.dict() for e in req.employees],
        projects=[p.dict() for p in req.projects],
        tasks=[t.dict() for t in req.tasks],
    )
    return result


# ==============================================================================
# 12. ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
