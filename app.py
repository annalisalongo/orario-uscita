from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, time
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Orario di Uscita", page_icon="🕒", layout="centered")

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PLANS_CSV = DATA_DIR / "agile_plan.csv"
LOGS_CSV = DATA_DIR / "week_log.csv"

WORK_DURATION = timedelta(hours=7, minutes=38)
MIN_EXIT_TIME = time(hour=16, minute=38)
DAY_NAMES = {
    0: "Lunedì",
    1: "Martedì",
    2: "Mercoledì",
    3: "Giovedì",
    4: "Venerdì",
    5: "Sabato",
    6: "Domenica",
}


def ensure_csv(path: Path, headers: list[str]) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


ensure_csv(PLANS_CSV, ["date", "mode", "updated_at"])
ensure_csv(LOGS_CSV, ["date", "start_time", "pause_minutes", "work_mode", "theoretical_exit", "final_exit", "updated_at"])


def read_csv(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.DataFrame()
    return df


def parse_manual_time(text: str) -> time:
    return datetime.strptime(text.strip(), "%H:%M").time()


def combine_day_and_time(d: date, t: time) -> datetime:
    return datetime.combine(d, t)


def current_week_bounds(anchor: date | None = None) -> tuple[date, date]:
    if anchor is None:
        anchor = date.today()
    monday = anchor - timedelta(days=anchor.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def save_plan(plan_date: date, mode: str) -> None:
    df = read_csv(PLANS_CSV)
    if df.empty:
        df = pd.DataFrame(columns=["date", "mode", "updated_at"])

    date_str = plan_date.isoformat()
    now_str = datetime.now().isoformat(timespec="seconds")

    row = {"date": date_str, "mode": mode, "updated_at": now_str}

    if "date" in df.columns and (df["date"] == date_str).any():
        df.loc[df["date"] == date_str, ["mode", "updated_at"]] = [mode, now_str]
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    df = df.sort_values("date")
    df.to_csv(PLANS_CSV, index=False)


def save_log(log_date: date, start_t: time, pause_minutes: int, work_mode: str, theoretical_exit: time, final_exit: time) -> None:
    df = read_csv(LOGS_CSV)
    if df.empty:
        df = pd.DataFrame(columns=["date", "start_time", "pause_minutes", "work_mode", "theoretical_exit", "final_exit", "updated_at"])

    date_str = log_date.isoformat()
    now_str = datetime.now().isoformat(timespec="seconds")

    row = {
        "date": date_str,
        "start_time": start_t.strftime("%H:%M"),
        "pause_minutes": pause_minutes,
        "work_mode": work_mode,
        "theoretical_exit": theoretical_exit.strftime("%H:%M"),
        "final_exit": final_exit.strftime("%H:%M"),
        "updated_at": now_str,
    }

    if "date" in df.columns and (df["date"] == date_str).any():
        for key, value in row.items():
            df.loc[df["date"] == date_str, key] = value
    else:
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    df = df.sort_values("date")
    df.to_csv(LOGS_CSV, index=False)


def get_plan_for_day(target_date: date) -> str:
    df = read_csv(PLANS_CSV)
    if df.empty or "date" not in df.columns:
        return "Non impostato"
    row = df[df["date"] == target_date.isoformat()]
    if row.empty:
        return "Non impostato"
    return str(row.iloc[-1]["mode"])


def get_log_for_day(target_date: date) -> dict | None:
    df = read_csv(LOGS_CSV)
    if df.empty or "date" not in df.columns:
        return None
    row = df[df["date"] == target_date.isoformat()]
    if row.empty:
        return None
    return row.iloc[-1].to_dict()


def build_week_summary(anchor: date | None = None) -> pd.DataFrame:
    monday, sunday = current_week_bounds(anchor)
    dates = [monday + timedelta(days=i) for i in range(7)]

    plans = read_csv(PLANS_CSV)
    logs = read_csv(LOGS_CSV)

    if plans.empty:
        plans = pd.DataFrame(columns=["date", "mode"])
    if logs.empty:
        logs = pd.DataFrame(columns=["date", "start_time", "pause_minutes", "final_exit"])

    rows = []
    for d in dates:
        d_str = d.isoformat()

        plan_mode = "Non impostato"
        if "date" in plans.columns and (plans["date"] == d_str).any():
            plan_mode = str(plans.loc[plans["date"] == d_str, "mode"].iloc[-1])

        start_time = ""
        pause = ""
        exit_time = ""
        if "date" in logs.columns and (logs["date"] == d_str).any():
            log_row = logs.loc[logs["date"] == d_str].iloc[-1]
            start_time = str(log_row.get("start_time", ""))
            pause_min = str(log_row.get("pause_minutes", ""))
            pause = f"{pause_min} min" if pause_min else ""
            exit_time = str(log_row.get("final_exit", ""))

        rows.append(
            {
                "Giorno": DAY_NAMES[d.weekday()],
                "Data": d.strftime("%d/%m/%Y"),
                "Modalità": plan_mode,
                "Ingresso": start_time,
                "Pausa": pause,
                "Uscita": exit_time,
            }
        )

    return pd.DataFrame(rows)


def style_page() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
        .title {font-size: 2.1rem; font-weight: 800; margin-bottom: 0.2rem;}
        .subtitle {color: #6b7280; margin-bottom: 1rem;}
        .card {
            border: 1px solid rgba(120,120,120,0.18);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: rgba(255,255,255,0.60);
            box-shadow: 0 8px 22px rgba(0,0,0,0.04);
            margin-top: 0.8rem;
        }
        .result-time {font-size: 2.2rem; font-weight: 800; margin: 0.2rem 0;}
        .soft {color: #6b7280; font-size: 0.95rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def app_header() -> None:
    st.markdown('<div class="title">🕒 Orario di uscita</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Inserisci l’inizio della giornata, scegli la pausa e pianifica il lavoro agile anche in anticipo.</div>',
        unsafe_allow_html=True,
    )


def monday_reminder() -> None:
    today = date.today()
    if today.weekday() != 0:
        return

    monday, sunday = current_week_bounds(today)
    plans = read_csv(PLANS_CSV)
    covered = 0
    if not plans.empty and "date" in plans.columns:
        week_dates = {(monday + timedelta(days=i)).isoformat() for i in range(5)}
        covered = int(plans["date"].isin(week_dates).sum())

    if covered < 5:
        st.info("Promemoria del lunedì: imposta il lavoro agile della settimana qui sotto.")


def planner_section() -> None:
    st.subheader("Pianifica lavoro agile")
    col1, col2 = st.columns([1, 1])

    with col1:
        plan_date = st.date_input("Data da pianificare", value=date.today(), format="DD/MM/YYYY", key="plan_date")

    existing_plan = get_plan_for_day(plan_date)

    with col2:
        plan_mode = st.selectbox(
            "Modalità",
            options=["Lavoro agile", "Presenza", "Non impostato"],
            index=["Lavoro agile", "Presenza", "Non impostato"].index(existing_plan if existing_plan in ["Lavoro agile", "Presenza", "Non impostato"] else "Non impostato"),
            key="plan_mode",
        )

    if st.button("Salva pianificazione", use_container_width=True):
        save_plan(plan_date, plan_mode)
        st.success(f"Pianificazione salvata per {plan_date.strftime('%d/%m/%Y')}.")


def time_input_section(selected_date: date) -> time:
    mode = st.radio(
        "Come vuoi inserire l’orario?",
        options=["Scrivo a mano", "Seleziono"],
        horizontal=True,
        key="input_mode",
    )

    saved_log = get_log_for_day(selected_date)
    default_time = time(hour=9, minute=15)
    if saved_log and saved_log.get("start_time"):
        try:
            default_time = parse_manual_time(str(saved_log["start_time"]))
        except Exception:
            default_time = time(hour=9, minute=15)

    if mode == "Scrivo a mano":
        manual_default = default_time.strftime("%H:%M")
        start_text = st.text_input(
            "Orario di inizio",
            value=manual_default,
            placeholder="09:15",
            help="Formato HH:MM",
            key="manual_time",
        )
        start_t = parse_manual_time(start_text)
    else:
        start_t = st.time_input(
            "Orario di inizio",
            value=default_time,
            step=300,
            key="picker_time",
        )

    return start_t


def calculator_section() -> None:
    st.subheader("Calcola uscita")
    selected_date = st.date_input("Data del calcolo", value=date.today(), format="DD/MM/YYYY", key="calc_date")

    plan_for_day = get_plan_for_day(selected_date)
    if plan_for_day != "Non impostato":
        st.caption(f"Per questa data hai impostato: **{plan_for_day}**")

    try:
        start_t = time_input_section(selected_date)
    except ValueError:
        st.error("Formato orario non valido. Usa HH:MM, per esempio 09:15.")
        return

    saved_log = get_log_for_day(selected_date)
    pause_default = 30
    if saved_log and str(saved_log.get("pause_minutes", "")) in {"30", "60"}:
        pause_default = int(saved_log["pause_minutes"])

    pause_label = st.radio(
        "Pausa pranzo",
        options=["30 minuti", "1 ora"],
        index=0 if pause_default == 30 else 1,
        horizontal=True,
        key="pause_choice",
    )
    pause_minutes = 30 if pause_label == "30 minuti" else 60

    work_mode_for_log = st.selectbox(
        "Modalità per questo giorno",
        options=["Lavoro agile", "Presenza", "Non impostato"],
        index=["Lavoro agile", "Presenza", "Non impostato"].index(plan_for_day if plan_for_day in ["Lavoro agile", "Presenza", "Non impostato"] else "Non impostato"),
        key="calc_work_mode",
        help="Puoi modificarla qui anche se l’avevi già pianificata prima.",
    )

    if st.button("Calcola e salva", type="primary", use_container_width=True):
        pause_td = timedelta(minutes=pause_minutes)
        start_dt = combine_day_and_time(selected_date, start_t)
        min_exit_dt = combine_day_and_time(selected_date, MIN_EXIT_TIME)

        theoretical_exit_dt = start_dt + WORK_DURATION + pause_td
        final_exit_dt = max(theoretical_exit_dt, min_exit_dt)

        save_plan(selected_date, work_mode_for_log)
        save_log(
            selected_date,
            start_t,
            pause_minutes,
            work_mode_for_log,
            theoretical_exit_dt.time(),
            final_exit_dt.time(),
        )

        st.markdown(
            f"""
            <div class="card">
                <div class="soft">Puoi staccare alle</div>
                <div class="result-time">{final_exit_dt.strftime("%H:%M")}</div>
                <div class="soft">Calcolo: ingresso + 7:38 + pausa</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Uscita teorica", theoretical_exit_dt.strftime("%H:%M"))
        c2.metric("Uscita minima", MIN_EXIT_TIME.strftime("%H:%M"))
        c3.metric("Modalità", work_mode_for_log)

        if final_exit_dt > theoretical_exit_dt:
            st.info(
                f"L’orario teorico sarebbe {theoretical_exit_dt.strftime('%H:%M')}, "
                f"ma non puoi uscire prima delle {MIN_EXIT_TIME.strftime('%H:%M')}."
            )
        else:
            st.success("Orario calcolato e salvato nel riepilogo settimanale.")


def summary_section() -> None:
    st.subheader("Riepilogo della settimana")
    week_df = build_week_summary(date.today())
    st.dataframe(week_df, use_container_width=True, hide_index=True)


def main() -> None:
    style_page()
    app_header()
    monday_reminder()
    planner_section()
    st.divider()
    calculator_section()
    st.divider()
    summary_section()


if __name__ == "__main__":
    main()
