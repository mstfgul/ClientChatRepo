"""
Vercel Serverless Function - Chat API
Knowledge base JSON'dan yüklenir ve vector search yapılır
"""

import json
import os
import numpy as np
from openai import OpenAI
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global variable for knowledge base (loaded once)
KNOWLEDGE_BASE = None


def load_knowledge_base():
    """Knowledge base'i yükle (bir kere)"""
    global KNOWLEDGE_BASE

    if KNOWLEDGE_BASE is not None:
        return KNOWLEDGE_BASE

    # Knowledge base path
    kb_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge_base.json')

    try:
        with open(kb_path, 'r', encoding='utf-8') as f:
            KNOWLEDGE_BASE = json.load(f)
        return KNOWLEDGE_BASE
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
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

    # Calculate similarities
    similarities = []
    for chunk in chunks:
        sim = cosine_similarity(query_embedding, chunk['embedding'])
        similarities.append({
            'chunk': chunk,
            'similarity': sim
        })

    # Sort by similarity
    similarities.sort(key=lambda x: x['similarity'], reverse=True)

    # Return top k
    return similarities[:top_k]


def generate_answer(question: str):
    """Soruya cevap üret"""
    try:
        # 1. Query embedding oluştur
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=question
        )
        query_embedding = query_response.data[0].embedding

        # 2. En benzer chunk'ları bul
        similar_chunks = search_similar_chunks(query_embedding, top_k=3)

        if not similar_chunks:
            return {
                "answer": "Üzgünüm, bu konuda bilgi tabanımda yeterli bilgi bulamadım.",
                "sources": []
            }

        # 3. Context oluştur
        context_parts = []
        sources = []

        for item in similar_chunks:
            chunk = item['chunk']
            context_parts.append(chunk['text'])
            sources.append({
                'text': chunk['text'][:200] + '...' if len(chunk['text']) > 200 else chunk['text'],
                'page': chunk['page_number'],
                'similarity': float(item['similarity'])
            })

        context = "\n\n---\n\n".join(context_parts)

        # 4. GPT-4 ile cevap üret
        system_prompt = """Sen yazar kasa uygulaması için yardımcı bir asistansın.
Kullanıcı klavuzunu temel alarak soruları Türkçe olarak net, anlaşılır ve dostane bir şekilde cevapla.
Sadece verilen kullanıcı klavuzu bilgilerine dayanarak cevap ver.
Bilmediğin bir şey sorulursa bunu açıkça belirt.
Cevaplarını adım adım ve örneklerle açıkla.
Görseller hakkında bilgi verirken "klavuzda gösterildiği gibi" diyerek detayları aktar."""

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

        return {
            "answer": answer,
            "sources": sources[:2]  # İlk 2 kaynağı göster
        }

    except Exception as e:
        return {
            "answer": f"Bir hata oluştu: {str(e)}",
            "sources": []
        }


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler"""

    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers()

    def do_GET(self):
        """Health check"""
        self._set_headers()
        kb = load_knowledge_base()

        response = {
            "status": "ok",
            "message": "Chat API is running",
            "knowledge_base_loaded": kb is not None,
            "chunks_count": len(kb['chunks']) if kb else 0
        }

        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle chat requests"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            question = data.get('question', '').strip()

            if not question:
                self._set_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Question is required"
                }).encode())
                return

            # Generate answer
            result = generate_answer(question)

            self._set_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({
                "error": str(e)
            }).encode())
