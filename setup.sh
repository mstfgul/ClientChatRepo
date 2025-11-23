#!/bin/bash

echo "🚀 Yazar Kasa Chatbot Kurulumu Başlatılıyor..."
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Python versiyonunu kontrol et
echo "📋 Python versiyonu kontrol ediliyor..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 bulunamadı! Lütfen Python 3.8 veya üstünü yükleyin.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION bulundu${NC}"
echo ""

# Virtual environment oluştur
echo "🔧 Virtual environment oluşturuluyor..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment oluşturuldu${NC}"
else
    echo -e "${YELLOW}ℹ Virtual environment zaten mevcut${NC}"
fi
echo ""

# Virtual environment'ı aktifleştir
echo "🔌 Virtual environment aktifleştiriliyor..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment aktif${NC}"
echo ""

# Pip'i güncelle
echo "📦 pip güncelleniyor..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ pip güncellendi${NC}"
echo ""

# Bağımlılıkları yükle
echo "📚 Bağımlılıklar yükleniyor... (bu birkaç dakika sürebilir)"
pip install -r backend/requirements.txt --quiet
echo -e "${GREEN}✓ Tüm bağımlılıklar yüklendi${NC}"
echo ""

# .env dosyası kontrol et
if [ ! -f "backend/.env" ]; then
    echo "⚙️  .env dosyası oluşturuluyor..."
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ .env dosyası oluşturuldu${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  ÖNEMLİ: backend/.env dosyasını açıp OPENAI_API_KEY değerini eklemeyi unutmayın!${NC}"
    echo ""
else
    echo -e "${GREEN}✓ .env dosyası mevcut${NC}"
    echo ""
fi

# data klasörünü kontrol et
if [ ! -d "data" ]; then
    mkdir -p data
    echo -e "${GREEN}✓ data klasörü oluşturuldu${NC}"
fi

echo ""
echo "================================================================"
echo -e "${GREEN}✓ Kurulum tamamlandı!${NC}"
echo "================================================================"
echo ""
echo "Sonraki adımlar:"
echo ""
echo "1. OpenAI API Key'inizi backend/.env dosyasına ekleyin:"
echo "   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
echo ""
echo "2. Uygulamayı başlatmak için:"
echo "   ./run.sh"
echo ""
echo "3. Tarayıcınızda açın:"
echo "   http://localhost:8000"
echo ""
echo "Detaylı bilgi için QUICKSTART.md dosyasına bakın."
echo ""
