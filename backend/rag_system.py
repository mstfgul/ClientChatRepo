import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from pdf_processor import PDFProcessor


class RAGSystem:
    """Retrieval-Augmented Generation sistemi"""

    def __init__(self, openai_api_key: str, collection_name: str = "user_guide"):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

        # ChromaDB kurulumu
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection_name = collection_name
        self.collection = None

    def initialize_knowledge_base(self, pdf_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """PDF'den bilgi tabanını oluştur"""
        # Önce var olan collection'ı sil
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            print(f"Eski '{self.collection_name}' koleksiyonu silindi")
        except Exception:
            pass

        # Yeni collection oluştur
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Kullanıcı klavuzu dokümantasyonu"}
        )

        # PDF'i işle
        processor = PDFProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = processor.process_pdf(pdf_path)

        # Embeddings oluştur ve kaydet
        print("Embeddings oluşturuluyor...")
        for idx, chunk in enumerate(chunks):
            embedding = self.embeddings.embed_query(chunk)
            self.collection.add(
                embeddings=[embedding],
                documents=[chunk],
                ids=[f"chunk_{idx}"]
            )

        print(f"✓ Bilgi tabanı hazır! {len(chunks)} parça yüklendi.")

    def load_collection(self):
        """Var olan collection'ı yükle"""
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            return True
        except Exception as e:
            print(f"Collection yüklenemedi: {e}")
            return False

    def search_relevant_chunks(self, query: str, n_results: int = 3) -> List[str]:
        """Sorguya en uygun parçaları bul"""
        if not self.collection:
            if not self.load_collection():
                return []

        query_embedding = self.embeddings.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return results['documents'][0] if results['documents'] else []

    def generate_answer(self, question: str, max_tokens: int = 500, temperature: float = 0.7) -> Dict:
        """Soruya cevap üret"""
        # İlgili dokuman parçalarını bul
        relevant_chunks = self.search_relevant_chunks(question, n_results=3)

        if not relevant_chunks:
            return {
                "answer": "Üzgünüm, bu konuda bilgi tabanımda yeterli bilgi bulamadım. Lütfen sorunuzu farklı şekilde sormayı deneyin.",
                "sources": []
            }

        # Context oluştur
        context = "\n\n".join(relevant_chunks)

        # System prompt
        system_prompt = """Sen yazar kasa uygulaması için yardımcı bir asistansın.
Kullanıcı klavuzunu temel alarak soruları Türkçe olarak net, anlaşılır ve dostane bir şekilde cevapla.
Sadece verilen kullanıcı klavuzu bilgilerine dayanarak cevap ver.
Bilmediğin bir şey sorulursa bunu açıkça belirt.
Cevaplarını adım adım ve örneklerle açıkla."""

        # User prompt
        user_prompt = f"""Kullanıcı Klavuzu İçeriği:
{context}

Kullanıcı Sorusu: {question}

Lütfen yukarıdaki kullanıcı klavuzu bilgilerine dayanarak soruyu cevapla."""

        # OpenAI API çağrısı
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": relevant_chunks[:2]  # İlk 2 kaynağı göster
        }
