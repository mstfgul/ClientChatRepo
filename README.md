# Yazar Kasa Kullanıcı Klavuzu Chatbot

OpenAI API destekli, kullanıcı klavuzunuzu akıllı chatbot'a dönüştüren web uygulaması.
**Vercel'de çalışmaya hazır - External veritabanı gerektirmez!**

## Özellikler

- **GPT-4 Vision ile Görsel Analizi**: PDF'deki görseller, tablolar ve diyagramlar otomatik analiz edilir
- **RAG (Retrieval-Augmented Generation)**: Soruya en uygun dokuman parçalarını bulup GPT-4'e gönderir
- **Modern Web Arayüzü**: Kullanıcı dostu, responsive chat arayüzü
- **Serverless Architecture**: Vercel'de çalışır, ölçeklenebilir
- **No External DB**: Embeddings JSON dosyasında saklanır (hızlı, ucuz, basit)
- **Kaynak Gösterimi**: Cevapların hangi sayfa ve bölümlerden geldiğini gösterir

## Sistem Mimarisi

### "Bake-in" Yaklaşımı

```
┌──────────────────────────────────────────────┐
│  1. LOCAL PDF İşleme (Tek Seferlik)         │
│  ─────────────────────────────────────────   │
│  PDF → GPT-4 Vision → Embeddings → JSON     │
└──────────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────┐
│  2. VERCEL DEPLOYMENT                        │
│  ─────────────────────────────────────────   │
│  ┌────────────┐         ┌────────────┐      │
│  │  Frontend  │────────▶│    API     │      │
│  │ (Static)   │         │ (Serverless│      │
│  └────────────┘         │ Function)  │      │
│                         └──────┬─────┘      │
│                                │             │
│                         ┌──────▼─────┐      │
│                         │ knowledge_ │      │
│                         │ base.json  │      │
│                         │ (Embedded) │      │
│                         └──────┬─────┘      │
│                                │             │
│                         ┌──────▼─────┐      │
│                         │  OpenAI    │      │
│                         │  GPT-4     │      │
│                         └────────────┘      │
└──────────────────────────────────────────────┘
```

**Avantajlar**:
- ✅ External veritabanı yok (Pinecone, ChromaDB vs. gereksiz)
- ✅ Deployment basit (sadece JSON + kod)
- ✅ Hızlı (local vector search)
- ✅ Ucuz (DB maliyeti yok)
- ✅ Offline processing (PDF bir kere işlenir)

## Hızlı Başlangıç

### Vercel'e Deploy (Önerilen)

Detaylı adımlar için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın.

**Özet**:
1. PDF'i local'de işleyin → `knowledge_base.json` oluşturun
2. Vercel'e deploy edin
3. Müşterileriniz kullanmaya başlasın!

### Local Development

#### 1. PDF İşleme (Tek Seferlik)

```bash
# Script dependencies
cd scripts
pip install -r requirements.txt

# poppler-utils kurulumu
brew install poppler  # macOS

# .env dosyası oluştur (proje ana dizininde)
echo "OPENAI_API_KEY=sk-xxxxxxxx" > .env

# PDF'i data/ klasörüne kopyala
cp /path/to/Manuel\ utilisateur.docx.pdf data/

# PDF'i işle
python process_pdf.py
```

Bu işlem `data/knowledge_base.json` dosyasını oluşturacaktır.

#### 2. Local Test (Opsiyonel)

Local'de test etmek istiyorsanız:

```bash
# Backend klasöründeki eski dosyalar local test için
cd backend
pip install -r requirements.txt
python app.py
```

**NOT**: Production'da backend/ klasörü kullanılmaz. Vercel `api/` klasörünü kullanır.

## Kullanım

### Chatbot'u Kullanma

1. Deploy edilmiş URL'i açın (örn: `https://yazar-kasa-chatbot.vercel.app`)
2. Sistem otomatik olarak yüklenecektir
3. Metin kutusuna sorunuzu yazın
4. "Gönder" butonuna tıklayın veya Enter tuşuna basın
5. Chatbot kullanıcı klavuzunuza dayanarak cevap verecektir
6. Cevapların altında ilgili kaynak bölümleri ve sayfa numaraları gösterilir

### Örnek Sorular

- "Uygulamaya nasıl giriş yapabilirim?"
- "Satış işlemi nasıl yapılır?"
- "Ürün girişi nasıl yapılır?"
- "Raporları nasıl görüntülerim?"
- "Stok güncelleme işlemi nedir?"

## API Endpoints

### `GET /api/chat`
Sistem sağlık kontrolü ve bilgi tabanı durumu

**Response**:
```json
{
  "status": "ok",
  "knowledge_base_loaded": true,
  "chunks_count": 150
}
```

### `POST /api/chat`
Soru sor ve cevap al

**Body**:
```json
{
  "question": "Satış işlemi nasıl yapılır?"
}
```

**Response**:
```json
{
  "answer": "Satış işlemi için şu adımları izlemelisiniz...",
  "sources": [
    {
      "text": "kaynak metin...",
      "page": 5,
      "similarity": 0.92
    }
  ]
}
```

## Yapılandırma

### PDF İşleme (Local - scripts/process_pdf.py)

Dosyayı düzenleyerek ayarlayabilirsiniz:

- `chunk_size`: PDF parçalarının boyutu (varsayılan: 1500)
- `chunk_overlap`: Parçalar arası çakışma (varsayılan: 300)
- `dpi`: PDF'den görsel çıkarma çözünürlüğü (varsayılan: 150)

### Chat API (api/chat.py)

- `max_tokens`: Cevap maksimum token sayısı (varsayılan: 800)
- `temperature`: GPT yaratıcılık seviyesi 0-1 arası (varsayılan: 0.7)
- `model`: GPT modeli (varsayılan: "gpt-4o")

## Proje Yapısı

```
ClientGuideBot/
├── api/                        # 🚀 Vercel Serverless Functions
│   └── chat.py                 # Chat API endpoint
├── frontend/                   # 🎨 Static Frontend
│   ├── index.html
│   ├── style.css
│   └── script.js
├── scripts/                    # 🔧 Local PDF Processing
│   ├── process_pdf.py          # PDF → knowledge_base.json
│   └── requirements.txt        # Processing dependencies
├── data/                       # 📦 Data Files
│   ├── Manuel utilisateur.docx.pdf  # Original PDF (gitignore)
│   └── knowledge_base.json     # ✅ Processed embeddings (deployed)
├── backend/                    # 📝 Legacy (local development only)
│   └── ...                     # NOT deployed to Vercel
├── vercel.json                 # ⚙️ Vercel Configuration
├── requirements.txt            # 📚 Production Dependencies
├── .vercelignore              # 🚫 Deployment exclusions
├── DEPLOYMENT.md              # 📖 Deployment Guide
└── README.md
```

## Nasıl Çalışır?

### Offline (Tek Seferlik)

1. **PDF → Görseller**: Her sayfa yüksek çözünürlükle görüntüye çevrilir
2. **GPT-4 Vision Analizi**: Her sayfadaki görseller, tablolar, diyagramlar analiz edilir
3. **Metin Çıkarma**: PyPDF2 ile normal metin çıkarılır
4. **Birleştirme**: Metin + görsel analizi birleştirilir
5. **Parçalama**: İçerik anlamlı parçalara (chunks) bölünür
6. **Embedding**: Her parça OpenAI Embeddings ile vektöre dönüştürülür
7. **JSON Export**: Tüm embeddings `knowledge_base.json` dosyasına kaydedilir

### Online (Her Request)

1. **Soru Gelir**: Kullanıcı soru sorar
2. **Query Embedding**: Soru vektöre çevrilir
3. **Vector Search**: JSON'dan en benzer 3 chunk bulunur (cosine similarity)
4. **Context Oluştur**: Bulunan chunk'lar birleştirilir
5. **GPT-4 Çağrısı**: Context + soru GPT-4'e gönderilir
6. **Cevap Dönüyor**: GPT-4'ün cevabı + kaynaklar kullanıcıya iletilir

## Maliyet

### OpenAI API

**İlk Kurulum (tek seferlik, local)**:
- GPT-4 Vision (sayfa analizi): ~$0.10-0.50
- Embeddings (text-embedding-3-small): ~$0.01-0.05
- **Toplam**: ~$0.15-0.55

**Runtime (her soru başına)**:
- Query embedding: ~$0.00001
- GPT-4o completion: ~$0.001-0.003
- **Toplam**: ~$0.001-0.003

**Aylık (1000 soru varsayımı)**: ~$1-3

### Vercel Hosting

**Hobby Plan (Ücretsiz)**:
- 100 GB bandwidth/ay
- 100 GB-hours serverless execution/ay
- Çoğu KOBİ için yeterli

**Pro Plan ($20/ay)**:
- 1 TB bandwidth
- 1000 GB-hours execution
- Custom domains

## Güvenlik

- API anahtarınızı `.env` dosyasında saklayın
- `.env` dosyasını asla paylaşmayın veya git'e eklemeyin
- Üretim ortamında CORS ayarlarını dikkatle yapılandırın

## Sorun Giderme

### "OPENAI_API_KEY bulunamadı" hatası
`.env` dosyasını oluşturup API anahtarınızı eklediğinizden emin olun.

### PDF yüklenmiyor
- PDF'in bozuk olmadığından emin olun
- PDF boyutunun çok büyük olmadığını kontrol edin (max 50MB önerilir)

### Chatbot yavaş cevap veriyor
- GPT-4 yerine GPT-3.5-turbo kullanabilirsiniz (rag_system.py:99)
- MAX_TOKENS değerini azaltabilirsiniz

### ChromaDB hatası
`chroma_db` klasörünü silip yeniden başlatmayı deneyin.

## Geliştirme

### Yeni Özellikler Eklemek

1. Backend API'ye yeni endpoint ekleyin (`app.py`)
2. Frontend'de ilgili fonksiyonu yazın (`script.js`)
3. Gerekirse stil ekleyin (`style.css`)

### Model Değiştirme

`backend/rag_system.py:99` satırında modeli değiştirebilirsiniz:

```python
model="gpt-3.5-turbo",  # veya "gpt-4-turbo-preview"
```

## Lisans

Bu proje özel kullanım içindir.

## Destek

Sorularınız için lütfen projeyi geliştiren kişi ile iletişime geçin.
