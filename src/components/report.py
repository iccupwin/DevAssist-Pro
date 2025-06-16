import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import re
import os
import plotly.graph_objects as go
import plotly.express as px
import base64
from io import BytesIO
import time
from src.config import settings
from src.components import comparison_table

def render_report_section(result_dir):
    """Отображает секцию с отчетом по выбранному КП или сравнительную таблицу."""
    
    # Определяем, показывать отчет по одному КП или сравнительную таблицу
    if "analysis_result" in st.session_state and st.session_state.analysis_result is not None:
        # Если выбран конкретный анализ, показываем его отчет
        render_single_report_new_structure()
    elif "all_analysis_results" in st.session_state and st.session_state.all_analysis_results:
        # Если не выбран конкретный, но есть общие результаты, показываем сравнение
        st.session_state.current_step = "comparison" # Убедимся, что мы на правильном шаге
        st.rerun() # Перезапустим, чтобы app.py отрисовал comparison_table
    else:
        # Если нет никаких данных для отчета или сравнения
        st.error("Ошибка: Нет данных для отображения отчета. Пожалуйста, сначала загрузите и проанализируйте файлы.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Вернуться к загрузке файлов", use_container_width=True, key="report_back_to_upload"):
                st.session_state.current_step = "upload"
                st.rerun()
        return

def render_single_report_new_structure():
    """Отображает отчет по одному КП согласно новой 11-пунктовой структуре."""
    
    analysis_data = st.session_state.analysis_result
    kp_name = analysis_data["kp_name"]
    company_name = analysis_data.get("company_name", kp_name)  # Используем название компании, если есть
    tz_name = analysis_data["tz_name"]
    comparison_result = analysis_data["comparison_result"]
    prelim_recommendation = analysis_data["preliminary_recommendation"]
    ratings = analysis_data.get("ratings", {})
    
    # Получаем дополнительные данные (технологии, сроки, стоимость)
    tech_stack = analysis_data.get("tech_stack", "Не указано")
    pricing = analysis_data.get("pricing", "Не указано")
    timeline = analysis_data.get("timeline", "Не указано")
    
    st.title(f"Анализ Коммерческого Предложения: {company_name}")
    st.markdown(f"*по отношению к ТЗ: {tz_name}*")
    st.divider()
    
    # Добавляем кнопки для экспорта в PDF
    export_cols = st.columns([2, 2, 2])
    with export_cols[1]:
        if st.button("📄 Сохранить отчет в PDF", use_container_width=True, key="export_pdf_report"):
            generate_pdf_report_placeholder(company_name)
            
    # --- 1. Резюме / Ключевые Выводы (Executive Summary) --- 
    st.markdown("## 1. Резюме / Ключевые Выводы")
    with st.container(border=True):
        st.markdown(f"**Цель:** Оценка КП компании '{company_name}' на соответствие ТЗ '{tz_name}'.")
        
        compliance_score = comparison_result["compliance_score"]
        if compliance_score >= 80:
            compliance_text = "Высокая степень соответствия"
        elif compliance_score >= 60:
            compliance_text = "Средняя степень соответствия, требует уточнений"
        else:
            compliance_text = "Значительные расхождения с требованиями ТЗ"
        st.markdown(f"**Общая Оценка Соответствия:** {compliance_text} ({compliance_score}%) ✨")

        # Ключевые моменты (берем первые N из анализа)
        st.markdown("**Ключевые Положительные Моменты:**")
        if prelim_recommendation["strength"]:
            for i, strength in enumerate(prelim_recommendation["strength"][:3]): # Показываем до 3
                st.markdown(f"  - {strength}")
        else:
            st.markdown("  - *Не выявлено*")
        
        st.markdown("**Ключевые Проблемы / Расхождения:**")
        if prelim_recommendation["weakness"]:
            for i, weakness in enumerate(prelim_recommendation["weakness"][:3]): # Показываем до 3
                st.markdown(f"  - {weakness}")
        else:
             st.markdown("  - *Не выявлено*")
        
        # Финансовый итог
        st.markdown(f"**Финансовый Итог:** {pricing} 💰")

        # Итоговая рекомендация
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        overall_score = (avg_rating * 10 + compliance_score) / 2
        
        if overall_score >= 75:
            recommendation_final = "✅ Рекомендовать к принятию"
        elif overall_score >= 60:
            recommendation_final = "⚠️ Рекомендовать к доработке/переговорам"
        else:
            recommendation_final = "❌ Рекомендовать к отклонению"
        st.markdown(f"**Итоговая Рекомендация:** {recommendation_final}")
        
    # --- 2. Вводная Информация --- 
    st.markdown("## 2. Вводная информация")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Анализируемые Документы:**")
            st.markdown(f"  - **ТЗ:** {tz_name} (Версия/дата не указаны)") # Добавить, если есть
            st.markdown(f"  - **КП:** от {company_name} (Версия/дата не указаны)") # Используем название компании
        with col2:
             st.markdown(f"**Поставщик:** {company_name}")
             st.markdown("**Контекст:** Оценка КП для выбора исполнителя по ТЗ.")
             st.markdown(f"**Дата Анализа:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    # --- 3. Обзор Коммерческого Предложения (КП) --- 
    st.markdown("## 3. Обзор Коммерческого Предложения (КП)")
    with st.container(border=True):
        # Используем извлеченные данные
        st.markdown("**Заявленный Объем Работ:**")
        st.markdown(f"  - Предложение включает разработку и внедрение системы согласно ТЗ.")
        
        st.markdown("**Предложенное Решение/Технологии:**")
        st.markdown(f"  - **Технологический стек:** {tech_stack}")
        
        st.markdown("**Заявленная Стоимость:**")
        st.markdown(f"  - **Стоимость:** {pricing}")

        st.markdown("**Заявленные Сроки:**")
        st.markdown(f"  - **График работ:** {timeline}")
        
        st.markdown("**Основные Допущения и Ограничения КП:**")
        st.markdown("  - Заказчик предоставляет необходимую инфраструктуру и доступы.")
        st.markdown("  - Изменения в ТЗ в процессе разработки могут повлиять на сроки и стоимость.")

    # --- 4. Детальное Построчное Сравнение ТЗ и КП --- 
    st.markdown("## 4. Детальное Построчное Сравнение ТЗ и КП")
    # Этот раздел требует детального анализа и сопоставления пунктов ТЗ и КП (сложная задача для AI)
    st.markdown("_Этот раздел требует более глубокого AI-анализа для автоматического сопоставления пунктов ТЗ и КП. Текущая версия предоставляет общую оценку соответствия._")
    
    # Отображаем таблицу соответствия по разделам (как временное решение)
    st.markdown("### Соответствие по основным разделам (упрощенно)")
    sections_data = []
    if "sections" in comparison_result:
        for section in comparison_result["sections"]:
            sections_data.append({
                "Раздел": section["name"],
                "Соответствие (%)": section["compliance"],
                "Комментарий": section["details"]
            })
        sections_df = pd.DataFrame(sections_data)
        st.dataframe(
            sections_df,
            column_config={
                "Раздел": st.column_config.TextColumn("Раздел ТЗ/КП"),
                "Соответствие (%)": st.column_config.ProgressColumn(
                    "Оценка Соответствия", format="%d%%", min_value=0, max_value=100
                ),
                "Комментарий": st.column_config.TextColumn("Комментарий Аналитика")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Данные о соответствии по разделам отсутствуют.")

    # --- 5. Анализ Полноты Охвата и Соответствия Объема Работ --- 
    st.markdown("## 5. Анализ Полноты Охвата и Соответствия Объема Работ")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Непокрытые Требования ТЗ:**")
            if comparison_result["missing_requirements"]:
                for req in comparison_result["missing_requirements"]:
                    st.markdown(f"  - 🔴 {req}")
            else:
                st.markdown("  - *Не выявлено*")
        with col2:
            st.markdown("**Избыточные Предложения КП:**")
            if comparison_result["additional_features"]:
                for feature in comparison_result["additional_features"]:
                    st.markdown(f"  - 🟢 {feature}")
            else:
                st.markdown("  - *Не выявлено*")
        st.divider()
        st.markdown(f"**Общая Оценка:** Предложенный объем работ соответствует запрошенному на {compliance_score}%. Выявлены {len(comparison_result['missing_requirements'])} непокрытых и {len(comparison_result['additional_features'])} избыточных пункта.")

    # --- 6. Финансовый Анализ (Детальный Разбор Цены) --- 
    st.markdown("## 6. Финансовый Анализ")
    with st.container(border=True):
        # Используем данные о цене
        st.markdown(f"**Структура Цены:** {pricing}")
        
        # Анализируем модель ценообразования
        if "Фиксированная цена" in pricing:
            st.markdown("**Тип ценовой модели:** 📌 Фиксированная цена (Fixed Price)")
            st.markdown("**Преимущества:** Предсказуемость затрат, четкие обязательства со стороны поставщика.")
            st.markdown("**Недостатки:** Меньшая гибкость при изменении требований, возможна избыточная оценка рисков исполнителем.")
        elif "T&M" in pricing:
            st.markdown("**Тип ценовой модели:** ⏱️ Time & Materials (T&M)")
            st.markdown("**Преимущества:** Гибкость при изменении требований, прозрачность затрат.")
            st.markdown("**Недостатки:** Менее предсказуемые затраты, требует более тщательного контроля со стороны заказчика.")
        elif "Смешанная" in pricing:
            st.markdown("**Тип ценовой модели:** 🔄 Смешанная модель")
            st.markdown("**Преимущества:** Баланс между предсказуемостью и гибкостью, распределение рисков.")
            st.markdown("**Недостатки:** Может быть сложнее в администрировании, требует четкого определения границ.")
        
        # Извлекаем стоимость для сравнения с рынком
        import re
        price_match = re.search(r'([0-9,]+,?[0-9]*)', pricing)
        if price_match:
            price_str = price_match.group(1)
            price_value = float(price_str.replace(',', ''))
            
            # Примерное сравнение с рыночными ценами (заглушка)
            if price_value > 5000000:
                market_position = "выше среднерыночной"
            elif price_value > 4000000:
                market_position = "в пределах среднерыночной"
            else:
                market_position = "ниже среднерыночной"
                
            st.markdown(f"**Сравнение с рынком:** Предложенная стоимость **{market_position}** для проектов подобного масштаба и сложности.")
        
        st.markdown("**Потенциальные скрытые или дополнительные расходы:**")
        st.markdown("  - Возможные затраты на масштабирование и поддержку")
        st.markdown("  - Затраты на дополнительные интеграции")
        st.markdown("  - Возможные переработки при изменении требований")

    # --- 7. Анализ Рисков и Угроз --- 
    st.markdown("## 7. Анализ Рисков и Угроз")
    with st.container(border=True):
        # Требуется более глубокий анализ
        st.markdown("Этот раздел требует более глубокого анализа КП и ТЗ.")
        st.markdown("Временный вариант: Определяется на основе расхождений с ТЗ.")

    # --- Дополнительная информация, если есть ---
    if "additional_info_analysis" in analysis_data and analysis_data["additional_info_analysis"]:
        render_additional_info_section(analysis_data["additional_info_analysis"])

    # --- 8. Оценка Предложенного Решения и Подхода (Технический Анализ) --- 
    st.markdown("## 8. Оценка Предложенного Решения и Подхода")
    with st.container(border=True):
        # Требует анализа КП
        st.markdown("**Технологии, Архитектура, Методология:** _(Требуется анализ КП)_ ")
        st.markdown("**Масштабируемость, Надежность, Безопасность:** _(Требуется анализ КП)_ ")

    # --- 9. Оценка Поставщика --- 
    st.markdown("## 9. Оценка Поставщика")
    with st.container(border=True):
        # Требует анализа КП и/или внешних данных
        st.markdown("**Понимание Задачи:** _(Оценивается по качеству КП)_ ")
        st.markdown("**Качество Подготовки КП:** _(Оценивается по структуре, ясности, полноте)_ ")
        st.markdown("**Релевантный Опыт:** _(Требуется анализ КП или внешних источников)_ ")

    # --- 10. Сводный Анализ Рисков --- 
    st.markdown("## 10. Сводный Анализ Рисков")
    with st.container(border=True):
        # Требуется агрегация рисков из предыдущих пунктов
        st.markdown("**Основные Выявленные Риски:**")
        st.markdown("  - Технические: _(Пример: риск совместимости...)_ ")
        st.markdown("  - Финансовые: _(Пример: риск превышения бюджета...)_ ")
        st.markdown("  - Временные: _(Пример: риск срыва сроков этапа X...)_ ")
        st.markdown("  - Организационные: _(Пример: риск недостаточной вовлеченности заказчика...)_ ")
        st.markdown("**Оценка Ключевых Рисков:** _(Требуется детальный анализ)_ ")

    # Рассчитываем общую оценку
    avg_rating = sum(ratings.values()) / len(ratings)
    compliance = comparison_result["compliance_score"]
    overall_score = (avg_rating * 10 + compliance) / 2  # Шкала 0-100
    
    # Определяем наличие дополнительной информации
    has_additional_info = analysis_data.get("additional_info_analysis") is not None
    additional_info_modifier = analysis_data.get("additional_info_analysis", {}).get("rating_impact", 0)
    
    # Добавляем информационную карточку если есть дополнительная информация
    if has_additional_info and additional_info_modifier > 0:
        st.markdown(f"""
        <div style="padding: 10px 15px; background-color: #f0f9ff; border-radius: 5px; margin: 15px 0; border-left: 4px solid #3b82f6;">
            <p style="margin:0; font-weight:500;">
                ⭐ Рейтинг этого предложения увеличен на <strong>{additional_info_modifier}</strong> балла 
                благодаря учету дополнительной информации!
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- 11. Заключение и Рекомендации (Итог) --- 
    st.markdown("## 11. Заключение и Рекомендации")
    with st.container(border=True):
        st.markdown("**Итоговая Оценка КП:**")
        st.markdown(f"  - Предложение от '{company_name}' демонстрирует {compliance_text.lower()} ({compliance_score}%) с ТЗ '{tz_name}'.")
        st.markdown("  - **Сильные стороны:** " + ", ".join(prelim_recommendation["strength"])
                      if prelim_recommendation["strength"] else "*Не выявлено*")
        st.markdown("  - **Слабые стороны:** " + ", ".join(prelim_recommendation["weakness"])
                      if prelim_recommendation["weakness"] else "*Не выявлено*")
                      
        st.markdown("**Список Критических Вопросов / Пунктов для Переговоров:**")
        critical_points = prelim_recommendation["weakness"] + comparison_result["missing_requirements"]
        if critical_points:
             for i, point in enumerate(critical_points[:5]): # Показываем до 5
                 st.markdown(f"  {i+1}. {point}")
        else:
            st.markdown("  - *Критических вопросов не выявлено*")

        # Финальная рекомендация (повтор из резюме)
        st.markdown(f"**Четкая Рекомендация:**")
        st.markdown(f"### {recommendation_final}")

        st.markdown("**Предлагаемые Следующие Шаги:**")
        # Шаги зависят от рекомендации
        if "Принять" in recommendation_final:
            st.markdown("  - Начать подготовку договора.")
            st.markdown("  - Согласовать финальный план работ.")
        elif "Доработать" in recommendation_final or "Переговоры" in recommendation_final:
            st.markdown("  - Запросить у поставщика разъяснения по критическим вопросам.")
            st.markdown("  - Провести встречу для обсуждения цены/сроков/условий.")
        else: # Отклонить
            st.markdown("  - Уведомить поставщика об отклонении предложения.")
            st.markdown("  - Рассмотреть альтернативные предложения (если есть). ")
            
    # --- 12. Сравнительная таблица (новый раздел) ---
    if "all_analysis_results" in st.session_state and len(st.session_state.all_analysis_results) > 1:
        st.markdown("## 12. Сравнительный анализ предложений")
        
        with st.container(border=True):
            st.markdown("### Сравнительная таблица КП")
            
            # Создаем данные для более компактной таблицы
            table_data = []
            
            for analysis in st.session_state.all_analysis_results:
                kp_name = analysis["kp_name"]
                comp_name = analysis.get("company_name", kp_name)
                
                is_current = comp_name == company_name
                
                # Сокращаем формат данных для более компактного отображения, обеспечивая перенос текста
                kp_info = {
                    "Название": comp_name + (" ★" if is_current else ""),
                    "Соотв.": f"{analysis['comparison_result']['compliance_score']}%",
                    "Цена": analysis.get("pricing", "—").split(':')[-1].strip() if ":" in analysis.get("pricing", "—") else analysis.get("pricing", "—"),
                    "Сроки": analysis.get("timeline", "—").split(':')[-1].strip() if ":" in analysis.get("timeline", "—") else analysis.get("timeline", "—"),
                    "Рейтинг": f"{round(sum(analysis.get('ratings', {}).values()) / len(analysis.get('ratings', {1: 0})), 1)}/10" if analysis.get('ratings') else "—",
                }
                
                # Добавляем с выделением текущего КП
                if is_current:
                    # Отмечаем текущее КП для стилизации
                    kp_info["_current"] = True
                
                table_data.append(kp_info)
            
            # Создаем DataFrame для таблицы
            comparison_df = pd.DataFrame(table_data)
            
            # Отображаем таблицу
            st.markdown("Ниже представлена сравнительная таблица всех проанализированных коммерческих предложений, включая текущее (отмечено звездочкой ★):")
            st.dataframe(
                comparison_df,
                column_config={
                    "Название": st.column_config.TextColumn("Компания", width="medium"),
                    "Соотв.": st.column_config.TextColumn("Соотв. ТЗ", width="small"),
                    "Цена": st.column_config.TextColumn("Стоимость", width="medium"),
                    "Сроки": st.column_config.TextColumn("Сроки", width="medium"),
                    "Рейтинг": st.column_config.TextColumn("Рейтинг", width="small"),
                },
                hide_index=True,
                use_container_width=True,
                column_order=["Название", "Соотв.", "Цена", "Сроки", "Рейтинг"],
                height=220 if len(table_data) > 4 else 180,  # Адаптивная высота
            )
            
            st.markdown("### Выводы сравнительного анализа")
            st.markdown("При сравнении с другими предложениями, данное КП:")
            
            # Определяем позицию текущего КП среди других
            current_compliance = comparison_result["compliance_score"]
            all_compliances = [a["comparison_result"]["compliance_score"] for a in st.session_state.all_analysis_results]
            sorted_compliances = sorted(all_compliances, reverse=True)
            position = sorted_compliances.index(current_compliance) + 1
            total = len(all_compliances)
            
            # Формируем сравнительный текст
            if position == 1:
                st.markdown(f"- Имеет **наилучшую степень соответствия** ТЗ ({current_compliance}%) среди всех предложений")
            elif position == total:
                st.markdown(f"- Имеет **наименьшую степень соответствия** ТЗ ({current_compliance}%) среди всех предложений")
            else:
                st.markdown(f"- Находится на **{position} месте из {total}** по степени соответствия ТЗ ({current_compliance}%)")
            
            # Добавляем рекомендацию по итогам сравнения
            st.markdown("**Рекомендация по результатам сравнения:**")
            if position == 1 and overall_score >= 75:
                st.markdown("✅ Данное КП является предпочтительным среди всех представленных.")
            elif position <= total / 3 and overall_score >= 60:
                st.markdown("✅ Данное КП входит в число лидеров и рекомендуется к дальнейшему рассмотрению.")
            elif position <= total / 2:
                st.markdown("⚠️ Данное КП имеет среднюю позицию, рекомендуется рассмотреть более сильные предложения.")
            else:
                st.markdown("❌ Данное КП находится среди аутсайдеров, рекомендуется отдать предпочтение другим предложениям.")
    
    # Кнопки управления
    st.divider()
    col1, col2, col3 = st.columns([2, 3, 2]) # Кнопка "Назад" шире
    
    with col1:
        if st.button("← Вернуться к Сравнительной таблице", use_container_width=True, key="report_back_to_comp"):
            st.session_state.analysis_result = None # Сбрасываем выбранный результат
            st.session_state.current_step = "comparison"
            st.rerun()
    
    with col2:
        # Кнопка для сохранения отчета
        if st.button(f"💾 Сохранить отчет по {company_name}", use_container_width=True, key="report_save_btn_new"):
            generate_pdf_report_placeholder(company_name)

def generate_pdf_report_placeholder(company_name):
    """Заглушка для функции генерации PDF-отчета."""
    # Отображаем индикатор загрузки
    with st.spinner(f"Генерация PDF-отчета для {company_name}..."):
        # Имитация процесса генерации
        progress_bar = st.progress(0)
        for i in range(101):
            time.sleep(0.02)  # Имитация длительного процесса
            progress_bar.progress(i)
        
        # Удаляем прогресс-бар
        progress_bar.empty()
        
        # Показываем уведомление об успехе
        st.success("✅ Функция экспорта в PDF будет доступна в следующей версии приложения.")

def render_additional_info_section(additional_info):
    """Отображает дополнительную информацию если она есть"""
    
    if not additional_info:
        return
    
    st.markdown("""
    <div style='background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 4px solid #22c55e;'>
        <h4 style='color: #15803d; margin-top: 0;'>🌟 Дополнительная информация</h4>
    """, unsafe_allow_html=True)
    
    # Добавляем ключевые выводы, если они есть
    if "key_findings" in additional_info and additional_info["key_findings"]:
        st.markdown("<h5>Ключевые выводы:</h5>", unsafe_allow_html=True)
        for finding in additional_info["key_findings"]:
            st.markdown(f"• {finding}")
    
    # Добавляем информацию о влиянии, если она есть
    if "impact" in additional_info and additional_info["impact"]:
        st.markdown("<h5>Влияние на оценку:</h5>", unsafe_allow_html=True)
        st.markdown(additional_info["impact"])
        
        # Добавляем информацию о влиянии на рейтинг, если она есть
        if "rating_impact" in additional_info:
            st.markdown(f"""
            <div style='margin-top: 10px; padding: 10px; background-color: #ecfdf5; border-radius: 4px;'>
                <strong>Модификатор рейтинга:</strong> +{additional_info["rating_impact"]} (существенное влияние на итоговую оценку)
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- Старые функции (могут быть удалены позже, если не используются) --- 
# def render_single_report(result_dir): ...
# def create_gauge_chart(value, title, height=400, max_value=100): ...
# def create_radar_chart(height=400): ... 