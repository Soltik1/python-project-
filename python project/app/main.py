import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.data_loader import load_seed
from core import frp
from core.transforms import (
    add_task, filter_by_status, avg_tasks_per_user,
    by_priority, by_assignee, by_date_range,
    walk_comments, traverse_tasks,
    overdue_tasks, measure_cache_performance,
    safe_task, validate_task, create_task_pipeline
)
from core.report import (
    overview_stats, project_overview_report, filtered_tasks_report,
    user_workload_report, overdue_tasks_report_cached, performance_comparison_report,
    safe_task_report, validation_report, pipeline_report, generate_summary_report
)
from core.ftypes import Maybe, Some, Nothing, Either, Right, Left
from core.domain import Task
import datetime

# Загружаем данные
projects, users, tasks, comments = load_seed()

# Инициализация EventBus в session_state
if "bus" not in st.session_state:
    st.session_state.bus = frp.EventBus()
    st.session_state.events = []

    def log_event(ev):
        st.session_state.events.append(ev)

    st.session_state.bus.subscribe("task_created", log_event)
    st.session_state.bus.subscribe("task_updated", log_event)

# Инициализация текущей страницы
if "current_page" not in st.session_state:
    st.session_state.current_page = "проекты"

# 🎨 Стили с фиксированной боковой панелью
st.markdown(
    """
    <style>
    /* Основные переменные */
    :root{
        --bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --bg-solid: #667eea;
        --sidebar-bg: rgba(255,255,255,0.1);
        --card: rgba(255,255,255,0.95);
        --card-hover: rgba(255,255,255,1);
        --text: #2d3748;
        --text-light: #4a5568;
        --muted: #718096;
        --brand: #4299e1;
        --brand-700: #2b6cb0;
        --brand-50: rgba(66,153,225,0.1);
        --success: #48bb78;
        --warning: #ed8936;
        --danger: #f56565;
        --info: #4299e1;
        --radius: 16px;
        --shadow: 0 10px 25px rgba(0,0,0,0.15);
        --shadow-hover: 0 15px 35px rgba(0,0,0,0.2);
        --border: rgba(255,255,255,0.2);
        --input: rgba(255,255,255,0.9);
        --sidebar-width: 250px;
    }

    /* Основной контейнер */
    .main .block-container {
        max-width: 1200px !important;
        padding: 20px !important;
    }

    /* Основной фон */
    .main {
        background: var(--bg);
        background-attachment: fixed;
        color: var(--text);
        min-height: 100vh;
    }
    
    /* Дополнительный стиль для body */
    .stApp {
        background: var(--bg);
        background-attachment: fixed;
    }

    /* Карточки проектов */
    .project-card {
        padding: 20px 24px;
        border-radius: var(--radius);
        margin: 12px 0;
        background: var(--card);
        color: var(--text) !important;
        font-weight: 600;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .project-card:hover {
        background: var(--card-hover);
        box-shadow: var(--shadow-hover);
        transform: translateY(-2px);
    }

    /* Блоки задач */
    .task-table{ 
        background: var(--card);
        color: var(--text) !important;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 20px;
        box-shadow: var(--shadow);
        margin: 12px 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .task-table:hover {
        background: var(--card-hover);
        box-shadow: var(--shadow-hover);
        transform: translateY(-1px);
    }

    /* Цвета статусов и приоритетов */
    .status-todo { color: var(--muted) !important; font-weight: 600; }
    .status-in_progress { color: var(--warning) !important; font-weight: 600; }
    .status-review { color: var(--info) !important; font-weight: 600; }
    .status-done { color: var(--success) !important; font-weight: 600; }
    .priority-low { color: var(--muted) !important; font-weight: 500; }
    .priority-medium { color: var(--warning) !important; font-weight: 500; }
    .priority-high { color: var(--danger) !important; font-weight: 600; }
    .priority-critical { color: #e53e3e !important; font-weight: 700; }

    /* Кнопки */
    .stButton>button{
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-700) 100%);
        color: #fff;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 999px;
        box-shadow: var(--shadow);
        font-weight: 600;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }
    .stButton>button:hover{ 
        background: linear-gradient(135deg, var(--brand-700) 0%, #1a365d 100%); 
        transform: translateY(-2px); 
        box-shadow: var(--shadow-hover);
    }
    .stButton>button:active{ 
        transform: translateY(0); 
        box-shadow: var(--shadow);
    }

    /* Элементы форм */
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div{
        border-radius: var(--radius) !important;
        background: var(--input) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea textarea:focus,
    .stSelectbox>div>div:focus{
        border-color: var(--brand) !important;
        box-shadow: 0 0 0 3px var(--brand-50) !important;
    }
    .stSelectbox div[data-baseweb="select"]>div{ 
        background: var(--input) !important; 
        border-radius: var(--radius) !important;
    }
    ::placeholder{ color: var(--muted) !important; opacity: 1; }

    /* Скрываем стандартный сайдбар Streamlit */
    .css-1d391kg {display: none;}
    
    /* Дополнительные стили для улучшения внешнего вида */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--text) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stMarkdown h1 {
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-700) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* Стили для навигации */
    .stButton>button {
        margin: 4px;
        font-size: 0.9rem;
    }
    
    /* Стили для успешных сообщений */
    .stSuccess {
        background: linear-gradient(135deg, var(--success) 0%, #38a169 100%);
        color: white;
        border-radius: var(--radius);
        padding: 1rem;
        box-shadow: var(--shadow);
    }
    
    /* Стили для информационных сообщений */
    .stInfo {
        background: linear-gradient(135deg, var(--info) 0%, var(--brand-700) 100%);
        color: white;
        border-radius: var(--radius);
        padding: 1rem;
        box-shadow: var(--shadow);
    }
    
    /* Анимация появления карточек */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .project-card, .task-table {
        animation: fadeInUp 0.6s ease-out;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Справочники отображения
status_labels = {
    "todo": "К выполнению",
    "in_progress": "В работе",
    "review": "На проверке",
    "done": "Готово",
}

user_id_to_name = {u.id: u.name for u in users}

priority_labels = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
    "critical": "Критический",
}

# Локализация названий событий
event_name_labels = {
    "task_created": "Задача создана",
    "task_updated": "Задача обновлена",
}

# Функции для отображения страниц
def show_projects_page():
    st.markdown("### 📂 Проекты")
    for proj in projects:
        st.markdown(f"<div class='project-card'>📁 {proj.name} (Владелец: {proj.owner})</div>", unsafe_allow_html=True)

def show_tasks_page():
    st.markdown("### 🗂️ Задачи")
    filter_project = st.selectbox("Фильтр по проекту", ["Все"] + [p.name for p in projects])
    filter_status = st.selectbox(
        "Фильтр по статусу",
        ["Все", "todo", "in_progress", "review", "done"],
        format_func=lambda v: "Все" if v == "Все" else status_labels.get(v, v),
    )

    filtered_tasks = tasks
    if filter_project != "Все":
        proj_id = next(p.id for p in projects if p.name == filter_project)
        filtered_tasks = [t for t in filtered_tasks if t.project_id == proj_id]

    if filter_status != "Все":
        filtered_tasks = [t for t in filtered_tasks if t.status == filter_status]

    for task in filtered_tasks:
        st.markdown(
            f"""
            <div class="task-table">
                <b>{task.title}</b><br>
                <span class="status-{task.status}">Статус: {status_labels.get(task.status, task.status)}</span> | 
                <span class="priority-{task.priority}">Приоритет: {priority_labels.get(task.priority, task.priority)}</span><br>
                👤 Исполнитель: {user_id_to_name.get(task.assignee, "Не назначен") if task.assignee else "Не назначен"}<br>
                🕒 Создано: {task.created}
            </div>
            """,
            unsafe_allow_html=True
        )

def show_task_list_page():
    st.markdown("### 📋 Список задач")
    for task in tasks:
        st.markdown(
            f"""
            <div class="task-table">
                <b>{task.title}</b><br>
                <span class="status-{task.status}">Статус: {status_labels.get(task.status, task.status)}</span> | 
                <span class="priority-{task.priority}">Приоритет: {priority_labels.get(task.priority, task.priority)}</span><br>
                👤 Исполнитель: {user_id_to_name.get(task.assignee, "Не назначен") if task.assignee else "Не назначен"}<br>
                🕒 Создано: {task.created}
            </div>
            """,
            unsafe_allow_html=True
        )

def show_events_page():
    st.markdown("### 🔔 События")
    if st.session_state.events:
        for ev in reversed(st.session_state.events[-10:]):  # показываем последние 10
            payload = ev.payload
            if isinstance(payload, dict):
                title = payload.get("title") or payload.get("id") or ""
                desc = payload.get("desc") or payload.get("text") or ""
                status_key = payload.get("status")
                status_ru = status_labels.get(status_key, status_key) if status_key else None
                priority_key = payload.get("priority")
                priority_ru = priority_labels.get(priority_key, priority_key) if priority_key else None
                assignee_key = payload.get("assignee")
                assignee_name = user_id_to_name.get(assignee_key) if assignee_key else None

                lines = []
                if title:
                    lines.append(f"Название: {title}")
                if desc:
                    lines.append(f"Описание: {desc}")
                if status_ru:
                    lines.append(f"Статус: {status_ru}")
                if priority_ru:
                    lines.append(f"Приоритет: {priority_ru}")
                if assignee_name:
                    lines.append(f"Исполнитель: {assignee_name}")

                pretty = " | ".join(lines) if lines else str(payload)
                date_only = str(ev.ts).split("T")[0]
                event_ru = event_name_labels.get(ev.name, ev.name)
                st.markdown(f"**{date_only}** — {event_ru} → {pretty}")
            else:
                date_only = str(ev.ts).split("T")[0]
                event_ru = event_name_labels.get(ev.name, ev.name)
                st.markdown(f"**{date_only}** — {event_ru} → {payload}")
    else:
        st.info("Пока событий нет — создайте первую задачу.")

def show_create_task_page():
    st.markdown("### ➕ Создать задачу")
    with st.form("new_task"):
        title = st.text_input("Название задачи")
        desc = st.text_area("Описание")
        status = st.selectbox(
            "Статус",
            ["todo", "in_progress", "review", "done"],
            format_func=lambda v: status_labels.get(v, v),
        )
        priority = st.selectbox(
            "Приоритет",
            ["low", "medium", "high", "critical"],
            format_func=lambda v: priority_labels.get(v, v),
        )
        assignee = st.selectbox(
            "Исполнитель",
            [None] + [u.id for u in users],
            format_func=lambda v: "" if v is None else user_id_to_name.get(v, v),
        )
        submitted = st.form_submit_button("Создать задачу")

        if submitted and title:
            new_task = {
                "title": title,
                "desc": desc,
                "status": status,
                "priority": priority,
                "assignee": assignee if assignee else None
            }
            ev = st.session_state.bus.publish("task_created", new_task)
            st.success(f"✅ Задача '{title}' создана!")

# === Лабораторные работы ===

def show_lab1_overview_page():
    """Лаба #1: Чистые функции + иммутабельность + HOF - Overview"""
    st.markdown("### 📊 Лаба #1: Overview (Чистые функции + иммутабельность + HOF)")
    
    # Получаем статистику
    stats = overview_stats(projects, users, tasks)
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📂 Проекты", stats["projects_count"])
    
    with col2:
        st.metric("🗂️ Задачи", stats["tasks_count"])
    
    with col3:
        st.metric("👥 Пользователи", stats["users_count"])
    
    with col4:
        st.metric("📈 Среднее задач/пользователь", f"{stats['avg_tasks_per_user']:.1f}")
    
    # Распределение по статусам
    st.markdown("#### 📊 Распределение задач по статусам")
    status_dist = stats["status_distribution"]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 К выполнению", status_dist["todo"])
    with col2:
        st.metric("🔄 В работе", status_dist["in_progress"])
    with col3:
        st.metric("👀 На проверке", status_dist["review"])
    with col4:
        st.metric("✅ Готово", status_dist["done"])
    
    # Демонстрация чистых функций
    st.markdown("#### 🧪 Демонстрация чистых функций")
    
    if st.button("Показать задачи со статусом 'todo'"):
        todo_tasks = filter_by_status(tasks, "todo")
        st.write(f"Найдено задач со статусом 'todo': {len(todo_tasks)}")
        for task in todo_tasks[:5]:  # Показываем первые 5
            st.write(f"- {task.title}")

def show_lab2_filters_page():
    """Лаба #2: Лямбда и замыкания + рекурсия - Фильтры"""
    st.markdown("### 🔍 Лаба #2: Фильтры (Лямбда и замыкания + рекурсия)")
    
    # Фильтры через замыкания
    st.markdown("#### 🎯 Фильтры через замыкания")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        priority_filter = st.selectbox("Фильтр по приоритету", ["Все"] + list(set(t.priority for t in tasks)))
    
    with col2:
        assignee_filter = st.selectbox("Фильтр по исполнителю", ["Все"] + [u.id for u in users])
    
    with col3:
        if st.checkbox("Фильтр по дате"):
            start_date = st.date_input("Дата начала", datetime.date.today() - datetime.timedelta(days=30))
            end_date = st.date_input("Дата окончания", datetime.date.today())
        else:
            start_date = None
            end_date = None
    
    # Применяем фильтры
    filters = {}
    if priority_filter != "Все":
        filters["priority"] = priority_filter
    if assignee_filter != "Все":
        filters["assignee"] = assignee_filter
    if start_date and end_date:
        filters["date_range"] = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        }
    
    filtered = filtered_tasks_report(tasks, filters)
    
    st.markdown(f"#### 📋 Результаты фильтрации: {len(filtered)} задач")
    for task in filtered[:10]:  # Показываем первые 10
        st.markdown(f"- **{task.title}** | {task.status} | {task.priority}")
    
    # Демонстрация рекурсивных функций
    st.markdown("#### 🔄 Демонстрация рекурсивных функций")
    
    if st.button("Найти комментарии для первой задачи"):
        if tasks:
            task_comments = walk_comments(comments, tasks[0].id)
            st.write(f"Комментарии для задачи '{tasks[0].title}': {len(task_comments)}")
            for comment in task_comments:
                st.write(f"- {comment.text[:50]}...")
    
    if st.button("Обойти задачи в порядке статусов"):
        status_order = ("todo", "in_progress", "review", "done")
        task_ids = traverse_tasks(tasks, status_order)
        st.write(f"ID задач в порядке статусов: {task_ids[:10]}")

def show_lab3_reports_page():
    """Лаба #3: Продвинутая рекурсия + мемоизация - Reports"""
    st.markdown("### 📈 Лаба #3: Reports (Продвинутая рекурсия + мемоизация)")
    
    # Кэшированные отчеты
    st.markdown("#### 💾 Кэшированные отчеты")
    
    if st.button("Генерировать отчет просроченных задач"):
        rules = ("overdue_7_days", "critical_overdue")
        overdue = overdue_tasks_report_cached(tasks, rules)
        
        st.markdown(f"**Просроченных задач: {len(overdue)}**")
        for task in overdue:
            st.write(f"- {task.title} | {task.status} | {task.priority}")
    
    # Сравнение производительности
    st.markdown("#### ⚡ Сравнение производительности")
    
    if st.button("Измерить производительность кэша"):
        rules = ("overdue_7_days", "critical_overdue")
        perf = performance_comparison_report(tasks, rules)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Первый вызов (с)", f"{perf['first_call_time']:.4f}")
        with col2:
            st.metric("Второй вызов (с)", f"{perf['second_call_time']:.4f}")
        with col3:
            st.metric("Улучшение", f"{perf['cache_improvement']:.1f}x")
        
        st.success(f"Кэш ускорил выполнение в {perf['cache_improvement']:.1f} раз!")
    
    # Отчет по загрузке пользователей
    st.markdown("#### 👥 Загрузка пользователей")
    workload = user_workload_report(tasks, users)
    
    for user_name, stats in workload.items():
        with st.expander(f"👤 {user_name}"):
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Всего", stats["total"])
            with col2:
                st.metric("К выполнению", stats["todo"])
            with col3:
                st.metric("В работе", stats["in_progress"])
            with col4:
                st.metric("На проверке", stats["review"])
            with col5:
                st.metric("Готово", stats["done"])

def show_lab4_functional_patterns_page():
    """Лаба #4: Функциональные паттерны Maybe/Either"""
    st.markdown("### 🎭 Лаба #4: Функциональные паттерны (Maybe/Either)")
    
    # Демонстрация Maybe
    st.markdown("#### 🔍 Maybe Pattern")
    
    task_id = st.text_input("Введите ID задачи для поиска", "task1")
    
    if st.button("Найти задачу (Maybe)"):
        maybe_task = safe_task(tasks, task_id)
        
        if maybe_task.is_some():
            task = maybe_task.get_or_else(None)
            st.success(f"✅ Задача найдена: {task.title}")
            st.write(f"Статус: {task.status} | Приоритет: {task.priority}")
        else:
            st.error("❌ Задача не найдена")
    
    # Демонстрация Either - валидация
    st.markdown("#### ✅ Either Pattern - Валидация")
    
    if st.button("Валидировать все задачи"):
        rules = ("title_min_length", "desc_min_length", "assignee_required")
        validation_results = validation_report(tasks, rules)
        
        valid_count = 0
        invalid_count = 0
        
        for task_id, result in list(validation_results.items())[:10]:  # Первые 10
            if result.is_right():
                valid_count += 1
                st.success(f"✅ {task_id}: Валидна")
            else:
                invalid_count += 1
                errors = result.map_left(lambda x: x).get_or_else({"errors": []})
                st.error(f"❌ {task_id}: {errors.get('errors', [])}")
        
        st.markdown(f"**Результаты валидации:** {valid_count} валидных, {invalid_count} с ошибками")
    
    # Демонстрация пайплайна
    st.markdown("#### 🔄 Pipeline Pattern")
    
    if st.button("Создать тестовую задачу через пайплайн"):
        # Создаем тестовую задачу
        new_task = Task(
            id="test_task",
            project_id="proj1",
            title="Тестовая задача",
            desc="Описание тестовой задачи для демонстрации пайплайна",
            status="todo",
            priority="medium",
            assignee="user1",
            created=datetime.datetime.now().isoformat(),
            updated=datetime.datetime.now().isoformat()
        )
        
        rules = ("title_min_length", "desc_min_length")
        result = create_task_pipeline(tasks, new_task, rules)
        
        if result.is_right():
            st.success("✅ Задача успешно создана через пайплайн!")
            st.write("Пайплайн: создать → валидировать → сохранить")
        else:
            errors = result.map_left(lambda x: x).get_or_else({"errors": []})
            st.error(f"❌ Ошибка в пайплайне: {errors.get('errors', [])}")

def show_about_page():
    st.markdown("### ℹ️ О нас")
    st.markdown("""
    **Трекер задач | Учебный проект**
    
    Это учебное приложение для управления задачами и проектами, созданное с использованием:
    - **Streamlit** - для веб-интерфейса
    - **Python** - для бэкенд логики
    - **EventBus** - для системы событий
    
    **Функции:**
    - 📂 Управление проектами
    - 🗂️ Создание и отслеживание задач
    - 🔔 Система событий
    - 📊 Фильтрация и поиск
    - 👥 Назначение исполнителей
    
    **Лабораторные работы:**
    - **Лаба #1**: Чистые функции + иммутабельность + HOF
    - **Лаба #2**: Лямбда и замыкания + рекурсия
    - **Лаба #3**: Продвинутая рекурсия + мемоизация
    - **Лаба #4**: Функциональные паттерны Maybe/Either
    
    **Статусы задач:**
    - К выполнению
    - В работе
    - На проверке
    - Готово
    
    **Приоритеты:**
    - Низкий
    - Средний
    - Высокий
    - Критический

    **Разработчики:**
    - (Бэк) Белялов Д.Р.
    - (Бэк + фронт) Пак Н.В.
    """)

# Заголовок приложения
st.title("Трекер задач | Учебный проект")

# Простая навигация
st.markdown("### 🧭 Навигация")

# Кнопки навигации - основные функции
st.markdown("#### 🔧 Основные функции")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    if st.button("📂 Проекты", key="nav_projects", use_container_width=True):
        st.session_state.current_page = "проекты"

with col2:
    if st.button("🗂️ Задачи", key="nav_tasks", use_container_width=True):
        st.session_state.current_page = "задачи"

with col3:
    if st.button("📋 Список задач", key="nav_task_list", use_container_width=True):
        st.session_state.current_page = "список задач"

with col4:
    if st.button("🔔 События", key="nav_events", use_container_width=True):
        st.session_state.current_page = "события"

with col5:
    if st.button("➕ Создать задачу", key="nav_create", use_container_width=True):
        st.session_state.current_page = "создать задачу"

with col6:
    if st.button("ℹ️ О нас", key="nav_about", use_container_width=True):
        st.session_state.current_page = "о нас"

# Кнопки навигации - лабораторные работы
st.markdown("#### 🧪 Лабораторные работы")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 Лаба #1: Overview", key="nav_lab1", use_container_width=True):
        st.session_state.current_page = "lab1_overview"

with col2:
    if st.button("🔍 Лаба #2: Фильтры", key="nav_lab2", use_container_width=True):
        st.session_state.current_page = "lab2_filters"

with col3:
    if st.button("📈 Лаба #3: Reports", key="nav_lab3", use_container_width=True):
        st.session_state.current_page = "lab3_reports"

with col4:
    if st.button("🎭 Лаба #4: Maybe/Either", key="nav_lab4", use_container_width=True):
        st.session_state.current_page = "lab4_functional_patterns"

st.markdown("---")

# Отображаем соответствующую страницу
if st.session_state.current_page == "проекты":
    show_projects_page()
elif st.session_state.current_page == "задачи":
    show_tasks_page()
elif st.session_state.current_page == "список задач":
    show_task_list_page()
elif st.session_state.current_page == "события":
    show_events_page()
elif st.session_state.current_page == "создать задачу":
    show_create_task_page()
elif st.session_state.current_page == "lab1_overview":
    show_lab1_overview_page()
elif st.session_state.current_page == "lab2_filters":
    show_lab2_filters_page()
elif st.session_state.current_page == "lab3_reports":
    show_lab3_reports_page()
elif st.session_state.current_page == "lab4_functional_patterns":
    show_lab4_functional_patterns_page()
elif st.session_state.current_page == "о нас":
    show_about_page()
