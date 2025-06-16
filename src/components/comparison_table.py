import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.config import settings
from src.services import ai_service
import time
import json
from datetime import datetime
import re
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os

def compare_all_proposals(analysis_results):
    """
    Создает сравнительный анализ всех КП между собой, 
    используя выбранную модель сравнения.
    
    Args:
        analysis_results: Список с результатами анализа всех КП
        
    Returns:
        str: HTML или Markdown текст с сравнительным анализом
    """
    if not analysis_results or len(analysis_results) < 2:
        return "Недостаточно КП для сравнительного анализа. Загрузите хотя бы 2 КП."
    
    # Собираем данные для сравнения
    companies_data = []
    for analysis in analysis_results:
        companies_data.append({
            "company_name": analysis.get("company_name", analysis["kp_name"]),
            "compliance_score": analysis["comparison_result"]["compliance_score"],
            "tech_stack": analysis.get("tech_stack", "Не указано"),
            "pricing": analysis.get("pricing", "Не указано"),
            "timeline": analysis.get("timeline", "Не указано"),
            "missing_count": len(analysis["comparison_result"]["missing_requirements"]),
            "additional_count": len(analysis["comparison_result"]["additional_features"]),
            "missing_requirements": analysis["comparison_result"]["missing_requirements"],
            "additional_features": analysis["comparison_result"]["additional_features"],
            "strengths": analysis["preliminary_recommendation"]["strength"],
            "weaknesses": analysis["preliminary_recommendation"]["weakness"]
        })
    
    # Формируем сравнительный запрос с данными всех КП
    system_prompt = (
        "Ты - аналитик, специализирующийся на сравнении коммерческих предложений для тендеров. "
        "Проанализируй данные нескольких коммерческих предложений и подготовь сравнительный отчет. "
        "Сосредоточься на следующих аспектах:\n"
        "1. Общий рейтинг КП от лучшего к худшему с объяснением выбора\n"
        "2. Сравнение ценовых предложений и соотношения цена/качество\n"
        "3. Сравнение технологических подходов и их соответствия задаче\n"
        "4. Сравнение сроков реализации\n"
        "5. Анализ рисков по каждому КП\n"
        "6. Рекомендация по выбору лучшего КП с обоснованием\n\n"
        "Твой отчет должен быть структурирован, аналитичен и содержать конкретные рекомендации. "
        "Используй Markdown для форматирования. Помни, что это итоговый документ для принятия решения."
    )
    
    # Формируем запрос с описанием всех компаний
    prompt = "# Данные для сравнительного анализа КП\n\n"
    
    for i, comp in enumerate(companies_data, 1):
        prompt += f"## Компания {i}: {comp['company_name']}\n"
        prompt += f"* Соответствие ТЗ: {comp['compliance_score']}%\n"
        prompt += f"* Технологический стек: {comp['tech_stack']}\n"
        prompt += f"* Стоимость: {comp['pricing']}\n"
        prompt += f"* Сроки реализации: {comp['timeline']}\n"
        prompt += f"* Пропущенные требования: {comp['missing_count']} шт\n"
        prompt += f"* Дополнительные функции: {comp['additional_count']} шт\n"
        
        prompt += "* Сильные стороны:\n"
        for s in comp['strengths']:
            prompt += f"  - {s}\n"
        
        prompt += "* Слабые стороны:\n"
        for w in comp['weaknesses']:
            prompt += f"  - {w}\n"
        
        prompt += "\n"
    
    # Используем модель для сравнения КП из session_state
    # Здесь используем именно selected_comparison_model, а не selected_model
    comparison_model_id = st.session_state.get("selected_comparison_model")
    
    try:
        st.info(f"Формируем сравнительный анализ КП с использованием модели {comparison_model_id}...")
        comparison_html = ai_service.get_ai_response(prompt, system_prompt, model_id=comparison_model_id)
        
        # Удаляем маркеры кода, если модель обернула HTML в блок кода
        comparison_html = re.sub(r'^```html\s*', '', comparison_html)
        comparison_html = re.sub(r'\s*```$', '', comparison_html)
        
        # Проверяем, является ли ответ валидным HTML
        if not comparison_html.strip().startswith("<"):
            # Если ответ не похож на HTML, обрамляем его тегами для форматирования
            comparison_html = f"""
            <div style='font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto;'>
                {comparison_html}
            </div>
            """
        
        return comparison_html
    except Exception as e:
        st.error(f"Ошибка при формировании сравнительного анализа: {e}")
        return "Не удалось сформировать сравнительный анализ. Пожалуйста, попробуйте еще раз или выберите другую модель."

def create_visualization_html(vis_type, comparative_data):
    """
    Создает HTML-код с интерактивной визуализацией Plotly
    
    Args:
        vis_type: Тип визуализации (например, 'Стоимость предложений')
        comparative_data: Данные для визуализации
        
    Returns:
        str: HTML-код с внедренной визуализацией
    """
    if "стоимость" in vis_type.lower() or "цен" in vis_type.lower() or "финанс" in vis_type.lower():
        # Визуализация стоимости
        fig = create_price_visualization(comparative_data)
    elif "срок" in vis_type.lower() or "время" in vis_type.lower() or "реализац" in vis_type.lower():
        # Визуализация сроков
        fig = create_timeline_visualization(comparative_data)
    elif "соответств" in vis_type.lower() or "требован" in vis_type.lower() or "техн" in vis_type.lower():
        # Визуализация соответствия требованиям
        fig = create_compliance_visualization(comparative_data)
    elif "рейтинг" in vis_type.lower() or "оценк" in vis_type.lower() or "сравнен" in vis_type.lower():
        # Визуализация сравнения рейтингов
        fig = create_rating_visualization(comparative_data)
    elif "риск" in vis_type.lower() or "недостатк" in vis_type.lower():
        # Визуализация рисков
        fig = create_risk_visualization(comparative_data)
    else:
        # Общий случай - сводная визуализация
        fig = create_summary_visualization(comparative_data)
    
    # Конвертируем график в HTML
    config = {'displayModeBar': False, 'staticPlot': False, 'responsive': True}
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn', config=config)
    
    # Оборачиваем в контейнер для стилизации
    return f"""
    <div class="visualization-container">
        <h4 class="visualization-title">{vis_type}</h4>
        {plot_html}
    </div>
    """

def create_price_visualization(comparative_data):
    """Создает визуализацию сравнения стоимости предложений"""
    # Подготавливаем данные
    companies = [data["vendor_name"] for data in comparative_data]
    prices = []
    price_labels = []
    
    for data in comparative_data:
        price_text = data["pricing"]
        price = extract_price_value(price_text)
        if price > 0:
            prices.append(price)
            price_labels.append(data["vendor_name"])
    
    # Сортируем по возрастанию цены
    sorted_data = sorted(zip(price_labels, prices), key=lambda x: x[1])
    companies_sorted = [item[0] for item in sorted_data]
    prices_sorted = [item[1] for item in sorted_data]
    
    # Создаем визуализацию с Plotly
    fig = px.bar(
        x=companies_sorted, 
        y=prices_sorted,
        labels={'x': 'Компания', 'y': 'Стоимость'},
        title='Сравнение стоимости предложений',
        color_discrete_sequence=[settings.BRAND_COLORS["primary"]]
    )
    
    # Форматируем числа и настраиваем вид
    max_price = max(prices_sorted) if prices_sorted else 0
    price_format = ',.0f' if max_price > 1000 else '.2f'
    
    fig.update_layout(
        xaxis_title="Компания",
        yaxis_title="Стоимость",
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=40, r=20, t=40, b=80),
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)')
    )
    
    fig.update_traces(texttemplate='%{y:' + price_format + '}', textposition='outside')
    
    return fig

def create_timeline_visualization(comparative_data):
    """Создает визуализацию сравнения сроков реализации"""
    # Подготавливаем данные
    companies = []
    timelines = []
    
    for data in comparative_data:
        timeline_text = data["timeline"]
        days = extract_timeline_days(timeline_text)
        if days > 0:
            timelines.append(days)
            companies.append(data["vendor_name"])
    
    # Сортируем по возрастанию сроков
    sorted_data = sorted(zip(companies, timelines), key=lambda x: x[1])
    companies_sorted = [item[0] for item in sorted_data]
    timelines_sorted = [item[1] for item in sorted_data]
    
    # Создаем визуализацию
    fig = px.bar(
        x=companies_sorted, 
        y=timelines_sorted,
        labels={'x': 'Компания', 'y': 'Дни'},
        title='Сравнение сроков реализации',
        color_discrete_sequence=[settings.BRAND_COLORS["accent"]]
    )
    
    fig.update_layout(
        xaxis_title="Компания",
        yaxis_title="Дни",
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=40, r=20, t=40, b=80),
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)')
    )
    
    fig.update_traces(texttemplate='%{y} дней', textposition='outside')
    
    return fig

def create_compliance_visualization(comparative_data):
    """Создает визуализацию соответствия требованиям и технических решений"""
    # Подготавливаем данные
    companies = [data["vendor_name"] for data in comparative_data]
    compliance = [data["compliance_score"] for data in comparative_data]
    missing = [len(data["missing_requirements"]) for data in comparative_data]
    additional = [len(data["additional_features"]) for data in comparative_data]
    
    # Сортируем по убыванию соответствия
    sorted_indices = sorted(range(len(compliance)), key=lambda k: compliance[k], reverse=True)
    companies_sorted = [companies[i] for i in sorted_indices]
    compliance_sorted = [compliance[i] for i in sorted_indices]
    missing_sorted = [missing[i] for i in sorted_indices]
    additional_sorted = [additional[i] for i in sorted_indices]
    
    # Создаем подграфики для соответствия и дополнительных параметров
    fig = make_subplots(
        rows=2, cols=1, 
        subplot_titles=("Соответствие ТЗ (%)", "Количество упущенных/дополнительных требований"),
        vertical_spacing=0.3
    )
    
    # Первый график - соответствие ТЗ (%)
    fig.add_trace(
        go.Bar(
            x=companies_sorted, 
            y=compliance_sorted, 
            name="Соответствие ТЗ (%)",
            marker_color=settings.BRAND_COLORS["primary"],
            text=compliance_sorted,
            texttemplate='%{text}%',
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Второй график - количество упущенных и дополнительных требований
    fig.add_trace(
        go.Bar(
            x=companies_sorted, 
            y=missing_sorted, 
            name="Пропущенные требования",
            marker_color="#FF5252",
            text=missing_sorted,
            textposition='outside'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=companies_sorted, 
            y=additional_sorted, 
            name="Дополнительные функции",
            marker_color="#4CAF50",
            text=additional_sorted,
            textposition='outside'
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=80, b=40),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    fig.update_xaxes(tickangle=-45)
    fig.update_yaxes(gridcolor='rgba(0,0,0,0.1)')
    
    return fig

def create_rating_visualization(comparative_data):
    """Создает визуализацию рейтингов КП"""
    # Подготавливаем данные
    companies = [data["vendor_name"] for data in comparative_data]
    compliance = [data["compliance_score"] for data in comparative_data]
    ratings = [data["avg_rating"] * 10 for data in comparative_data]  # переводим в шкалу 0-100
    
    # Добавляем индикатор наличия дополнительной информации
    has_additional_info = [data.get("has_additional_info", False) for data in comparative_data]
    
    # Расчет общего рейтинга с учетом дополнительной информации (если есть)
    overall = [(data["avg_rating"] * 10 + data["compliance_score"]) / 2 for data in comparative_data]
    
    # Сортируем по убыванию общего рейтинга
    sorted_indices = sorted(range(len(overall)), key=lambda k: overall[k], reverse=True)
    companies_sorted = [companies[i] for i in sorted_indices]
    compliance_sorted = [compliance[i] for i in sorted_indices]
    ratings_sorted = [ratings[i] for i in sorted_indices]
    overall_sorted = [overall[i] for i in sorted_indices]
    has_additional_info_sorted = [has_additional_info[i] for i in sorted_indices]
    
    # Создаем визуализацию
    fig = go.Figure()
    
    # Добавляем линии для порогов рекомендаций
    fig.add_shape(
        type="line",
        x0=-0.5, y0=75, x1=len(companies_sorted)-0.5, y1=75,
        line=dict(color="green", width=1, dash="dash"),
    )
    
    fig.add_shape(
        type="line",
        x0=-0.5, y0=60, x1=len(companies_sorted)-0.5, y1=60,
        line=dict(color="orange", width=1, dash="dash"),
    )
    
    # Добавляем три показателя для каждой компании
    fig.add_trace(go.Bar(
        x=companies_sorted, 
        y=compliance_sorted, 
        name="Соответствие ТЗ (%)",
        marker_color=settings.BRAND_COLORS["primary"],
        text=["%.1f%%" % val for val in compliance_sorted],
        textposition='outside'
    ))
    
    fig.add_trace(go.Bar(
        x=companies_sorted, 
        y=ratings_sorted, 
        name="Рейтинг (0-100)",
        marker_color=settings.BRAND_COLORS["accent"],
        text=["%.1f" % val for val in ratings_sorted],
        textposition='outside'
    ))
    
    # Добавляем метки для КП с дополнительной информацией в текст общего рейтинга
    overall_text = []
    for i, val in enumerate(overall_sorted):
        if has_additional_info_sorted[i]:
            overall_text.append("%.1f ⭐" % val)  # Добавляем звездочку к рейтингу с дополнительной информацией
        else:
            overall_text.append("%.1f" % val)
            
    fig.add_trace(go.Scatter(
        x=companies_sorted, 
        y=overall_sorted, 
        name="Общий рейтинг",
        mode='lines+markers+text',
        marker=dict(size=10, color="#FF9800"),
        line=dict(width=2, color="#FF9800"),
        text=overall_text,
        textposition='top center'
    ))
    
    # Настраиваем внешний вид
    fig.update_layout(
        title='Сравнение рейтингов КП',
        xaxis_title="Компания",
        yaxis_title="Оценка (0-100)",
        barmode='group',
        height=500,
        xaxis_tickangle=-45,
        yaxis=dict(range=[0, 100]),
        margin=dict(l=40, r=20, t=60, b=80),
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_gridcolor='rgba(0,0,0,0.1)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        annotations=[
            dict(
                x=len(companies_sorted)-1, y=75,
                xref="x", yref="y",
                text="Рекомендуется",
                showarrow=False,
                font=dict(size=10, color="green"),
                xanchor="right", yanchor="bottom"
            ),
            dict(
                x=len(companies_sorted)-1, y=60,
                xref="x", yref="y",
                text="Требует доработки",
                showarrow=False,
                font=dict(size=10, color="orange"),
                xanchor="right", yanchor="bottom"
            )
        ]
    )
    
    return fig

def create_risk_visualization(comparative_data):
    """Создает визуализацию рисков по предложениям"""
    # Подготавливаем данные
    companies = [data["vendor_name"] for data in comparative_data]
    missing_counts = [len(data["missing_requirements"]) for data in comparative_data]
    weakness_counts = [len(data["weaknesses"]) for data in comparative_data]
    
    # Рассчитываем риск-рейтинг (чем больше, тем выше риск)
    risk_scores = []
    for i, data in enumerate(comparative_data):
        score = data["compliance_score"]
        risk = 100 - score + missing_counts[i] * 2 + weakness_counts[i]
        risk_scores.append(min(100, risk))  # Ограничиваем до 100
    
    # Создаем цветовую шкалу для рисков
    risk_colors = []
    for score in risk_scores:
        if score < 40:
            risk_colors.append("#4CAF50")  # Зеленый - низкий риск
        elif score < 70:
            risk_colors.append("#FFC107")  # Желтый - средний риск
        else:
            risk_colors.append("#FF5252")  # Красный - высокий риск
    
    # Сортируем по возрастанию риска
    sorted_data = sorted(zip(companies, risk_scores, risk_colors), key=lambda x: x[1])
    companies_sorted = [item[0] for item in sorted_data]
    risk_scores_sorted = [item[1] for item in sorted_data]
    risk_colors_sorted = [item[2] for item in sorted_data]
    
    # Создаем визуализацию
    fig = px.bar(
        x=companies_sorted, 
        y=risk_scores_sorted,
        labels={'x': 'Компания', 'y': 'Уровень риска'},
        title='Оценка рисков по предложениям',
    )
    
    # Настраиваем цвета столбцов
    fig.update_traces(marker_color=risk_colors_sorted, texttemplate='%{y:.1f}', textposition='outside')
    
    fig.update_layout(
        xaxis_title="Компания",
        yaxis_title="Уровень риска (0-100)",
        xaxis_tickangle=-45,
        height=400,
        margin=dict(l=40, r=20, t=40, b=80),
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', range=[0, 100])
    )
    
    # Добавляем аннотации для интерпретации уровней риска
    fig.add_shape(
        type="rect",
        x0=-0.5, y0=0, x1=len(companies_sorted)-0.5, y1=40,
        fillcolor="rgba(76,175,80,0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, y0=40, x1=len(companies_sorted)-0.5, y1=70,
        fillcolor="rgba(255,193,7,0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_shape(
        type="rect",
        x0=-0.5, y0=70, x1=len(companies_sorted)-0.5, y1=100,
        fillcolor="rgba(255,82,82,0.1)",
        line=dict(width=0),
        layer="below"
    )
    
    fig.add_annotation(
        x=len(companies_sorted)-0.5, y=20,
        text="Низкий риск",
        showarrow=False,
        font=dict(size=10, color="green"),
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(companies_sorted)-0.5, y=55,
        text="Средний риск",
        showarrow=False,
        font=dict(size=10, color="orange"),
        xanchor="right"
    )
    
    fig.add_annotation(
        x=len(companies_sorted)-0.5, y=85,
        text="Высокий риск",
        showarrow=False,
        font=dict(size=10, color="red"),
        xanchor="right"
    )
    
    return fig

def create_summary_visualization(comparative_data):
    """Создает сводную визуализацию с основными показателями КП"""
    # Подготавливаем данные
    companies = [data["vendor_name"] for data in comparative_data]
    
    # Рассчитываем общий рейтинг
    overall_scores = [(data["avg_rating"] * 10 + data["compliance_score"]) / 2 for data in comparative_data]
    
    # Сортируем по убыванию общего рейтинга
    sorted_data = sorted(zip(companies, overall_scores, comparative_data), key=lambda x: x[1], reverse=True)
    companies_sorted = [item[0] for item in sorted_data]
    scores_sorted = [item[1] for item in sorted_data]
    data_sorted = [item[2] for item in sorted_data]
    
    # Создаем таблицу с основными показателями
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Компания', 'Общий рейтинг', 'Соответствие ТЗ', 'Стоимость', 'Сроки', 'Рекомендация'],
            fill_color=settings.BRAND_COLORS["primary"],
            align='center',
            font=dict(color='white', size=12),
            height=40
        ),
        cells=dict(
            values=[
                companies_sorted,
                [f"{score:.1f}/100" for score in scores_sorted],
                [f"{data['compliance_score']}%" for data in data_sorted],
                [data["pricing"] for data in data_sorted],
                [data["timeline"] for data in data_sorted],
                [data["recommendation"] for data in data_sorted]
            ],
            fill_color=[['white', 'rgba(240,240,240,0.5)'] * len(companies_sorted)],
            align=['left', 'center', 'center', 'left', 'left', 'center'],
            font=dict(color=['black'], size=11),
            height=35
        )
    )])
    
    fig.update_layout(
        title='Сводные данные по коммерческим предложениям',
        height=75 + 35 * len(companies_sorted),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def generate_analytical_report(analysis_results):
    """
    Генерирует профессиональный аналитический отчет по сравнению всех КП
    с использованием выбранной модели сравнения.
    
    Args:
        analysis_results: Список с результатами анализа всех КП
        
    Returns:
        str: HTML отчет с аналитическим сравнением
    """
    # Local import to ensure datetime is available in this function
    from datetime import datetime
    
    if not analysis_results or len(analysis_results) < 2:
        return "Недостаточно КП для сравнительного анализа. Загрузите хотя бы 2 КП."
    
    # Подготавливаем данные для запроса к модели
    comparative_data = []
    
    for analysis in analysis_results:
        company_name = analysis.get("company_name", analysis["kp_name"])
        compliance_score = analysis["comparison_result"]["compliance_score"]
        missing_count = len(analysis["comparison_result"]["missing_requirements"])
        additional_count = len(analysis["comparison_result"]["additional_features"])
        
        # Рассчитываем среднюю оценку
        ratings = analysis.get("ratings", {})
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        
        # Проверяем наличие дополнительной информации
        has_additional_info = analysis.get("additional_info_analysis") is not None
        
        # Определяем рекомендацию
        overall_score = (avg_rating * 10 + compliance_score) / 2
        if overall_score >= 75:
            recommendation = "Рекомендовать к принятию"
        elif overall_score >= 60:
            recommendation = "Рекомендовать к доработке"
        else:
            recommendation = "Рекомендовать к отклонению"
        
        vendor_data = {
            "vendor_name": company_name,
            "compliance_score": compliance_score,
            "tech_stack": analysis.get("tech_stack", "Не указан"),
            "pricing": analysis.get("pricing", "Не указана"),
            "timeline": analysis.get("timeline", "Не указаны"),
            "missing_requirements": analysis["comparison_result"]["missing_requirements"],
            "additional_features": analysis["comparison_result"]["additional_features"],
            "strengths": analysis["preliminary_recommendation"]["strength"],
            "weaknesses": analysis["preliminary_recommendation"]["weakness"],
            "avg_rating": avg_rating,
            "recommendation": recommendation,
            "overall_score": overall_score,
            "has_additional_info": has_additional_info
        }
        comparative_data.append(vendor_data)
    
    # Формируем системный промпт для аналитического отчета
    system_prompt = r"""
    Ты - ведущий аналитик в области тендерных процессов. Твоя задача - создать профессиональный аналитический отчет в HTML формате, \
    который поможет заказчику принять обоснованное решение при выборе подрядчика.\
    \
    Структура отчета должна включать следующие HTML секции:\
    \
    <h1>Аналитический отчет по выбору подрядчика</h1>\
    \
    <h2>1. Итоговое резюме и рекомендация</h2>\
    - Обзор всех предложений\
    - Выявление лидеров и аутсайдеров\
    - Ключевые различия между предложениями\
    - Итоговая рекомендация с обоснованием\
    \
    <h2>2. Сравнительная таблица ключевых показателей</h2>\
    - Создай HTML таблицу (<table>) с компаниями и их показателями\
    - Используй CSS классы .high, .medium, .low для цветового кодирования ячеек\
    \
    <h2>3. Анализ финансовых предложений</h2>\
    - Сравнение стоимости разных предложений\
    - Для графиков используй <div class="visual">[VISUALIZATION: Название визуализации]</div>\
    \
    <h2>4. Сравнение сроков реализации</h2>\
    - Анализ предложенных сроков и их реалистичности\
    - Для графиков используй <div class="visual">[VISUALIZATION: Название визуализации]</div>\
    \
    <h2>5. Сравнение технических решений и соответствия ТЗ</h2>\
    - Анализ технических подходов\
    - Оценка непокрытых требований и дополнительных функций\
    \
    <h2>6. Анализ рисков</h2>\
    - Используй <div class="warning"> для блоков с рисками\
    - Выявление ключевых рисков по каждому предложению\
    \
    <h2>7. Детальные отчеты и заключение</h2>\
    - Используй <div class="recommendation"> для блоков с рекомендациями\
    - Четкое обоснование финального выбора\
    \
    Обязательно используй стандартный HTML5 с корректным синтаксисом. Не используй Markdown внутри HTML.\
    Для визуализаций используй плейсхолдеры в формате [VISUALIZATION: Название] внутри div с классом visual.\
    \
    В конце отчета добавь:\
    <p>Отчет сгенерирован системой Devent Tender Analysis AI | Дата формирования: ТЕКУЩАЯ_ДАТА</p>\
    """
    
    # Формируем запрос с данными всех КП
    prompt = "# Данные для аналитического отчета по КП\n\n"
    
    for i, vendor in enumerate(comparative_data, 1):
        prompt += f"## Компания {i}: {vendor['vendor_name']}\n"
        prompt += f"* Общий рейтинг: {vendor['overall_score']:.1f}/100\n"
        prompt += f"* Соответствие ТЗ: {vendor['compliance_score']}%\n"
        prompt += f"* Технологический стек: {vendor['tech_stack']}\n"
        prompt += f"* Стоимость: {vendor['pricing']}\n"
        prompt += f"* Сроки реализации: {vendor['timeline']}\n"
        prompt += f"* Пропущенные требования: {len(vendor['missing_requirements'])} шт\n"
        if len(vendor['missing_requirements']) > 0:
            prompt += "  - " + "\n  - ".join(vendor['missing_requirements'][:3])
            if len(vendor['missing_requirements']) > 3:
                prompt += f"\n  - ... и еще {len(vendor['missing_requirements']) - 3} требований"
            prompt += "\n"
        
        prompt += f"* Дополнительные функции: {len(vendor['additional_features'])} шт\n"
        if len(vendor['additional_features']) > 0:
            prompt += "  - " + "\n  - ".join(vendor['additional_features'][:3])
            if len(vendor['additional_features']) > 3:
                prompt += f"\n  - ... и еще {len(vendor['additional_features']) - 3} функций"
            prompt += "\n"
        
        prompt += "* Сильные стороны:\n"
        for s in vendor['strengths']:
            prompt += f"  - {s}\n"
        
        prompt += "* Слабые стороны:\n"
        for w in vendor['weaknesses']:
            prompt += f"  - {w}\n"
        
        prompt += f"* Рекомендация: {vendor['recommendation']}\n\n"
    
    # Используем модель для сравнения КП из session_state
    comparison_model_id = st.session_state.get("selected_comparison_model")
    
    try:
        st.info(f"Формируем аналитический отчет с использованием модели {comparison_model_id}...")
        report_html = ai_service.get_ai_response(prompt, system_prompt, model_id=comparison_model_id)
        
        # Очищаем ответ от некорректных \u escape-последовательностей
        # Заменяем \u (если за ним не идут 4 hex-символа) на \\u
        # Исправленный шаблон: r'\\u(...)' вместо r'\u(...)'
        report_html = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\u', report_html)
        
        # Удаляем маркеры кода, если модель обернула HTML в блок кода
        report_html = re.sub(r'^```html\s*', '', report_html)
        report_html = re.sub(r'\s*```$', '', report_html)
        
        # Удаляем DOCTYPE и HTML теги, если модель создала полный HTML документ
        report_html = re.sub(r'<!DOCTYPE[^>]*>|<html[^>]*>|<head>.*?</head>|<body[^>]*>|</body>|</html>', '', report_html, flags=re.DOTALL)
        
        # Проверяем, является ли ответ валидным HTML
        if not report_html.strip().startswith("<"):
            # Если ответ не похож на HTML, обрамляем его тегами для форматирования
            report_html = f"<div style='font-family: Arial, sans-serif; line-height: 1.6;'>{report_html}</div>"
        
        # Обрабатываем плейсхолдеры визуализаций - ЗАМЕНА НА ЗАГЛУШКИ
        # Добавляем CSS-стили (стили визуализаций теперь не нужны, но оставим для контейнера)
        css_styles = """
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1000px;
                margin: 0 auto;
            }
            h1 {
                color: #1E3A8A;
                font-size: 24px;
                margin-bottom: 16px;
            }
            h2 {
                color: #2563EB;
                font-size: 20px;
                margin-top: 24px;
                margin-bottom: 16px;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 8px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 16px 0;
            }
            th {
                background-color: #EFF6FF;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                border: 1px solid #D1D5DB;
            }
            td {
                padding: 12px;
                border: 1px solid #D1D5DB;
            }
            .high {
                background-color: #DCFCE7;
                color: #166534;
            }
            .medium {
                background-color: #FEF9C3;
                color: #854D0E;
            }
            .low {
                background-color: #FEE2E2;
                color: #B91C1C;
            }
            .visual {
                background-color: #F3F4F6;
                border-radius: 8px;
                padding: 16px;
                margin: 16px 0;
                text-align: center;
            }
            .warning {
                background-color: #FEF3C7;
                border-left: 4px solid #F59E0B;
                padding: 16px;
                margin: 16px 0;
            }
            .recommendation {
                background-color: #DBEAFE;
                border-left: 4px solid #2563EB;
                padding: 16px;
                margin: 16px 0;
            }
            .footer {
                margin-top: 32px;
                padding-top: 16px;
                border-top: 1px solid #E5E7EB;
                color: #6B7280;
                font-size: 14px;
                text-align: center;
            }
            .vis-placeholder {
                padding: 20px;
                margin: 16px 0;
                background-color: #f8f9fa;
                border: 1px dashed #ced4da;
                text-align: center;
                color: #6c757d;
                font-style: italic;
                border-radius: 8px;
            }
        </style>
        """

        # Определяем текст заглушки
        placeholder_text = "<div class='vis-placeholder'>[Визуализация будет доступна позже]</div>"
        placeholder_text_named = "<div class='vis-placeholder'>[Визуализация '{vis_name}' будет доступна позже]</div>"

        # Удаляем код автоматической вставки визуализаций
        # report_html = re.sub(r'(<h2>3\. Анализ финансовых предложений</h2>.*?)(<h2>|$)', r'\\1' + price_vis + r'\\2', report_html, flags=re.DOTALL)
        # report_html = re.sub(r'(<h2>4\. Сравнение сроков реализации</h2>.*?)(<h2>|$)', r'\\1' + timeline_vis + r'\\2', report_html, flags=re.DOTALL)
        # report_html = re.sub(r'(<h2>5\. Сравнение технических решений.*?</h2>.*?)(<h2>|$)', r'\\1' + compliance_vis + r'\\2', report_html, flags=re.DOTALL)


        # Заменяем [VISUALIZATION: Name] на заглушку
        report_html = re.sub(r'\\[VISUALIZATION:?\\s*(.*?)\\]', lambda m: placeholder_text_named.format(vis_name=m.group(1).strip()), report_html)

        # Заменяем [VISUALIZATION] на заглушку
        report_html = re.sub(r'\\[VISUALIZATION\\]', placeholder_text, report_html)

        # Заменяем <div class="visual">...</div> на заглушку
        report_html = re.sub(r'<div class="visual">.*?</div>', placeholder_text, report_html, flags=re.DOTALL | re.IGNORECASE)

        # Оборачиваем отчет стилями, но НЕ добавляем div container в начало
        # Просто встраиваем CSS стили перед содержимым
        report_html = f"{css_styles}{report_html}"

        # Добавляем дату в отчет, если модель не добавила ее сама
        if "Дата формирования" not in report_html:
            # Ищем существующий div footer или добавляем новый
            if '<div class="footer">' in report_html:
                 # Если футер уже есть (возможно, добавлен стилями), просто вставляем текст
                 report_html = report_html.replace('<div class="footer">', 
                     f'<div class="footer"><p>Отчет сгенерирован системой Devent Tender Analysis AI | Дата формирования: {datetime.now().strftime("%d.%m.%Y")}</p>')
            else:
                 # Добавляем новый футер
                 report_html += f"""
                 <div class="footer">
                     <p>Отчет сгенерирован системой Devent Tender Analysis AI | Дата формирования: {datetime.now().strftime('%d.%m.%Y')}</p>
                 </div>
                 """

        return report_html
    except Exception as e:
        # Добавляем traceback в лог для детальной диагностики
        import traceback
        st.error(f"Ошибка при формировании аналитического отчета: {e}\\n{traceback.format_exc()}")
        return f"Не удалось сформировать аналитический отчет. Ошибка: {str(e)}"

# Вспомогательные функции для подготовки данных
def extract_price_value(price_text):
    """Извлекает числовое значение цены из текстового описания"""
    import re
    
    # Очищаем текст от НДС и другой информации
    price_text = price_text.lower().replace('без ндс', '').replace('с ндс', '')
    
    # Пытаемся найти числовые значения
    numbers = re.findall(r'(\d[\d\s]*[\d.,]*\d)', price_text)
    if numbers:
        # Берем первое найденное число и очищаем от пробелов
        price_str = numbers[0].replace(' ', '').replace(',', '.')
        try:
            return float(price_str)
        except ValueError:
            return 0
    return 0

def extract_pricing_model(price_text):
    """Определяет модель ценообразования из текстового описания"""
    if "фиксированная" in price_text.lower():
        return "Fixed Price"
    elif "t&m" in price_text.lower() or "time & materials" in price_text.lower():
        return "Time & Materials"
    else:
        return "Unknown"

def extract_timeline_days(timeline_text):
    """Извлекает длительность в днях из текстового описания сроков"""
    import re
    
    # Ищем упоминания дней, недель, месяцев
    days_match = re.search(r'(\d+)\s*(?:раб\w+\s*)?дн', timeline_text.lower())
    weeks_match = re.search(r'(\d+)\s*недел', timeline_text.lower())
    months_match = re.search(r'(\d+)\s*месяц', timeline_text.lower())
    
    days = 0
    
    if days_match:
        days += int(days_match.group(1))
    if weeks_match:
        days += int(weeks_match.group(1)) * 7
    if months_match:
        days += int(months_match.group(1)) * 30
    
    # Если никаких сроков не нашли, возвращаем случайное значение как заглушку
    if days == 0:
        days = np.random.randint(30, 120)
    
    return days

def assess_timeline_realism(timeline_text):
    """Оценивает реалистичность предложенных сроков"""
    timeline_days = extract_timeline_days(timeline_text)
    
    if timeline_days < 45:
        return "Оптимистичный"
    elif timeline_days < 90:
        return "Реалистичный"
    else:
        return "Консервативный"

def assess_risk_level(compliance_score, avg_rating):
    """Оценивает общий уровень риска на основе соответствия ТЗ и рейтинга"""
    combined_score = (compliance_score + avg_rating * 10) / 2
    
    if combined_score >= 80:
        return "Low"
    elif combined_score >= 60:
        return "Medium"
    else:
        return "High"

def generate_critical_risks(weaknesses):
    """Генерирует структуру критических рисков на основе слабых сторон"""
    risks = []
    
    risk_categories = ["Technical", "Financial", "Timeline", "Scope", "Quality"]
    
    for i, weakness in enumerate(weaknesses):
        if i >= 3:  # Ограничиваем количество рисков
            break
            
        category = risk_categories[i % len(risk_categories)]
        
        risks.append({
            "category": category,
            "risk": weakness,
            "severity": np.random.randint(1, 5),  # Случайная оценка серьезности от 1 до 5
            "mitigation_proposed": "Требуется дополнительное обсуждение с поставщиком"
        })
    
    return risks

def random_budget_variance():
    """Возвращает случайное отклонение от бюджета как заглушку"""
    return round(np.random.uniform(-15, 25), 1)

def random_timeline_variance():
    """Возвращает случайное отклонение от сроков как заглушку"""
    return round(np.random.uniform(-10, 30), 1)

def export_comparison_to_pdf(comparison_df, all_analyses):
    """
    Экспортирует сравнительную таблицу КП в PDF файл
    
    Args:
        comparison_df: DataFrame с данными сравнительной таблицы
        all_analyses: Список с результатами анализа всех КП
        
    Returns:
        BytesIO: PDF файл в формате BytesIO для скачивания
    """
    # Создаем временный BytesIO буфер для хранения PDF
    buffer = BytesIO()
    
    # Создаем PDF документ
    with PdfPages(buffer) as pdf:
        # --- Титульная страница ---
        plt.figure(figsize=(11, 8.5))
        plt.axis('off')
        plt.text(0.5, 0.8, 'Сравнительный анализ', fontsize=24, ha='center')
        plt.text(0.5, 0.7, 'коммерческих предложений', fontsize=24, ha='center')
        plt.text(0.5, 0.5, f'Сгенерирован: {datetime.now().strftime("%d.%m.%Y %H:%M")}', fontsize=14, ha='center')
        plt.text(0.5, 0.4, f'Проанализировано КП: {len(all_analyses)}', fontsize=14, ha='center')
        plt.text(0.5, 0.2, 'Devent Tender Analysis AI', fontsize=16, ha='center', color='gray')
        pdf.savefig()
        plt.close()
        
        # --- Сравнительная таблица ---
        plt.figure(figsize=(11, 8.5))
        plt.axis('off')
        plt.text(0.5, 0.95, 'Сравнительная таблица КП', fontsize=16, ha='center')
        
        # Подготавливаем данные для таблицы
        table_data = comparison_df.copy()
        if 'kp_key' in table_data.columns:
            table_data = table_data.drop('kp_key', axis=1)
        
        # Рисуем таблицу
        table = plt.table(
            cellText=table_data.values,
            colLabels=table_data.columns,
            cellLoc='center',
            loc='center',
            colWidths=[0.15, 0.10, 0.20, 0.15, 0.10, 0.10, 0.10, 0.10]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)
        pdf.savefig()
        plt.close()
        
        # --- График сравнения ---
        plt.figure(figsize=(11, 6))
        summary_data = comparison_df[["Название компании", "Соответствие (%)", "Рейтинг (1-10)"]]
        
        # Сокращаем длинные названия компаний
        summary_data["Название компании"] = summary_data["Название компании"].apply(
            lambda x: x[:20] + '...' if len(x) > 20 else x
        )
        
        # Нормализуем рейтинг до 100 для единообразия
        y1 = summary_data["Соответствие (%)"]
        y2 = summary_data["Рейтинг (1-10)"] * 10
        x = range(len(summary_data))
        
        plt.bar(x, y1, width=0.4, align='center', label='Соответствие ТЗ (%)', color=settings.BRAND_COLORS["primary"])
        plt.bar([i+0.4 for i in x], y2, width=0.4, align='center', label='Рейтинг (0-100)', color=settings.BRAND_COLORS["accent"])
        
        plt.xticks([i+0.2 for i in x], summary_data["Название компании"], rotation=45, ha='right')
        plt.ylim(0, 100)
        plt.legend()
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.title('Сравнение соответствия ТЗ и рейтинга')
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # --- Анализ цен и сроков ---
        plt.figure(figsize=(11, 8.5))
        plt.subplot(2, 1, 1)
        
        # Извлекаем и обрабатываем цены
        prices = []
        price_labels = []
        for i, row in comparison_df.iterrows():
            price_text = row["Стоимость"]
            price_labels.append(row["Название компании"])
            try:
                # Пытаемся извлечь числовое значение из строки
                price_value = extract_price_value(price_text)
                prices.append(price_value)
            except:
                prices.append(0)
        
        # Сортируем по возрастанию цены
        price_data = sorted(zip(price_labels, prices), key=lambda x: x[1])
        price_labels = [item[0] for item in price_data]
        prices = [item[1] for item in price_data]
        
        plt.bar(price_labels, prices, color=settings.BRAND_COLORS["primary"])
        plt.xticks(rotation=45, ha='right')
        plt.title('Сравнение стоимости предложений')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        # График сроков
        plt.subplot(2, 1, 2)
        timelines = []
        for i, row in comparison_df.iterrows():
            timeline_text = row["Сроки"]
            try:
                # Пытаемся извлечь длительность в днях
                days = extract_timeline_days(timeline_text)
                timelines.append((row["Название компании"], days))
            except:
                timelines.append((row["Название компании"], 0))
        
        # Сортируем по возрастанию сроков
        timelines.sort(key=lambda x: x[1])
        
        timeline_labels = [item[0] for item in timelines]
        timeline_days = [item[1] for item in timelines]
        
        plt.bar(timeline_labels, timeline_days, color=settings.BRAND_COLORS["accent"])
        plt.xticks(rotation=45, ha='right')
        plt.title('Сравнение сроков реализации (в днях)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        pdf.savefig()
        plt.close()
        
        # --- Страница с рекомендациями ---
        plt.figure(figsize=(11, 8.5))
        plt.axis('off')
        plt.text(0.5, 0.95, 'Рекомендации по выбору КП', fontsize=16, ha='center')
        
        # Сортируем компании по общему рейтингу
        overall_scores = []
        for analysis in all_analyses:
            company_name = analysis.get("company_name", analysis["kp_name"])
            compliance_score = analysis["comparison_result"]["compliance_score"]
            ratings = analysis.get("ratings", {})
            avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
            overall_score = (avg_rating * 10 + compliance_score) / 2
            overall_scores.append((company_name, overall_score))
        
        # Сортируем по убыванию оценки
        overall_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Выводим рекомендации
        y_pos = 0.85
        plt.text(0.1, y_pos, "Ранжирование КП по общей оценке:", fontsize=12)
        y_pos -= 0.05
        
        for i, (company, score) in enumerate(overall_scores, 1):
            if score >= 75:
                recommendation = "✅ Рекомендовано к принятию"
                color = 'green'
            elif score >= 60:
                recommendation = "⚠️ Рекомендовано с оговорками"
                color = 'orange'
            else:
                recommendation = "❌ Не рекомендовано"
                color = 'red'
                
            plt.text(0.1, y_pos, f"{i}. {company}", fontsize=11)
            plt.text(0.6, y_pos, f"Оценка: {score:.1f}/100", fontsize=11)
            plt.text(0.8, y_pos, recommendation, fontsize=11, color=color)
            y_pos -= 0.04
            
            if i == 1:
                # Для лучшего КП даем развернутую рекомендацию
                y_pos -= 0.02
                plt.text(0.1, y_pos, f"Рекомендация:", fontsize=12, fontweight='bold')
                y_pos -= 0.04
                plt.text(0.1, y_pos, f"Предложение от '{company}' является наиболее подходящим с общей оценкой {score:.1f}/100.", 
                         fontsize=10, wrap=True)
                y_pos -= 0.04
        
        plt.text(0.1, 0.1, "Примечание: Данный отчет сгенерирован автоматически и носит рекомендательный характер.", 
                 fontsize=9, fontstyle='italic')
        pdf.savefig()
        plt.close()
    
    # Возвращаем буфер в начальную позицию
    buffer.seek(0)
    return buffer

def render_comparison_table():
    """
    Отображает сравнительную таблицу всех коммерческих предложений
    и позволяет выбрать КП для детального отчета с помощью кнопок.
    """
    if "all_analysis_results" not in st.session_state or not st.session_state.all_analysis_results:
        st.warning("Нет данных для сравнения. Пожалуйста, запустите анализ.")
        # Добавим кнопку для возврата к загрузке, если данных нет
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Вернуться к загрузке файлов", use_container_width=True, key="comp_back_to_upload"):
                st.session_state.current_step = "upload"
                st.rerun()
        return
    
    st.header("Сравнительная таблица коммерческих предложений")

    # Если у нас более одного КП, предлагаем сформировать сравнительный анализ
    all_analyses = st.session_state.all_analysis_results
    
    if len(all_analyses) >= 2:
        with st.expander("📊 **Сравнительный анализ всех КП**", expanded=True):
            # Кнопка для формирования или обновления анализа
            if "comparison_analysis" not in st.session_state:
                st.session_state.comparison_analysis = None
                
            col1, col2, col3 = st.columns([2, 1, 1])
            with col2:
                if st.button("Сформировать анализ", use_container_width=True, key="run_comparison_analysis"):
                    st.session_state.comparison_analysis = compare_all_proposals(all_analyses)
            
            with col3:
                if st.button("Аналитический отчет", use_container_width=True, key="run_analytical_report"):
                    st.session_state.comparison_analysis = generate_analytical_report(all_analyses)
            
            # Если анализ уже был сформирован, отображаем его
            if st.session_state.comparison_analysis:
                st.markdown(st.session_state.comparison_analysis, unsafe_allow_html=True)
            else:
                st.markdown("Нажмите кнопку 'Сформировать анализ' или 'Аналитический отчет', чтобы получить результаты сравнения всех КП.")
    
    st.divider()
    
    # Сначала добавим заметную инструкцию
    st.info("👇 **Чтобы увидеть подробный отчет по конкретной компании, нажмите на соответствующую кнопку ниже.**")
    
    # Сначала отображаем крупные кнопки для быстрого доступа к отчетам
    st.subheader("Быстрый доступ к отчетам")
    
    # Расположим кнопки в несколько столбцов
    cols_per_row = 4
    
    for i in range(0, len(all_analyses), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(all_analyses):
                analysis = all_analyses[i + j]
                company = analysis.get("company_name", analysis["kp_name"])
                compliance = analysis["comparison_result"]["compliance_score"]
                
                # Определяем цвет кнопки на основе соответствия
                if compliance >= 80:
                    btn_color = "🟢"
                elif compliance >= 60:
                    btn_color = "🟡"
                else:
                    btn_color = "🔴"
                    
                with cols[j]:
                    if st.button(f"{btn_color} Отчет: {company}\n{compliance}% соотв.", 
                                 key=f"quick_report_{i+j}",
                                 use_container_width=True):
                        st.session_state.analysis_result = analysis
                        st.session_state.current_step = "report"
                        st.rerun()
    
    st.divider()
    
    # Создаем данные для таблицы
    table_data = []
    kp_names = []
    
    for analysis in st.session_state.all_analysis_results:
        kp_name = analysis["kp_name"]
        company_name = analysis.get("company_name", kp_name)  # Используем company_name, если есть
        kp_names.append(kp_name)  # Сохраняем имя файла для ключа
        
        # Базовая информация
        kp_info = {
            "Название компании": company_name,  # Используем название компании
            "Соответствие (%)": analysis["comparison_result"]["compliance_score"],
            "Стоимость": analysis.get("pricing", "Не указана"),      # Новое поле
            "Сроки": analysis.get("timeline", "Не указаны"),         # Новое поле
            "Пропущено": len(analysis["comparison_result"]["missing_requirements"]),
            "Добавлено": len(analysis["comparison_result"]["additional_features"])
        }
        
        # Расчет среднего рейтинга (если есть)
        ratings = analysis.get("ratings", {})
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0
        kp_info["Рейтинг (1-10)"] = round(avg_rating, 1)
        
        # Добавляем рекомендацию
        compliance_score = kp_info["Соответствие (%)"]
        overall_score = (avg_rating * 10 + compliance_score) / 2
        
        if overall_score >= 75:
            kp_info["Рекомендация"] = "✅ Рекомендовано"
        elif overall_score >= 60:
            kp_info["Рекомендация"] = "⚠️ С оговорками"
        else:
            kp_info["Рекомендация"] = "❌ Не рекомендовано"
            
        # Добавляем столбец для кнопки отчета
        # kp_info["Открыть отчет"] = "📊 Открыть детальный отчет"  # Изменяем текст
        kp_info["kp_key"] = kp_name # Добавляем скрытый ключ для идентификации КП
        
        table_data.append(kp_info)
    
    # Для более компактного отображения, преобразуем данные таблицы
    # Сокращаем форматы строк для Стоимости и Сроков, обеспечивая перенос
    for item in table_data:
        # Очищаем стоимость от лишнего текста
        if "Фиксированная цена:" in item["Стоимость"]:
            price_parts = item["Стоимость"].split(":")
            item["Стоимость"] = price_parts[1].strip() if len(price_parts) > 1 else item["Стоимость"]
        
        # Преобразуем длинные строки с добавлением переносов
        if len(item["Стоимость"]) > 30:
            # Добавляем пробелы в длинных числах для облегчения переноса
            item["Стоимость"] = item["Стоимость"].replace(" ", "\n")
        
        # Аналогично для сроков
        if ":" in item["Сроки"]:
            timeline_parts = item["Сроки"].split(":")
            item["Сроки"] = timeline_parts[1].strip() if len(timeline_parts) > 1 else item["Сроки"]
    
    # Создаем DataFrame
    comparison_df = pd.DataFrame(table_data)
    
    # Отображаем таблицу без колонки ButtonColumn - улучшенная версия с компактными колонками
    st.markdown("""
    <div style='background-color: white; padding: 15px 20px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); margin-bottom: 20px;'>
        <h3 style='margin:0 0 10px 0; color: #1A1E3A; font-size: 1.1rem;'>📊 Сравнительная таблица коммерческих предложений</h3>
        <p style='color: #64748B; font-size: 0.9rem; margin: 0 0 15px 0;'>Сводные данные по всем КП для итогового сравнения</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.dataframe(
        comparison_df,
        column_config={
            "Название компании": st.column_config.TextColumn(
                "Компания", 
                width="medium",
                help="Название компании, предоставившей КП"
            ),
            "Соответствие (%)": st.column_config.ProgressColumn(
                "Соотв. (%)", 
                format="%d%%", 
                min_value=0, 
                max_value=100,
                width="small",
                help="Процент соответствия требованиям ТЗ"
            ),
            "Стоимость": st.column_config.TextColumn(
                "Цена", 
                width="medium",
                help="Предложенная стоимость работ"
            ),
            "Сроки": st.column_config.TextColumn(
                "Сроки", 
                width="medium",
                help="Предложенные сроки реализации"
            ),
            "Рейтинг (1-10)": st.column_config.ProgressColumn(
                "Рейтинг", 
                format="%.1f", 
                min_value=0, 
                max_value=10,
                width="small",
                help="Средний рейтинг по всем критериям (1-10)"
            ),
            "Пропущено": st.column_config.NumberColumn(
                "Упущено", 
                format="%d",
                width="small",
                help="Количество пропущенных требований ТЗ"
            ),
            "Добавлено": st.column_config.NumberColumn(
                "Добавл.", 
                format="%d",
                width="small",
                help="Количество дополнительных функций"
            ),
            "Рекомендация": st.column_config.TextColumn(
                "Итог", 
                width="small",
                help="Итоговая рекомендация на основе анализа"
            ),
            "kp_key": None
        },
        hide_index=True,
        use_container_width=True,
        height=280, # Фиксированная высота для компактности
        column_order=["Название компании", "Соответствие (%)", "Стоимость", "Сроки", "Рейтинг (1-10)", "Пропущено", "Добавлено", "Рекомендация"],
        key="comparison_table_df_no_button" # Меняем ключ, чтобы избежать конфликтов
    )
    
    # Добавляем кнопку для сохранения сравнительной таблицы в PDF
    save_col1, save_col2, save_col3 = st.columns([3, 2, 3])
    with save_col2:
        if st.button("📄 Сохранить таблицу в PDF", use_container_width=True, key="save_comparison_table"):
            st.info("Подготовка PDF-файла с таблицей сравнения...")
            try:
                # Генерируем PDF
                pdf_buffer = export_comparison_to_pdf(comparison_df, all_analyses)
                
                # Кодируем PDF в base64 для скачивания
                b64 = base64.b64encode(pdf_buffer.read()).decode()
                
                # Создаем ссылку для скачивания
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"tender_comparison_{now}.pdf"
                
                st.success("PDF успешно сгенерирован!")
                
                # Отображаем ссылку для скачивания
                href = f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">📥 Скачать PDF файл</a>'
                st.markdown(href, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Ошибка при создании PDF: {e}")
    
    st.divider()
    
    # --- Визуализации остаются ниже --- 
    
    # Сравнение общего соответствия и среднего рейтинга
    st.subheader("Сводная оценка по компаниям", anchor=False)
    
    if len(table_data) > 0:
        summary_data = comparison_df[["Название компании", "Соответствие (%)", "Рейтинг (1-10)"]]
        
        # Для более компактного отображения, сокращаем длинные названия компаний
        summary_data["Название компании"] = summary_data["Название компании"].apply(
            lambda x: x[:20] + '...' if len(x) > 20 else x
        )
        
        summary_data_melted = pd.melt(
            summary_data, 
            id_vars=["Название компании"],
            var_name="Показатель", 
            value_name="Значение"
        )
        
        # Нормализуем оценки - рейтинг умножаем на 10
        summary_data_melted["Значение"] = np.where(
            summary_data_melted["Показатель"] == "Рейтинг (1-10)", 
            summary_data_melted["Значение"] * 10, 
            summary_data_melted["Значение"]
        )
        
        # Меняем название показателя для легенды
        summary_data_melted["Показатель"] = np.where(
            summary_data_melted["Показатель"] == "Рейтинг (1-10)",
            "Рейтинг (норм. до 100)",
            summary_data_melted["Показатель"]
        )

        fig = px.bar(
            summary_data_melted, 
            x="Название компании", 
            y="Значение", 
            color="Показатель",
            barmode="group",
            height=350, # Уменьшаем высоту графика для компактности
            color_discrete_map={
                "Соответствие (%)": settings.BRAND_COLORS["primary"],
                "Рейтинг (норм. до 100)": settings.BRAND_COLORS["accent"]
            }
        )
        
        fig.update_layout(
            xaxis_title="Компания",
            yaxis_title="Оценка (0-100)",
            legend_title="Показатель",
            yaxis=dict(range=[0, 100]),
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=40, b=80)  # Компактные отступы
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Кнопки управления
    st.divider()
    # Убираем кнопку "Вернуться к анализу", так как анализ теперь автоматический
    # col1, col2 = st.columns(2)
    # with col1: ...
    
    col1, col2, col3 = st.columns([1, 2, 1]) # Центрируем кнопку
    with col2:
        if st.button("🔄 Загрузить новые файлы / Начать новый анализ", use_container_width=True, key="comp_restart_btn_new"):
            # Сбрасываем состояние сессии для нового анализа
            st.session_state.uploaded_files = {
                "tz_file": None,
                "kp_files": [],
                "additional_files": []
            }
            st.session_state.analysis_result = None
            st.session_state.all_analysis_results = []
            st.session_state.ratings = {}
            st.session_state.comments = {}
            st.session_state.run_full_analysis = False
            st.session_state.current_step = "upload"
            st.rerun() 