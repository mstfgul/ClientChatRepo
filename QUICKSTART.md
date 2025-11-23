# Hızlı Başlangıç Rehberi

Bu rehber, uygulamayı 5 dakikada çalıştırmanızı sağlayacaktır.

## Adım 1: OpenAI API Key Alın

1. [OpenAI Platform](https://platform.openai.com/api-keys) sayfasına gidin
2. Hesap oluşturun veya giriş yapın
3. "Create new secret key" butonuna tıklayın
4. Oluşan anahtarı kopyalayın (başı `sk-` ile başlar)

## Adım 2: Kurulum

Terminal'de sırasıyla şu komutları çalıştırın:

```bash
# Proje klasörüne gidin
cd /Users/mustafagul/Desktop/KasaSystem/ClientGuideBot

# Backend klasörüne geçin
cd backend

# Gerekli paketleri yükleyin
pip install -r requirements.txt

# .env dosyası oluşturun
cp .env.example .env
```

## Adım 3: API Anahtarını Ayarlayın

`.env` dosyasını metin editörü ile açın ve API anahtarınızı ekleyin:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**ÖNEMLİ**: `sk-xxxxxxx...` yerine kendi API anahtarınızı yapıştırın!

## Adım 4: Uygulamayı Başlatın

```bash
# Backend klasöründeyken
python app.py
```

Terminal şu mesajı gösterecek:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Adım 5: Tarayıcıda Açın

1. Tarayıcınızda `http://localhost:8000` adresine gidin
2. PDF yükleme ekranını göreceksiniz

## Adım 6: Kullanıcı Klavuzunu Yükleyin

1. "Choose File" butonuna tıklayın
2. Kullanıcı klavuzunuzu (PDF) seçin
3. "Klavuzu Yükle ve Başlat" butonuna tıklayın
4. İşlem bitene kadar bekleyin (30 saniye - 2 dakika)

## Adım 7: Soru Sormaya Başlayın!

Chatbot hazır! Artık sorularınızı sorabilirsiniz:

- "Uygulamaya nasıl giriş yapabilirim?"
- "Satış işlemi nasıl yapılır?"
- "Raporları nasıl görüntülerim?"

## Sorun mu var?

### "ModuleNotFoundError" hatası
```bash
pip install -r requirements.txt
```
komutunu tekrar çalıştırın.

### "OPENAI_API_KEY bulunamadı" hatası
- `.env` dosyasının `backend/` klasöründe olduğundan emin olun
- API anahtarının doğru kopyalandığından emin olun

### Sayfa açılmıyor
- Terminal'de uygulamanın çalıştığından emin olun
- `http://localhost:8000` adresini doğru yazdığınızdan emin olun

## Uygulamayı Durdurmak

Terminal'de `Ctrl + C` tuşlarına basın.

## Tekrar Başlatmak

```bash
cd backend
python app.py
```

PDF'i tekrar yüklemenize gerek yok, bilgi tabanı saklanır!

---

Daha fazla bilgi için `README.md` dosyasına bakın.
