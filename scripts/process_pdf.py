"""
PDF'i GPT-4 Vision ile işleyip embeddings oluşturan script
Bu script sadece bir kere çalıştırılır ve knowledge_base.json dosyası oluşturur
"""

import os
import json
import base64
from typing import List, Dict
from pypdf import PdfReader
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def count_tokens(text: str) -> int:
    """Token sayısını hesapla"""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(encoding.encode(text))


def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF'den text çıkar (görseller olmadan)"""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def extract_images_and_analyze(pdf_path: str) -> List[Dict]:
    """
    PDF'i sayfa sayfa görsel olarak işle ve GPT-4 Vision ile analiz et
    Her sayfa için görsel analizi + text extraction
    """
    print(f"📄 PDF işleniyor: {pdf_path}")
    print("🖼️  Sayfalar görsele dönüştürülüyor...")

    # PDF'i görsellere çevir
    images = convert_from_path(pdf_path, dpi=150)

    # PDF'den text de çıkar
    reader = PdfReader(pdf_path)

    pages_data = []

    for page_num, (image, page) in enumerate(zip(images, reader.pages), 1):
        print(f"⚙️  Sayfa {page_num}/{len(images)} işleniyor...")

        # Sayfadan normal text çıkar
        text_content = page.extract_text() or ""

        # Görseli base64'e çevir
        import io
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # GPT-4 Vision ile görseli analiz et
        try:
            vision_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Bu görsel bir kullanıcı klavuzundan bir sayfa.
Lütfen bu sayfadaki:
1. Tüm metinleri oku (özellikle görsellerin içindeki yazılar)
2. Görselleri/diyagramları/ekran görüntülerini detaylıca açıkla
3. Adım adım talimatları varsa bunları açıkla
4. Butonlar, menüler, arayüz elementlerini tanımla

Türkçe olarak, kullanıcının bu sayfayı tam anlaması için gereken tüm bilgiyi ver."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )

            vision_analysis = vision_response.choices[0].message.content

        except Exception as e:
            print(f"⚠️  GPT-4 Vision analizi başarısız (sayfa {page_num}): {e}")
            vision_analysis = ""

        # Text ve vision analizini birleştir
        combined_content = f"""
=== SAYFA {page_num} ===

[Metin İçeriği]
{text_content}

[Görsel Analizi]
{vision_analysis}
"""

        pages_data.append({
            "page_number": page_num,
            "text_content": text_content,
            "vision_analysis": vision_analysis,
            "combined_content": combined_content.strip()
        })

        print(f"✓ Sayfa {page_num} tamamlandı")

    return pages_data


def create_chunks(pages_data: List[Dict], chunk_size: int = 1500, overlap: int = 300) -> List[Dict]:
    """Sayfaları anlamlı parçalara böl"""
    chunks = []

    for page in pages_data:
        content = page["combined_content"]
        page_num = page["page_number"]

        # Basit overlapping chunks
        words = content.split()

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)

            if len(chunk_text.strip()) > 100:  # Minimum chunk size
                chunks.append({
                    "text": chunk_text,
                    "page_number": page_num,
                    "chunk_index": len(chunks)
                })

    return chunks


def create_embeddings(chunks: List[Dict]) -> List[Dict]:
    """Her chunk için embedding oluştur"""
    print(f"\n🔮 {len(chunks)} parça için embeddings oluşturuluyor...")

    enriched_chunks = []

    for i, chunk in enumerate(chunks, 1):
        print(f"  {i}/{len(chunks)}", end='\r')

        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=chunk["text"]
            )

            embedding = response.data[0].embedding

            enriched_chunks.append({
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "embedding": embedding,
                "token_count": count_tokens(chunk["text"])
            })

        except Exception as e:
            print(f"\n⚠️  Embedding oluşturulamadı (chunk {i}): {e}")
            continue

    print(f"\n✓ {len(enriched_chunks)} embedding oluşturuldu")
    return enriched_chunks


def save_knowledge_base(chunks: List[Dict], output_path: str):
    """Knowledge base'i JSON olarak kaydet"""
    knowledge_base = {
        "metadata": {
            "total_chunks": len(chunks),
            "total_tokens": sum(c["token_count"] for c in chunks),
            "embedding_model": "text-embedding-3-small",
            "vision_model": "gpt-4o"
        },
        "chunks": chunks
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"\n💾 Knowledge base kaydedildi: {output_path}")
    print(f"   Dosya boyutu: {file_size:.2f} MB")


def main():
    print("=" * 60)
    print("  PDF İşleme ve Knowledge Base Oluşturma")
    print("  GPT-4 Vision ile Görsel Analizi Dahil")
    print("=" * 60)
    print()

    # PDF yolu
    pdf_path = "../data/Manuel utilisateur.docx.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF bulunamadı: {pdf_path}")
        print("Lütfen PDF'i data/ klasörüne koyun.")
        return

    # 1. PDF'i işle (text + vision)
    print("\n📋 Adım 1: PDF Analizi (GPT-4 Vision)")
    print("-" * 60)
    pages_data = extract_images_and_analyze(pdf_path)

    # 2. Chunks oluştur
    print("\n📋 Adım 2: Parçalara Bölme")
    print("-" * 60)
    chunks = create_chunks(pages_data)
    print(f"✓ {len(chunks)} parça oluşturuldu")

    # 3. Embeddings oluştur
    print("\n📋 Adım 3: Embeddings Oluşturma")
    print("-" * 60)
    enriched_chunks = create_embeddings(chunks)

    # 4. Kaydet
    print("\n📋 Adım 4: Knowledge Base Kaydetme")
    print("-" * 60)
    output_path = "../data/knowledge_base.json"
    save_knowledge_base(enriched_chunks, output_path)

    print("\n" + "=" * 60)
    print("✅ İşlem Tamamlandı!")
    print("=" * 60)
    print("\nÖzet:")
    print(f"  • {len(pages_data)} sayfa işlendi")
    print(f"  • {len(enriched_chunks)} chunk oluşturuldu")
    print(f"  • Knowledge base: {output_path}")
    print("\nArtık Vercel'e deploy edebilirsiniz!")


if __name__ == "__main__":
    main()
