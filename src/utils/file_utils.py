import os
import shutil
import base64
from pathlib import Path
import PyPDF2
import docx
from io import BytesIO

def save_uploaded_file(uploaded_file, destination_path: Path) -> bool:
    """
    Сохраняет загруженный файл по указанному пути
    
    Args:
        uploaded_file: Файл, загруженный через st.file_uploader
        destination_path: Путь, по которому нужно сохранить файл
        
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        # Гарантируем, что директория существует
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Записываем содержимое файла
        with open(destination_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return False

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Извлекает текст из PDF-файла
    
    Args:
        pdf_path: Путь к PDF-файлу
        
    Returns:
        str: Извлеченный текст
    """
    try:
        text = ""
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Ошибка при извлечении текста из PDF: {e}")
        return ""

def extract_text_from_docx(docx_path: Path) -> str:
    """
    Извлекает текст из DOCX-файла
    
    Args:
        docx_path: Путь к DOCX-файлу
        
    Returns:
        str: Извлеченный текст
    """
    try:
        doc = docx.Document(docx_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        print(f"Ошибка при извлечении текста из DOCX: {e}")
        return ""

def extract_text_from_file(file_path: Path) -> str:
    """
    Извлекает текст из файла в зависимости от его формата
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        str: Извлеченный текст
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == ".pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        return extract_text_from_docx(file_path)
    elif file_extension == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка при чтении текстового файла: {e}")
            return ""
    else:
        print(f"Неподдерживаемый формат файла: {file_extension}")
        return ""

def get_image_as_base64(image_path):
    """
    Конвертирует изображение в строку base64 для встраивания в HTML
    
    Args:
        image_path: Путь к файлу изображения
        
    Returns:
        str: Строка base64 с изображением
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string
    except Exception as e:
        print(f"Ошибка при конвертации изображения в base64: {e}")
        return "" 