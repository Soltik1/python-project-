import streamlit as st
from core.data_loader import load_seed
from core import frp

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

# 🎨 Красивые стили
st.markdown(
    """
    <style>
    /* Умеренная ширина контейнера: шире дефолта, но не во всю ширину */
    .block-container{max-width: 1200px !important; padding-left: 24px; padding-right: 24px;}
    @media (min-width: 1600px){ .block-container{ max-width: 1320px !important; } }
    @media (max-width: 800px){ .block-container{ padding-left: 16px; padding-right: 16px; } }

    :root{
        /* Тёмная палитра с тёплыми акцентами */
        --bg:#0f1115;          /* общий фон */
        --card:#1b1f2a;        /* фон карточек */
        --text:#e9ecef;        /* основной светлый текст */
        --muted:#9aa4b2;       /* вторичный текст */
        --brand:#d97706;       /* тёплый оранжевый */
        --brand-700:#b45309;   /* активы */
        --brand-50:rgba(217,119,6,0.14); /* мягкая подсветка */
        --success:#22c55e;
        --warning:#f59e0b;
        --danger:#ef4444;
        --info:#60a5fa;
        --radius:12px;
        --shadow:0 8px 20px rgba(0,0,0,0.35);
        --border:#2a2f3a;
        --input:#111827;
    }

    .main {
        background: radial-gradient(1200px 800px at 85% 110%, rgba(217,119,6,0.15) 0%, var(--bg) 55%)
                    ,linear-gradient(180deg, var(--bg), var(--bg));
        font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
        color: var(--text);
    }

    /* Заголовки чуть теплее и дружелюбнее */
    h1, h2, h3 { letter-spacing: 0.2px; }
    h1 { font-weight: 800; }

    /* Карточка проекта в тёплом тоне */
    .project-card {
        padding: 16px 18px;
        border-radius: var(--radius);
        margin: 10px 0;
        background: linear-gradient(135deg, var(--brand-50) 0%, rgba(255,255,255,0.02) 100%);
        color: var(--text);
        font-weight: 700;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }

    /* Блоки задач выглядят как спокойные карточки */
    .task-table{ 
        background: var(--card);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: calc(var(--radius) - 4px);
        padding: 12px 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    }
    .task-table td { padding: 6px 10px; }

    /* Цвета статусов и приоритетов в палитре */
    .status-todo { color: var(--muted); font-weight: 700; }
    .status-in_progress { color: var(--warning); font-weight: 700; }
    .status-review { color: var(--info); font-weight: 700; }
    .status-done { color: var(--success); font-weight: 700; }
    .priority-low { color: var(--muted); }
    .priority-medium { color: var(--warning); }
    .priority-high { color: var(--danger); }
    .priority-critical { color: #7c2d12; font-weight: 800; }

    /* Дружелюбные кнопки */
    .stButton>button{
        background: var(--brand);
        color: #fff;
        border: none;
        padding: 0.55rem 0.9rem;
        border-radius: 999px;
        box-shadow: 0 8px 20px rgba(217,119,6,0.25);
        font-weight: 700;
        transition: transform .05s ease, background .15s ease;
    }
    .stButton>button:hover{ background: var(--brand-700); transform: translateY(-1px); }
    .stButton>button:active{ transform: translateY(0); }

    /* Элементы форм слегка скруглены */
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div{
        border-radius: 10px !important;
        background: var(--input) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
    }
    .stSelectbox div[data-baseweb="select"]>div{ background: var(--input) !important; }
    ::placeholder{ color: var(--muted) !important; opacity: 1; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🍕 Трекер задач | Учебный проект")

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

# --- Блок проектов ---
st.subheader("📂 Проекты")
for proj in projects:
    st.markdown(f"<div class='project-card'>📁 {proj.name} (Владелец: {proj.owner})</div>", unsafe_allow_html=True)

# --- Фильтры задач ---
st.subheader("🗂️ Задачи")
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

# --- Таблица задач ---
st.markdown("### 📋 Список задач")
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
        <hr>
        """,
        unsafe_allow_html=True
    )

# --- События ---
st.subheader("🔔 События")
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

# --- Создание новой задачи ---
st.subheader("➕ Создать задачу")
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
