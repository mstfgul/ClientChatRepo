import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from rag_system import RAGSystem
import uvicorn

# Environment variables yükle
load_dotenv()

# FastAPI uygulaması
app = FastAPI(
    title="Yazar Kasa Kullanıcı Klavuzu Chatbot",
    description="OpenAI destekli kullanıcı klavuzu chatbot API",
    version="1.0.0"
)

# CORS ayarları
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend dosyalarını servis et
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# RAG sistemi
rag_system = None


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list


@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında RAG sistemini yükle"""
    global rag_system

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("UYARI: OPENAI_API_KEY bulunamadı!")
        return

    rag_system = RAGSystem(openai_api_key=openai_api_key)

    # Eğer bilgi tabanı varsa yükle
    if rag_system.load_collection():
        print("✓ Bilgi tabanı yüklendi")
    else:
        print("ℹ Bilgi tabanı henüz oluşturulmamış. /initialize endpoint'ini kullanın.")


@app.get("/")
async def root():
    """Ana sayfa - Frontend'i göster"""
    return FileResponse("../frontend/index.html")


@app.get("/health")
async def health_check():
    """Sağlık kontrolü"""
    return {
        "status": "healthy",
        "rag_initialized": rag_system is not None and rag_system.collection is not None
    }


@app.post("/initialize")
async def initialize_knowledge_base(pdf_file: UploadFile = File(...)):
    """PDF yükleyerek bilgi tabanını oluştur"""
    global rag_system

    if not rag_system:
        raise HTTPException(status_code=500, detail="RAG sistemi başlatılamadı")

    # PDF'i kaydet
    pdf_path = "../data/user_guide.pdf"
    with open(pdf_path, "wb") as f:
        content = await pdf_file.read()
        f.write(content)

    # Bilgi tabanını oluştur
    try:
        chunk_size = int(os.getenv("CHUNK_SIZE", 1000))
        chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 200))

        rag_system.initialize_knowledge_base(
            pdf_path=pdf_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        return {
            "status": "success",
            "message": "Bilgi tabanı başarıyla oluşturuldu"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bilgi tabanı oluşturulamadı: {str(e)}")


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Soru sor ve cevap al"""
    if not rag_system or not rag_system.collection:
        raise HTTPException(
            status_code=400,
            detail="Bilgi tabanı henüz yüklenmemiş. Lütfen önce PDF yükleyin."
        )

    try:
        max_tokens = int(os.getenv("MAX_TOKENS", 500))
        temperature = float(os.getenv("TEMPERATURE", 0.7))

        result = rag_system.generate_answer(
            question=request.question,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cevap üretilemedi: {str(e)}")


@app.get("/status")
async def get_status():
    """Sistem durumunu kontrol et"""
    if not rag_system:
        return {"initialized": False, "message": "RAG sistemi başlatılmamış"}

    has_collection = rag_system.collection is not None

    if has_collection:
        count = rag_system.collection.count()
        return {
            "initialized": True,
            "chunks_count": count,
            "message": f"Sistem hazır. {count} parça yüklenmiş."
        }
    else:
        return {
            "initialized": False,
            "message": "Bilgi tabanı henüz oluşturulmamış"
        }


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
