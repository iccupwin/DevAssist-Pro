import streamlit as st
import os
from src.config import settings

def render_sidebar():
    """Отображает боковую панель с навигацией и информацией о приложении"""
    
    with st.sidebar:
        st.title("Навигация")
        
        # Логотип или изображение (опционально)
        st.image("https://via.placeholder.com/150x150.png?text=Tender+AI", width=150)
        
        # Навигационные кнопки
        st.subheader("Этапы анализа")
        
        if st.button("1. Загрузка документов", 
                    use_container_width=True,
                    disabled=st.session_state.current_step == "upload"):
            st.session_state.current_step = "upload"
            st.rerun()
            
        analysis_disabled = st.session_state.uploaded_files["tz_file"] is None or not st.session_state.uploaded_files["kp_files"]
        if st.button("2. Анализ и оценка", 
                    use_container_width=True,
                    disabled=analysis_disabled or st.session_state.current_step == "analysis"):
            st.session_state.current_step = "analysis"
            st.rerun()
            
        report_disabled = st.session_state.analysis_result is None
        if st.button("3. Итоговый отчет", 
                    use_container_width=True,
                    disabled=report_disabled or st.session_state.current_step == "report"):
            st.session_state.current_step = "report"
            st.rerun()
        
        # Кнопка для перехода к сравнительной таблице всех КП
        comparison_disabled = "all_analysis_results" not in st.session_state or not st.session_state.all_analysis_results
        if st.button("4. Сравнение всех КП", 
                    use_container_width=True,
                    disabled=comparison_disabled or st.session_state.current_step == "comparison"):
            st.session_state.current_step = "comparison"
            st.rerun()
        
        # Индикатор статуса API ключей
        st.subheader("Статус API ключей")
        
        anthropic_key = settings.ANTHROPIC_API_KEY is not None
        openai_key = settings.OPENAI_API_KEY is not None
        
        st.markdown(f"Claude API: {'✅' if anthropic_key else '❌'}")
        st.markdown(f"GPT-4o API: {'✅' if openai_key else '❌'}")
        
        if not anthropic_key or not openai_key:
            st.warning("Для полной функциональности необходимо добавить API ключи в файл .env")
            
        # Информация о проекте
        st.divider()
        st.markdown("### О проекте")
        st.markdown("""
        Система автоматизированного анализа 
        и сравнения коммерческих предложений 
        с техническим заданием тендера
        """)
        
        # Версия
        st.caption("v1.0.0") 