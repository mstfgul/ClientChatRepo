#!/bin/bash

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Yazar Kasa Chatbot Başlatılıyor..."
echo ""

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment bulunamadı!${NC}"
    echo "Lütfen önce kurulumu yapın:"
    echo "  ./setup.sh"
    exit 1
fi

# Virtual environment'ı aktifleştir
echo "🔌 Virtual environment aktifleştiriliyor..."
source venv/bin/activate

# .env dosyası kontrolü
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ .env dosyası bulunamadı!${NC}"
    echo "Lütfen backend/.env.example dosyasını backend/.env olarak kopyalayın"
    echo "ve OPENAI_API_KEY değerini ekleyin."
    exit 1
fi

# OPENAI_API_KEY kontrolü
if ! grep -q "OPENAI_API_KEY=sk-" backend/.env; then
    echo -e "${YELLOW}⚠️  UYARI: backend/.env dosyasında geçerli bir OPENAI_API_KEY bulunamadı!${NC}"
    echo "Lütfen backend/.env dosyasını açıp API anahtarınızı ekleyin:"
    echo "  OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo ""
    read -p "Devam etmek istiyor musunuz? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ Ortam hazır${NC}"
echo ""
echo "================================================================"
echo "  Uygulama başlatılıyor..."
echo "  Tarayıcınızda http://localhost:8000 adresini açın"
echo ""
echo "  Durdurmak için: Ctrl + C"
echo "================================================================"
echo ""

# Backend'i başlat
cd backend
python app.py
