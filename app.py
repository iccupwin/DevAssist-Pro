import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Импорт модулей приложения (будут созданы позже)
from src.components import sidebar, file_upload, analysis, report, comparison_table
from src.utils import file_utils
from src.config import settings

# --- Конфигурация страницы --- 
# Вызываем самой первой командой Streamlit!
st.set_page_config(page_title=settings.APP_TITLE, layout="wide")

# Загрузка переменных окружения (API ключей)
load_dotenv()

# Пути для загрузки и сохранения файлов
UPLOAD_DIR = Path("src/data/uploads")
RESULT_DIR = Path("src/data/results")

# Создание директорий, если они не существуют
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

# Инициализация состояния сессии
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {
        "tz_file": None,
        "kp_files": [],
        "additional_files": []
    }
    
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "all_analysis_results" not in st.session_state:
    st.session_state.all_analysis_results = []
    
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
    
if "current_step" not in st.session_state:
    st.session_state.current_step = "upload"  # Шаги: upload, analysis, report, comparison

if "run_full_analysis" not in st.session_state:
    st.session_state.run_full_analysis = False

# Добавляем выбранные модели в состояние
if "selected_model" not in st.session_state:
    # Устанавливаем модель по умолчанию для анализа КП
    default_model = settings.AVAILABLE_MODELS.get("Claude 3.7 Sonnet (Пользовательский запрос)", list(settings.AVAILABLE_MODELS.values())[0])
    st.session_state.selected_model = default_model

if "selected_comparison_model" not in st.session_state:
    # Устанавливаем модель по умолчанию для сравнения КП
    default_comparison_model = settings.AVAILABLE_MODELS.get("GPT-4.5 Preview", list(settings.AVAILABLE_MODELS.values())[0])
    st.session_state.selected_comparison_model = default_comparison_model

# Настройка корпоративной темы Devent
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {{
        /* Основная палитра Devent */
        --primary-color: {settings.BRAND_COLORS["primary"]};
        --secondary-color: {settings.BRAND_COLORS["secondary"]};
        --accent-color: {settings.BRAND_COLORS["accent"]};
        --background-color: {settings.BRAND_COLORS["background"]};
        --text-color: {settings.BRAND_COLORS["text"]};
        --light-text: {settings.BRAND_COLORS["light_text"]};
        
        /* Функциональные цвета */
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --danger-color: #EF4444;
        --info-color: #3B82F6;
        
        /* Размеры */
        --border-radius: 8px;
        --small-radius: 6px;
    }}
    
    /* Основные стили */
    .stApp {{
        background-color: var(--background-color);
        color: var(--text-color);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        letter-spacing: -0.011em;
    }}
    
    /* Стили для sidebar */
    section[data-testid="stSidebar"] {{
        background-color: white;
        border-right: 1px solid rgba(0,0,0,0.05);
    }}
    
    /* Типография */
    h1 {{
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        color: var(--primary-color);
        margin-bottom: 1.5rem;
        letter-spacing: -0.02em;
    }}
    
    h2 {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.75rem;
        color: var(--secondary-color);
        letter-spacing: -0.02em;
        margin-top: 2rem;
    }}
    
    h3 {{
        font-family: 'Inter', sans-serif;
        font-weight: 600; 
        font-size: 1.4rem;
        color: var(--secondary-color);
        letter-spacing: -0.01em;
    }}
    
    p, li, ol, ul {{
        color: var(--text-color);
        font-size: 1rem;
        line-height: 1.6;
    }}
    
    a {{
        color: var(--primary-color);
        text-decoration: none;
    }}
    
    a:hover {{
        text-decoration: underline;
    }}
    
    /* Кнопки */
    .stButton > button {{
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button:hover {{
        background-color: #1A62C5; /* Немного темнее primary */
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-1px);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }}
    
    /* Контейнеры и карточки */
    div[data-testid="stExpander"] {{
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: var(--border-radius);
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        overflow: hidden;
        margin: 1rem 0;
    }}
    
    div[data-testid="stExpander"] > div:first-child {{
        background-color: var(--background-color);
        padding: 1rem;
        border-bottom: 1px solid rgba(0,0,0,0.05);
    }}
    
    /* Таблицы */
    .stDataFrame {{
        border: none;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 5px rgba(0,0,0,0.05);
    }}
    
    .stDataFrame thead {{
        background-color: #F8FAFD;
    }}
    
    .stDataFrame thead tr th {{
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--secondary-color);
        padding: 0.7rem 1rem;
        text-align: left;
        border-bottom: 1px solid #EDF2F7;
    }}
    
    .stDataFrame tbody tr td {{
        font-size: 0.9rem;
        color: var(--text-color);
        padding: 0.7rem 1rem;
        border-bottom: 1px solid #EDF2F7;
        text-align: left;
    }}
    
    .stDataFrame tbody tr:hover {{
        background-color: #F8FAFD;
    }}
    
    /* Загрузчик файлов */
    .stFileUploader {{
        margin-bottom: 1.5rem;
    }}
    
    .stFileUploader > div {{
        background-color: white;
        border: 2px dashed #E2E8F0;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        transition: all 0.2s;
    }}
    
    .stFileUploader > div:hover {{
        border-color: var(--primary-color);
        background-color: #F8FAFD;
    }}
    
    /* Прогресс-бары и слайдеры */
    .stProgress > div > div {{
        background-color: var(--primary-color);
        height: 6px;
        border-radius: 3px;
    }}
    
    /* Инфо-боксы */
    .stAlert {{
        border-radius: var(--border-radius);
        padding: 1rem;
        margin: 1rem 0;
    }}
    
    /* Селект-боксы */
    .stSelectbox label {{
        color: var(--secondary-color);
        font-weight: 500;
        font-size: 0.9rem;
    }}
    
    .stSelectbox > div > div > div {{
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: var(--small-radius);
        transition: all 0.2s;
    }}
    
    .stSelectbox > div > div > div:hover {{
        border-color: var(--primary-color);
    }}
    
    /* Разделители */
    hr {{
        margin: 1.5rem 0;
        border-color: rgba(0,0,0,0.05);
    }}
    
    /* Override стили для сообщений */
    div[data-testid="stSuccessAlert"] {{
        background-color: rgba(16, 185, 129, 0.1);
        border-radius: 6px;
        padding: 8px 16px;
        border-left: 4px solid #10B981;
    }}
    
    div[data-testid="stInfoAlert"] {{
        background-color: rgba(59, 130, 246, 0.1);
        border-radius: 6px;
        padding: 8px 16px;
        border-left: 4px solid #3B82F6;
    }}
    
    div[data-testid="stWarningAlert"] {{
        background-color: rgba(245, 158, 11, 0.1);
        border-radius: 6px;
        padding: 8px 16px;
        border-left: 4px solid #F59E0B;
    }}
    
    div[data-testid="stErrorAlert"] {{
        background-color: rgba(239, 68, 68, 0.1);
        border-radius: 6px;
        padding: 8px 16px;
        border-left: 4px solid #EF4444;
    }}
    
    /* Анимации */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .stApp > div:not(.stSidebar) {{
        animation: fadeIn 0.3s ease-out;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

def initialize_session_state():
    """Инициализирует состояние сессии, если оно еще не создано."""
    if "current_step" not in st.session_state:
        st.session_state.current_step = "upload" # 'upload', 'analysis', 'comparison', 'report'
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {"tz": None, "kp": [], "additional": []}
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None # Результат анализа одного выбранного КП
    if "all_analysis_results" not in st.session_state:
        st.session_state.all_analysis_results = [] # Список результатов анализа всех КП
    if "run_full_analysis" not in st.session_state:
        st.session_state.run_full_analysis = False
    # Добавляем выбранные модели в состояние
    if "selected_model" not in st.session_state:
        # Устанавливаем модель по умолчанию для анализа КП
        default_model = settings.AVAILABLE_MODELS.get("Claude 3.7 Sonnet (Пользовательский запрос)", list(settings.AVAILABLE_MODELS.values())[0])
        st.session_state.selected_model = default_model
    # Добавляем отдельную модель для сравнения КП
    if "selected_comparison_model" not in st.session_state:
        # Устанавливаем модель по умолчанию для сравнения КП
        default_comparison_model = settings.AVAILABLE_MODELS.get("GPT-4.5 Preview", list(settings.AVAILABLE_MODELS.values())[0])
        st.session_state.selected_comparison_model = default_comparison_model

def render_sidebar():
    """Отображает боковое меню в корпоративном стиле Devent."""
    with st.sidebar:
        # Стильный блок с логотипом и названием
        logo_container = st.container()
        with logo_container:
            # Проверяем наличие файлов логотипов
            if os.path.exists(settings.LOGO_WITH_NAME_PATH):
                # Используем логотип с названием бренда (без округления краев)
                st.markdown(f"""
                <div style='padding:10px 0;'>
                    <img src="data:image/png;base64,{file_utils.get_image_as_base64(settings.LOGO_WITH_NAME_PATH)}" width="240" style="border-radius:0;">
                </div>
                """, unsafe_allow_html=True)
                
                # Добавляем полное название продукта
                st.markdown(f"""
                <div style='margin-top:-5px; padding:0 5px 10px 5px;'>
                    <p style='font-size:0.9em; font-weight:500; color:{settings.BRAND_COLORS["secondary"]}; line-height:1.3;'>
                    Интеллектуальная система анализа тендерных предложений
                    </p>
                </div>
                """, unsafe_allow_html=True)
            elif os.path.exists(settings.LOGO_PATH):
                # Если есть только логотип без названия - отображаем его без округления краев
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"""
                    <div>
                        <img src="data:image/png;base64,{file_utils.get_image_as_base64(settings.LOGO_PATH)}" width="80" style="border-radius:0;">
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style='padding-left:5px;'>
                        <h2 style='margin:5px 0 0 0; padding:0; color:{settings.BRAND_COLORS["primary"]}; font-size:1.5em;'>Devent</h2>
                        <p style='margin:0; padding:0; font-size:0.9em; color:{settings.BRAND_COLORS["light_text"]};'>Tender Analysis AI</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Добавляем полное название под логотипом (более компактное)
                st.markdown(f"""
                <div style='margin-top:5px; padding:0 5px 10px 5px;'>
                    <p style='font-size:0.9em; font-weight:500; color:{settings.BRAND_COLORS["secondary"]}; line-height:1.2;'>
                    Интеллектуальная система анализа тендерных предложений
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Если логотипов нет - просто текст в стиле бренда (более компактный)
                st.markdown(f"""
                <div style='text-align:center; padding:10px 0;'>
                    <h2 style='margin:0; color:{settings.BRAND_COLORS["primary"]};'>Devent</h2>
                    <p style='margin:3px 0 10px 0; font-size:1.2em; color:{settings.BRAND_COLORS["secondary"]};'>Tender Analysis AI</p>
                    <p style='font-size:0.9em; font-weight:500; color:{settings.BRAND_COLORS["text"]}; line-height:1.2;'>
                    Интеллектуальная система анализа тендерных предложений
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Добавим строчку-разделитель для улучшения визуальной структуры
        st.markdown(f"""<hr style='margin:0 0 20px 0; border-color:rgba(0,0,0,0.05);'>""", unsafe_allow_html=True)
        
        # Выбор AI моделей
        st.subheader("Настройки Анализа")
        
        # Получаем имена моделей для отображения в selectbox
        model_display_names = list(settings.AVAILABLE_MODELS.keys())
        
        # --- Первая модель: для анализа КП и сравнения с ТЗ ---
        st.markdown(f"""<p style='margin-bottom:5px; font-weight:500; color:{settings.BRAND_COLORS["secondary"]};'>Модель для анализа КП</p>""", unsafe_allow_html=True)
        current_model_id = st.session_state.selected_model
        current_model_name = next((name for name, id_val in settings.AVAILABLE_MODELS.items() if id_val == current_model_id), model_display_names[0])
        try:
            current_model_index = model_display_names.index(current_model_name)
        except ValueError:
             current_model_index = 0 # Fallback if name not found
             st.warning(f"Выбранная модель '{current_model_name}' не найдена в списке доступных. Установлена модель по умолчанию.")
             
        selected_model_name = st.selectbox(
            "Выберите AI модель для анализа:",
            options=model_display_names,
            index=current_model_index,
            key="model_selector"
        )
        
        new_model_id = settings.AVAILABLE_MODELS[selected_model_name]
        if st.session_state.selected_model != new_model_id:
            st.session_state.selected_model = new_model_id
            st.info(f"✅ Модель анализа изменена на: {selected_model_name}")
        
        # --- Вторая модель: для сравнения КП между собой ---
        st.markdown(f"""<p style='margin-bottom:5px; margin-top:15px; font-weight:500; color:{settings.BRAND_COLORS["secondary"]};'>Модель для сравнения КП</p>""", unsafe_allow_html=True)
        current_comparison_model_id = st.session_state.selected_comparison_model
        current_comparison_model_name = next((name for name, id_val in settings.AVAILABLE_MODELS.items() if id_val == current_comparison_model_id), model_display_names[0])
        try:
            current_comparison_model_index = model_display_names.index(current_comparison_model_name)
        except ValueError:
             current_comparison_model_index = 0
             
        selected_comparison_model_name = st.selectbox(
            "Выберите AI модель для сравнения:",
            options=model_display_names,
            index=current_comparison_model_index,
            key="comparison_model_selector"
        )
        
        new_comparison_model_id = settings.AVAILABLE_MODELS[selected_comparison_model_name]
        if st.session_state.selected_comparison_model != new_comparison_model_id:
            st.session_state.selected_comparison_model = new_comparison_model_id
            st.info(f"✅ Модель сравнения изменена на: {selected_comparison_model_name}")
        
        st.divider()
        
        # Блок навигации
        st.markdown(f"""<p style='font-weight:500; color:{settings.BRAND_COLORS["secondary"]};'>Навигация</p>""", unsafe_allow_html=True)
        
        # Стилизуем кнопки навигации
        upload_btn = st.button(
            "🏠 Загрузка файлов", 
            key="nav_upload", 
            use_container_width=True,
            help="Вернуться к загрузке файлов"
        )
        if upload_btn:
            st.session_state.current_step = "upload"
            st.rerun()
            
        compare_btn = st.button(
            "📊 Сравнение КП", 
            key="nav_compare", 
            use_container_width=True,
            disabled=not st.session_state.all_analysis_results,
            help="Перейти к сравнительной таблице КП"
        )
        if compare_btn:
            st.session_state.current_step = "comparison"
            st.session_state.analysis_result = None
            st.rerun()

        # Добавим информацию о версии приложения
        st.markdown(f"""
        <div style='position:fixed; bottom:20px; left:20px; right:20px; text-align:center;'>
            <div style='background-color:white; padding:10px; border-radius:5px; box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
                <p style='font-size:0.75em; margin:0; color:{settings.BRAND_COLORS["light_text"]};'>{settings.SIDEBAR_FOOTER}</p>
                <p style='font-size:0.7em; margin:2px 0 0 0; color:{settings.BRAND_COLORS["light_text"]};'>v1.0.0</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_header():
    """Отображает шапку с логотипом и названием проекта в профессиональном стиле."""
    # Создаем контейнер для шапки
    header_container = st.container()
    
    with header_container:
        # Версия для мобильных (при скрытой боковой панели)
        small_header = st.columns([1, 5])
        with small_header[0]:
            if os.path.exists(settings.LOGO_PATH):
                st.image(settings.LOGO_PATH, width=50)
        with small_header[1]:
            st.markdown(f"""
            <h1 style='font-size:1.5rem; margin-bottom:0.5rem; color:{settings.BRAND_COLORS["primary"]};'>
                Devent Tender Analysis AI
            </h1>
            """, unsafe_allow_html=True)
    
    # Тонкая линия-разделитель под шапкой
    st.markdown(f"""<hr style='margin:0 0 1.5rem 0; opacity:0.2;'>""", unsafe_allow_html=True)

def main():
    """Основная функция приложения."""
    
    initialize_session_state()
    render_sidebar()
    
    # Проверки API ключей, после инициализации и sidebar
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("API ключ OpenAI не найден в переменных окружения (OPENAI_API_KEY). Некоторые модели могут быть недоступны.")
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("API ключ Anthropic не найден в переменных окружения (ANTHROPIC_API_KEY). Некоторые модели могут быть недоступны.")
    
    # Добавляем шапку для основного контента
    render_header()
    
    # --- Основное содержимое страницы --- 
    main_container = st.container()
    with main_container:
        if st.session_state.current_step == "upload":
            file_upload.render_upload_section()
        elif st.session_state.current_step == "analysis":
            analysis.render_analysis_section()
        elif st.session_state.current_step == "comparison":
            comparison_table.render_comparison_table()
        elif st.session_state.current_step == "report":
            report.render_report_section(RESULT_DIR)
        else:
            st.error("Неизвестный шаг приложения.")
            st.session_state.current_step = "upload"
            st.rerun()

if __name__ == "__main__":
    main() 