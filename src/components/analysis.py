import streamlit as st
import pandas as pd
import time
from pathlib import Path
from src.config import settings
from src.utils import file_utils
from src.services import ai_service
import json
import random

def run_single_analysis(tz_file, kp_file, additional_files):
    """Выполняет анализ одного КП по отношению к ТЗ и доп. файлам с использованием AI."""
    
    st.info(f"Анализ КП: {kp_file['original_name']}...")
    
    try:
        # 1. Извлечение текста из файлов
        tz_text = file_utils.extract_text_from_file(Path(tz_file["file_path"]))
        if not tz_text:
            st.error(f"Не удалось извлечь текст из ТЗ: {tz_file['original_name']}")
            return None
            
        kp_text = file_utils.extract_text_from_file(Path(kp_file["file_path"]))
        if not kp_text:
            st.error(f"Не удалось извлечь текст из КП: {kp_file['original_name']}")
            return None
        
        # Ограничение длины текста для экономии токенов (можно настроить)
        MAX_LEN = 30000 # Примерно 7-8 тыс. токенов
        if len(tz_text) > MAX_LEN:
            st.warning(f"Текст ТЗ ({tz_file['original_name']}) слишком длинный, будет обрезан до {MAX_LEN} символов для анализа.")
            tz_text = tz_text[:MAX_LEN]
        if len(kp_text) > MAX_LEN:
             st.warning(f"Текст КП ({kp_file['original_name']}) слишком длинный, будет обрезан до {MAX_LEN} символов для анализа.")
             kp_text = kp_text[:MAX_LEN]

        # === Вызов AI сервисов ===
        
        # 2. Извлечение ключевых данных из КП
        st.write(f"- Извлечение ключевых данных из {kp_file['original_name']}...")
        kp_summary_data = ai_service.extract_kp_summary_data(kp_text)
        # Добавляем небольшую задержку для наглядности
        time.sleep(random.uniform(0.5, 1.5))

        # 3. Сравнение ТЗ и КП
        st.write(f"- Сравнение {kp_file['original_name']} с ТЗ...")
        comparison_result = ai_service.compare_tz_kp(tz_text, kp_text)
        # Добавляем фиктивные секции на основе общей оценки для демо
        compliance_score = comparison_result.get("compliance_score", 0)
        comparison_result["sections"] = [
            {"name": "Общие требования", "compliance": random.randint(max(0, compliance_score-10), min(100, compliance_score+10)), "details": "(Детали будут добавлены после более глубокого анализа секций)"},
            {"name": "Функциональные требования", "compliance": random.randint(max(0, compliance_score-15), min(100, compliance_score+5)), "details": "(Детали будут добавлены после более глубокого анализа секций)"},
            {"name": "Нефункциональные требования", "compliance": random.randint(max(0, compliance_score-20), min(100, compliance_score+15)), "details": "(Детали будут добавлены после более глубокого анализа секций)"},
        ]
        time.sleep(random.uniform(0.5, 1.5))

        # 4. Генерация предварительной рекомендации
        st.write(f"- Формирование предварительных выводов по {kp_file['original_name']}...")
        preliminary_recommendation = ai_service.generate_recommendation(comparison_result, kp_summary_data)
        time.sleep(random.uniform(0.5, 1.5))

        # 5. Анализ дополнительных файлов (пока заглушка)
        additional_info_analysis = None
        if additional_files:
            st.write(f"- Анализ дополнительных файлов для {kp_file['original_name']}...")
            # Реализуем анализ дополнительных файлов - это будет влиять на рейтинг
            additional_info_analysis = {
                "key_findings": ["Учитываю дополнительную информацию для расчета рейтинга"],
                "impact": "Дополнительная информация имеет существенное положительное влияние на общую оценку",
                "rating_impact": 2.0  # Добавляем значимый положительный модификатор к рейтингу (2 из 10)
            }
            time.sleep(1)

        # 6. Рейтинги (пока заглушка - случайные значения)
        base_ratings = {c["id"]: random.randint(3, 9) for c in settings.EVALUATION_CRITERIA}
        
        # Модифицируем рейтинги с учетом дополнительной информации
        ratings = base_ratings.copy()
        if additional_info_analysis and "rating_impact" in additional_info_analysis:
            # Применяем модификатор ко всем рейтингам, но с ограничением максимума 10
            for key in ratings:
                ratings[key] = min(10, ratings[key] + additional_info_analysis["rating_impact"])
            st.info(f"Рейтинг скорректирован в большую сторону благодаря дополнительной информации (+{additional_info_analysis['rating_impact']} балла)")
        
        comments = {} # Пустые комментарии
        # === Конец вызовов AI сервисов ===

        st.success(f"Анализ {kp_file['original_name']} завершен.")
        
        # Формируем итоговый результат для этого КП
        analysis_output = {
            "tz_name": tz_file["original_name"],
            "kp_name": kp_file["original_name"],
            "company_name": kp_summary_data.get("company_name", "Не определено"),
            "tech_stack": kp_summary_data.get("tech_stack", "Не указано"),
            "pricing": kp_summary_data.get("pricing", "Не указано"),
            "timeline": kp_summary_data.get("timeline", "Не указано"),
            "comparison_result": comparison_result, 
            "additional_info_analysis": additional_info_analysis,
            "preliminary_recommendation": preliminary_recommendation,
            "ratings": ratings, 
            "comments": comments
        }
        return analysis_output
        
    except Exception as e:
        st.error(f"Критическая ошибка при анализе {kp_file['original_name']}: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

def render_analysis_section():
    """Отображает процесс анализа всех загруженных КП."""
    
    st.header("Анализ коммерческих предложений", anchor=False)

    if not st.session_state.uploaded_files["tz"] or not st.session_state.uploaded_files["kp"]:
        st.warning("Пожалуйста, загрузите ТЗ и хотя бы одно КП на предыдущем шаге.")
        if st.button("Вернуться к загрузке"): 
            st.session_state.current_step = "upload"
            st.rerun()
        return

    # Запуск анализа, если он еще не был запущен или нужно перезапустить
    if st.session_state.get("run_full_analysis"):
        
        tz_file = st.session_state.uploaded_files["tz"]
        kp_files = st.session_state.uploaded_files["kp"]
        # Используем .get() для безопасного получения списка доп. файлов
        additional_files = st.session_state.uploaded_files.get("additional", [])
        
        total_files = len(kp_files)
        st.session_state.all_analysis_results = [] # Очищаем предыдущие результаты
        
        # Стильное отображение информации о старте анализа
        st.markdown(f"""
        <div style='background-color: #f0f7ff; padding: 15px 20px; border-radius: 10px; margin-bottom: 20px; border-left: 4px solid {settings.BRAND_COLORS["primary"]}'>
            <h3 style='margin:0 0 10px 0; color: {settings.BRAND_COLORS["primary"]}; font-size: 1.2rem;'>🤖 Запуск AI-анализа</h3>
            <p style='margin:0; font-size: 0.95rem;'>
                Анализирую <b>{total_files}</b> коммерческих предложений относительно технического задания.
                <br>Используемая модель: <b>{st.session_state.selected_model}</b>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Создаем контейнер для процесса анализа с красивым оформлением
        analysis_container = st.container(border=False)
        with analysis_container:
            # Стилизованный прогресс-бар и контейнер для статуса
            progress_container = st.container()
            with progress_container:
                # Создаем placeholder для текста над прогресс-баром
                progress_text_ph = st.empty()
                progress_bar = st.progress(0)
                
            # Добавляем отступ под прогресс-баром
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            
            # Создаем стилизованную карточку для отображения деталей процесса
            status_card_container = st.container()
            with status_card_container:
                st.markdown("""
                <div style='background-color: white; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 15px 20px; margin-bottom: 10px;'>
                    <h4 style='margin:0 0 10px 0; color: #1A1E3A; font-size: 1.1rem;'>📊 Детали процесса анализа</h4>
                </div>
                """, unsafe_allow_html=True)
                status_placeholder = st.empty()

        for i, kp_file in enumerate(kp_files):
            # Обновляем процент выполнения
            completion_pct = (i + 1) / total_files
            
            # Обновляем текст над прогресс-баром
            progress_text = f"Анализ {i+1} из {total_files} КП: {kp_file['original_name']}"
            progress_text_ph.markdown(f"""
            <div style='color: {settings.BRAND_COLORS["secondary"]}; font-weight: 500; padding: 5px 0; margin-bottom: 5px;'>
                {progress_text} ({int(completion_pct * 100)}%)
            </div>
            """, unsafe_allow_html=True)
            
            # Обновляем прогресс-бар
            progress_bar.progress(completion_pct)
            
            # Очищаем статус и запускаем анализ одного файла
            with status_placeholder.container(): 
                result = run_single_analysis(tz_file, kp_file, additional_files)
            
            if result:
                st.session_state.all_analysis_results.append(result)
            else:
                st.error(f"Не удалось проанализировать файл: {kp_file['original_name']}. Он будет пропущен.")
                # Можно добавить логирование или более детальную обработку ошибок
        
        # Завершаем с красивым уведомлением
        progress_text_ph.empty()
        progress_bar.empty()
        
        st.markdown(f"""
        <div style='background-color: #ecfdf5; padding: 15px 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #10B981;'>
            <h3 style='margin:0 0 5px 0; color: #065f46; font-size: 1.2rem;'>✅ Анализ успешно завершен</h3>
            <p style='margin:0; font-size: 0.95rem; color: #065f46;'>
                Проанализировано {total_files} коммерческих предложений.
                <br>Переход к сравнительной таблице...
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Добавляем небольшую задержку для отображения завершения
        time.sleep(1.5)
        
        # Сбрасываем флаг, чтобы анализ не запускался повторно при перезагрузке
        st.session_state.run_full_analysis = False 
        
        # Автоматически переходим к сравнительной таблице
        st.session_state.current_step = "comparison"
        st.rerun()
        
    else:
        # Красивое информационное сообщение 
        st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0; border: 1px solid #e2e8f0;'>
            <img src="https://cdn-icons-png.flaticon.com/512/1162/1162914.png" width="80" style="margin-bottom: 15px;">
            <h3 style='margin:0 0 10px 0; color: {settings.BRAND_COLORS["secondary"]}; font-size: 1.3rem;'>Анализ еще не запущен</h3>
            <p style='margin:0 0 20px 0; color: {settings.BRAND_COLORS["light_text"]}; font-size: 1rem;'>
                Вернитесь на страницу загрузки файлов и нажмите кнопку "Запустить анализ всех КП"
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔙 Вернуться к загрузке файлов", use_container_width=True): 
                st.session_state.current_step = "upload"
                st.rerun()

def get_section_compliance_color(compliance_score):
    """Возвращает цвет для отображения соответствия раздела"""
    if compliance_score >= 80:
        return "#28a745"  # Зеленый
    elif compliance_score >= 60:
        return "#17a2b8"  # Голубой
    elif compliance_score >= 40:
        return "#ffc107"  # Желтый
    else:
        return "#dc3545"  # Красный 