# Vercel Deployment Rehberi

Bu rehber, Yazar Kasa Chatbot uygulamasını Vercel'e deploy etmek için gereken adımları içerir.

## Mimari

Bu uygulama **"Bake-in"** yaklaşımı kullanır:
- PDF bir kere local'de işlenir (GPT-4 Vision ile)
- Embeddings ve chunks JSON dosyasına kaydedilir
- JSON dosyası Vercel'e deploy edilir
- External veritabanı gerekmez (Pinecone, ChromaDB vb. YOK)
- Her request'te sadece vector search yapılır (hızlı ve ucuz)

## Ön Hazırlık (Local)

### 1. PDF'i İşleyin

PDF'i işlemek için local bilgisayarınızda GPT-4 Vision kullanarak embeddings oluşturacağız.

#### Gereksinimleri Yükleyin

```bash
cd scripts
pip install -r requirements.txt
```

**Önemli**: `poppler-utils` kurulmalı (pdf2image için):

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# Windows
# https://github.com/oschwartz10612/poppler-windows/releases/
```

#### .env Dosyası Oluşturun

Proje ana dizininde `.env` dosyası oluşturun:

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### PDF'i data/ Klasörüne Koyun

```bash
# PDF dosyanızı data/ klasörüne kopyalayın
cp /path/to/Manuel\ utilisateur.docx.pdf data/
```

#### PDF'i İşleyin

```bash
cd scripts
python process_pdf.py
```

Bu işlem:
1. PDF'in her sayfasını görüntüye çevirir
2. Her sayfayı GPT-4 Vision ile analiz eder
3. Metin ve görsel analizini birleştirir
4. Embeddings oluşturur
5. `data/knowledge_base.json` dosyasını oluşturur

**Süre**: ~2-5 dakika (PDF boyutuna göre)
**Maliyet**: ~$0.10-0.50 (tek seferlik)

#### knowledge_base.json Kontrol

İşlem tamamlandıktan sonra:

```bash
ls -lh data/knowledge_base.json
```

Dosya boyutu yaklaşık 5-50 MB olmalı (PDF'e göre).

## Vercel Deployment

### 1. Vercel Hesabı Oluşturun

[vercel.com](https://vercel.com) adresinden ücretsiz hesap açın.

### 2. Vercel CLI Yükleyin

```bash
npm install -g vercel
```

### 3. Vercel'e Giriş Yapın

```bash
vercel login
```

### 4. Environment Variables Ayarlayın

Vercel dashboard'dan veya CLI ile:

```bash
vercel env add OPENAI_API_KEY
```

OpenAI API Key'inizi girin (sk-...).

### 5. Deploy Edin

Proje ana dizininde:

```bash
vercel
```

İlk deploy'da sorulan sorular:
- **Setup and deploy?** → Yes
- **Which scope?** → Kendi hesabınızı seçin
- **Link to existing project?** → No
- **What's your project's name?** → `yazar-kasa-chatbot` (veya istediğiniz isim)
- **In which directory is your code located?** → `./`

Deploy tamamlandığında bir URL alacaksınız:
```
https://yazar-kasa-chatbot-xxxxx.vercel.app
```

### 6. Production Deploy

Test ettikten sonra production'a gönderin:

```bash
vercel --prod
```

## Dosya Yapısı (Deploy Edilenler)

```
Vercel'e Deploy Edilen Dosyalar:
├── api/
│   └── chat.py              # Serverless function
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── data/
│   └── knowledge_base.json  # ✅ Bu dosya MUTLAKA olmalı!
├── requirements.txt         # Production dependencies
└── vercel.json             # Vercel configuration
```

## Test

Deploy sonrası test edin:

```bash
# Health check
curl https://your-app.vercel.app/api/chat

# Soru sor
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Uygulamaya nasıl giriş yapabilirim?"}'
```

## Güncelleme Süreci

### PDF Güncellendiğinde

1. Yeni PDF'i `data/` klasörüne kopyalayın
2. `scripts/process_pdf.py` scriptini tekrar çalıştırın
3. Yeni `knowledge_base.json` oluşacak
4. Vercel'e tekrar deploy edin:

```bash
vercel --prod
```

### Kod Güncellemesi

Sadece kodu değiştirdiyseniz:

```bash
git add .
git commit -m "Update code"
vercel --prod
```

## Domain Bağlama

### 1. Vercel Dashboard

- Project settings → Domains
- Add domain
- DNS kayıtlarını güncelleyin

### 2. Custom Domain Örneği

```
yazar-kasa-destek.com → CNAME → cname.vercel-dns.com
```

## Maliyet Hesaplama

### Vercel (Ücretsiz Plan)
- 100 GB bandwidth/ay
- Serverless function execution: 100 GB-hours/ay
- Çoğu küçük/orta işletme için yeterli

### OpenAI Kullanımı

**İlk Kurulum (tek seferlik)**:
- PDF işleme (GPT-4 Vision): ~$0.10-0.50
- Embeddings: ~$0.01-0.05
- **Toplam**: ~$0.15-0.55

**Her Soru (runtime)**:
- Embedding (query): ~$0.00001
- GPT-4 completion: ~$0.001-0.003
- **Toplam**: ~$0.001-0.003 per soru

**Aylık (1000 soru için)**: ~$1-3

## Monitoring

### Vercel Dashboard

- Analytics → Performance
- Function logs → Runtime logs
- Deployment logs → Build logs

### Error Tracking

```bash
# Son deployment loglarını gör
vercel logs

# Spesifik deployment
vercel logs [deployment-url]
```

## Troubleshooting

### "knowledge_base.json not found" Hatası

```bash
# Dosyanın var olduğundan emin olun
ls -la data/knowledge_base.json

# .vercelignore'da exclude edilmediğinden emin olun
cat .vercelignore
```

### "Function timeout" Hatası

`vercel.json` dosyasında timeout artırın:

```json
{
  "functions": {
    "api/chat.py": {
      "maxDuration": 60
    }
  }
}
```

### "Module not found" Hatası

`requirements.txt` dosyasını kontrol edin. Production dependencies eksik olabilir.

### CORS Hatası

Frontend farklı domainse, `api/chat.py` dosyasında CORS ayarları yapılandırılmış olmalı (zaten yapılandırılmış).

## Güvenlik

### API Key Güvenliği

- ✅ Environment variables kullanın
- ✅ `.env` dosyasını git'e eklemeyin
- ✅ Vercel secrets kullanın

### Rate Limiting

Vercel otomatik DDoS koruması sağlar. Ekstra rate limiting için:

```python
# api/chat.py içinde
from functools import lru_cache
import time

# Simple rate limiting
request_times = []

def check_rate_limit(max_requests=10, window=60):
    now = time.time()
    global request_times
    request_times = [t for t in request_times if now - t < window]

    if len(request_times) >= max_requests:
        return False

    request_times.append(now)
    return True
```

## Optimizasyon

### Bundle Size

`knowledge_base.json` çok büyükse:

1. Chunk size'ı artırın (daha az chunk)
2. Embedding compression kullanın
3. Sadece en önemli sayfaları ekleyin

### Cold Start

Vercel functions soğuk başlangıçta ~1-2 saniye sürebilir. Isınmış durumda <100ms.

## Backup

### Knowledge Base Backup

```bash
# Git'e ekleyin (opsiyonel - büyükse LFS kullanın)
git lfs track "data/knowledge_base.json"
git add data/knowledge_base.json
git commit -m "Update knowledge base"
```

### Otomatik Backup

```bash
# Cron job ile otomatik backup
0 0 * * * cp /path/to/data/knowledge_base.json /path/to/backups/kb-$(date +\%Y\%m\%d).json
```

## Sonraki Adımlar

1. ✅ PDF'i işleyin → `knowledge_base.json` oluştur
2. ✅ Vercel'e deploy edin
3. ✅ Test edin
4. Domain bağlayın (opsiyonel)
5. Analytics kurun
6. Müşterilerinizle paylaşın!

## Destek

Sorularınız için:
- Vercel Docs: https://vercel.com/docs
- OpenAI Docs: https://platform.openai.com/docs
