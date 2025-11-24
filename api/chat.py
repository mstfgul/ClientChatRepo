"""
Vercel Serverless Function - Chat API
Knowledge base JSON'dan yüklenir ve vector search yapılır
"""

import json
import os
import numpy as np
from openai import OpenAI
from http.server import BaseHTTPRequestHandler

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key present: {api_key is not None}, Length: {len(api_key) if api_key else 0}")

if not api_key:
    print("❌ OPENAI_API_KEY environment variable not set!")
    client = None
else:
    try:
        client = OpenAI(api_key=api_key)
        print("✓ OpenAI client initialized successfully")
    except Exception as e:
        print(f"❌ OpenAI initialization error: {e}")
        import traceback
        traceback.print_exc()
        client = None

# Global variable for knowledge base (loaded once)
KNOWLEDGE_BASE = None


def load_knowledge_base():
    """Knowledge base'i yükle (bir kere)"""
    global KNOWLEDGE_BASE

    if KNOWLEDGE_BASE is not None:
        return KNOWLEDGE_BASE

    # Knowledge base path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_path = os.path.join(base_dir, 'data', 'knowledge_base.json')

    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            KNOWLEDGE_BASE = json.load(f)
        print(f"✓ Knowledge base loaded: {len(KNOWLEDGE_BASE.get('chunks', []))} chunks")
        return KNOWLEDGE_BASE
    except Exception as e:
        print(f"❌ Error loading knowledge base: {e}")
        print(f"   Tried path: {kb_path}")
        print(f"   Base dir: {base_dir}")
        return None


def cosine_similarity(vec1, vec2):
    """İki vektör arasındaki cosine similarity hesapla"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def search_similar_chunks(query_embedding, top_k=3):
    """Query embedding'e en yakın chunk'ları bul"""
    kb = load_knowledge_base()

    if not kb or 'chunks' not in kb:
        return []

    chunks = kb['chunks']
    similarities = []

    for chunk in chunks:
        sim = cosine_similarity(query_embedding, chunk['embedding'])
        similarities.append({'chunk': chunk, 'similarity': sim})

    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities[:top_k]


def generate_answer(question: str):
    """Soruya cevap üret"""
    if not client:
        return {"answer": "OpenAI client başlatılamadı", "sources": []}

    try:
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=question
        )
        query_embedding = query_response.data[0].embedding

        similar_chunks = search_similar_chunks(query_embedding, top_k=3)

        if not similar_chunks:
            return {
                "answer": "Üzgünüm, bu konuda bilgi tabanımda yeterli bilgi bulamadım.",
                "sources": []
            }

        context_parts = []
        sources = []

        for item in similar_chunks:
            chunk = item['chunk']
            context_parts.append(chunk['text'])
            sources.append({
                'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                'page': chunk.get('page_number', 0),
                'similarity': float(item['similarity'])
            })

        context = "\n\n---\n\n".join(context_parts)

        system_prompt = """Sen yazar kasa uygulaması için yardımcı bir asistansın.
Kullanıcı klavuzunu temel alarak soruları Türkçe olarak net, anlaşılır ve dostane bir şekilde cevapla.
Sadece verilen kullanıcı klavuzu bilgilerine dayanarak cevap ver.
Cevaplarını adım adım ve örneklerle açıkla."""

        user_prompt = f"""Kullanıcı Klavuzu İçeriği:

{context}

Kullanıcı Sorusu: {question}

Lütfen yukarıdaki kullanıcı klavuzu bilgilerine dayanarak soruyu cevapla."""

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        answer = completion.choices[0].message.content

        return {"answer": answer, "sources": sources[:2]}

    except Exception as e:
        print(f"Error in generate_answer: {e}")
        return {"answer": f"Bir hata oluştu: {str(e)}", "sources": []}


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler"""

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        try:
            kb = load_knowledge_base()
            response = {
                "status": "ok",
                "message": "Chat API is running",
                "knowledge_base_loaded": kb is not None,
                "chunks_count": len(kb.get('chunks', [])) if kb else 0
            }

            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            print(f"GET error: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            question = data.get('question', '').strip()

            if not question:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Question is required"}).encode())
                return

            result = generate_answer(question)

            self._set_headers(200)
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            print(f"POST error: {e}")
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
