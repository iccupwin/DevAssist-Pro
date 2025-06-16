import streamlit as st
import os
from pathlib import Path
import uuid
from src.config import settings
from src.utils import file_utils


def render_upload_section(upload_dir: Path = settings.UPLOAD_DIR):
    """Отображает секцию загрузки файлов и сохраняет их в session_state под ключами tz, kp, additional."""
    
    st.header("Загрузка документов для анализа", anchor=False)
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 12px 15px; border-radius: 8px; border-left: 4px solid #2E75D6; margin-bottom: 25px;'>
        <p style='margin:0; font-size: 0.95rem;'>Загрузите техническое задание и коммерческие предложения для их сравнительного анализа с помощью AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Основные документы - ТЗ и КП
    row1_cols = st.columns([1, 1])
    
    with row1_cols[0]:
        st.markdown("""
        <div style='background-color: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%;'>
            <h3 style='font-size: 1.2rem; color: #1A1E3A; margin-bottom: 10px;'>📄 Техническое задание</h3>
            <p style='color: #64748B; font-size: 0.9rem; margin-bottom: 15px;'>Загрузите файл ТЗ в формате PDF или DOCX</p>
        </div>
        """, unsafe_allow_html=True)
        
        tz_file_uploader = st.file_uploader(
            "Выберите файл ТЗ",
            type=["pdf", "docx"],
            key="tz_uploader",
            accept_multiple_files=False,
            label_visibility="collapsed"
        )
        
        if tz_file_uploader is not None:
            file_extension = os.path.splitext(tz_file_uploader.name)[1].lower()
            unique_filename = f"tz_{uuid.uuid4().hex}{file_extension}"
            file_path = upload_dir / unique_filename
            file_utils.save_uploaded_file(tz_file_uploader, file_path)
            
            # Используем ключ "tz"
            st.session_state.uploaded_files["tz"] = {
                "original_name": tz_file_uploader.name,
                "file_path": str(file_path),
                "extension": file_extension
            }
            st.success(f"✅ Файл '{tz_file_uploader.name}' успешно загружен!")
    
    with row1_cols[1]:
        st.markdown("""
        <div style='background-color: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); height: 100%;'>
            <h3 style='font-size: 1.2rem; color: #1A1E3A; margin-bottom: 10px;'>📑 Коммерческие предложения</h3>
            <p style='color: #64748B; font-size: 0.9rem; margin-bottom: 15px;'>Загрузите один или несколько файлов КП</p>
        </div>
        """, unsafe_allow_html=True)
        
        kp_files_uploader = st.file_uploader(
            "Выберите файлы КП",
            type=["pdf", "docx"],
            key="kp_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if kp_files_uploader:
            # Используем ключ "kp"
            st.session_state.uploaded_files["kp"] = [] 
            
            for kp_file in kp_files_uploader:
                file_extension = os.path.splitext(kp_file.name)[1].lower()
                unique_filename = f"kp_{uuid.uuid4().hex}{file_extension}"
                file_path = upload_dir / unique_filename
                file_utils.save_uploaded_file(kp_file, file_path)
                
                st.session_state.uploaded_files["kp"].append({
                    "original_name": kp_file.name,
                    "file_path": str(file_path),
                    "extension": file_extension
                })
            
            # Улучшенное сообщение об успехе с перечислением файлов
            st.markdown(f"""
            <div style='background-color: #ecfdf5; padding: 10px 15px; border-radius: 6px; margin-top: 10px;'>
                <p style='margin:0; color: #065f46; font-size: 0.9rem;'>
                    ✅ Загружено {len(kp_files_uploader)} КП:
                </p>
                <ul style='margin: 5px 0 0 0; padding-left: 20px; color: #065f46; font-size: 0.85rem;'>
                    {"".join([f"<li>{file.name}</li>" for file in kp_files_uploader])}
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Дополнительная информация - с отступом сверху
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background-color: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
        <h3 style='font-size: 1.2rem; color: #1A1E3A; margin-bottom: 10px;'>📌 Дополнительная информация (опционально)</h3>
        <p style='color: #64748B; font-size: 0.9rem; margin-bottom: 15px;'>
            Загрузите дополнительные файлы (протоколы встреч, отчеты, письма) или введите текст, 
            который может быть релевантен для анализа
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    row2_cols = st.columns([3, 2])
    
    with row2_cols[0]:
        additional_files_uploader = st.file_uploader(
            "Выберите дополнительные файлы",
            type=["pdf", "docx", "txt"],
            key="additional_uploader",
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if additional_files_uploader:
            # Используем ключ "additional"
            if "additional" not in st.session_state.uploaded_files or not isinstance(st.session_state.uploaded_files["additional"], list):
                st.session_state.uploaded_files["additional"] = []
                
            for add_file in additional_files_uploader:
                file_extension = os.path.splitext(add_file.name)[1].lower()
                unique_filename = f"add_{uuid.uuid4().hex}{file_extension}"
                file_path = upload_dir / unique_filename
                file_utils.save_uploaded_file(add_file, file_path)
                
                st.session_state.uploaded_files["additional"].append({
                    "original_name": add_file.name,
                    "file_path": str(file_path),
                    "extension": file_extension
                })
            
            st.success(f"✅ Загружено дополнительных файлов: {len(additional_files_uploader)}")
    
    # Поле для ввода дополнительного текста
    with row2_cols[1]:
        # Добавляем выделенное описание для подчеркивания важности
        st.markdown("""
        <div style='background-color: #f0f9ff; padding:10px; border-radius:5px; border-left:3px solid #2E75D6; margin-bottom:10px;'>
            <strong>Дополнительная информация (опционально)</strong> - 
            <span style='color:#1A1E3A;'>эти данные имеют <u>существенный вес</u> в рейтинге и общей оценке!</span>
        </div>
        """, unsafe_allow_html=True)
        
        additional_text = st.text_area(
            "Введите информацию о предыдущем опыте, компетенциях или других важных факторах",
            height=150,
            key="additional_text_input",
            placeholder="Например: информация о предыдущем опыте поставщика, результаты проверки референсов, дополнительные требования, обсуждавшиеся вне ТЗ..."
        )
        
        if additional_text:
            text_filename = f"additional_text_{uuid.uuid4().hex}.txt"
            text_file_path = upload_dir / text_filename
            
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(additional_text)
            
            # Используем ключ "additional"
            if "additional" not in st.session_state.uploaded_files or not isinstance(st.session_state.uploaded_files["additional"], list):
                st.session_state.uploaded_files["additional"] = []
                
            # Добавляем текст как еще один "файл"
            st.session_state.uploaded_files["additional"].append({
                "original_name": "Дополнительный текст",
                "file_path": str(text_file_path),
                "extension": ".txt"
            })
            st.success("✅ Комментарий сохранен!")
    
    # Добавляем инструкцию перед кнопкой
    uploaded_tz = st.session_state.uploaded_files.get("tz") is not None
    uploaded_kp = len(st.session_state.uploaded_files.get("kp", [])) > 0
    
    # Разделитель и кнопка анализа
    st.divider()
    
    # Показываем статус загрузки файлов над кнопкой
    status_cols = st.columns([1, 1, 1])
    with status_cols[0]:
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; border-radius: 5px; background-color: {"#ecfdf5" if uploaded_tz else "#fee2e2"};'>
            <p style='margin:0; font-size: 0.9rem; color: {"#065f46" if uploaded_tz else "#b91c1c"};'>
                {'✅' if uploaded_tz else '❌'} ТЗ: {'загружено' if uploaded_tz else 'не загружено'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with status_cols[1]:
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; border-radius: 5px; background-color: {"#ecfdf5" if uploaded_kp else "#fee2e2"};'>
            <p style='margin:0; font-size: 0.9rem; color: {"#065f46" if uploaded_kp else "#b91c1c"};'>
                {'✅' if uploaded_kp else '❌'} КП: {'загружено ' + str(len(st.session_state.uploaded_files.get("kp", []))) if uploaded_kp else 'не загружено'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with status_cols[2]:
        has_additional = len(st.session_state.uploaded_files.get("additional", [])) > 0
        st.markdown(f"""
        <div style='text-align: center; padding: 8px; border-radius: 5px; background-color: {"#ecfdf5" if has_additional else "#f8fafc"};'>
            <p style='margin:0; font-size: 0.9rem; color: {"#065f46" if has_additional else "#64748b"};'>
                {'✅' if has_additional else '🔹'} Доп: {'загружено ' + str(len(st.session_state.uploaded_files.get("additional", []))) if has_additional else 'опционально'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Кнопка для запуска анализа (центрированная, более заметная)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    col1, col2, col1 = st.columns([1, 2, 1])
    
    with col2:
        # Проверяем наличие файлов по ключам
        analysis_disabled = not uploaded_tz or not uploaded_kp
        
        if analysis_disabled:
            st.info("⚠️ Для запуска анализа необходимо загрузить ТЗ и хотя бы одно КП")
        
        analyze_btn = st.button(
            "🚀 Запустить анализ всех КП",
            use_container_width=True, 
            disabled=analysis_disabled,
            type="primary"
        )
        
        if analyze_btn:
            st.session_state.run_full_analysis = True
            st.session_state.all_analysis_results = []
            st.session_state.analysis_result = None 
            st.session_state.ratings = {} 
            # st.session_state.comments = {} # comments пока не используются широко
            
            st.session_state.current_step = "analysis"
            st.rerun() 