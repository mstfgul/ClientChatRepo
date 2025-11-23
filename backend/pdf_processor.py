import os
from typing import List
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken


class PDFProcessor:
    """PDF dosyasını işleyip metne çeviren ve parçalara bölen sınıf"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self._count_tokens,
            separators=["\n\n", "\n", " ", ""]
        )

    def _count_tokens(self, text: str) -> int:
        """Token sayısını hesapla"""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(encoding.encode(text))

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF'den text çıkar"""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {pdf_path}")

        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text.strip()

    def split_text(self, text: str) -> List[str]:
        """Metni parçalara böl"""
        chunks = self.text_splitter.split_text(text)
        return chunks

    def process_pdf(self, pdf_path: str) -> List[str]:
        """PDF'i işleyip parçalara böl"""
        print(f"PDF işleniyor: {pdf_path}")
        text = self.extract_text_from_pdf(pdf_path)

        print(f"Toplam karakter sayısı: {len(text)}")
        chunks = self.split_text(text)
        print(f"Oluşturulan parça sayısı: {len(chunks)}")

        return chunks
