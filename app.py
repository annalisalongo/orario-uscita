from __future__ import annotations

import csv
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List

import streamlit as st

st.set_page_config(
    page_title="Orario di uscita",
    page_icon="🕒",
    layout="centered",
)

ORE_LAVORO = 7
MINUTI_LAVORO = 38
USCITA_MINIMA = "16:38"
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "giornate.csv"
WEEKDAY_LABELS = [
    "Lunedì",
    "Martedì",
    "Mercoledì",
    "Giovedì",
    "Venerdì",
    "Sabato",
    "Domenica",
]



def inject_style() -> None:
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.15rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            letter-spacing: -0.02em;
        }
        .subtitle {
            color: #6b7280;
            margin-bottom: 1.1rem;
        }
        .result-card {
            padding: 1.2rem 1.4rem;
            border-radius: 20px;
            border: 1px solid rgba(120,120,120,0.16);
            background: linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,248,230,0.92));
            box-shadow: 0 8px 24px rgba(0,0,0,0.05);
            margin: 0.9rem 0 0.3rem 0;
        }
        .result-kicker {
            color: #7a6a45;
            font-size: 0.95rem;
        }
        .result-time {
            font-size: 2.3rem;
            font-weight: 900;
            margin: 0.18rem 0;
            color: #2f2a1f;
        }
        .muted-note {
            color: #6b7280;
            font-size: 0.95rem;
        }
        .week-card {
            padding: 0.9rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(120,120,120,0.14);
            background: rgba(255,255,255,0.66);
            margin-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def ensure_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["date", "weekday", "start", "pause_minutes", "agile", "theoretical_exit", "final_exit"],
            )
            writer.writeheader()



def load_records() -> List[Dict[str, str]]:
    ensure_storage()
    with DATA_FILE.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))



def upsert_record(record: Dict[str, str]) -> None:
    rows = load_records()
    updated = False
    for idx, row in enumerate(rows):
        if row["date"] == record["date"]:
            rows[idx] = record
            updated = True
            break
    if not updated:
        rows.append(record)
    rows.sort(key=lambda x: x["date"])

    with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["date", "weekday", "start", "pause_minutes", "agile", "theoretical_exit", "final_exit"],
        )
        writer.writeheader()
        writer.writerows(rows)



def parse_hhmm(value: str) -> datetime:
    return datetime.strptime(value, "%H:%M")



def format_time(value: datetime) -> str:
    return value.strftime("%H:%M")



def compute_exit(start_value: time, pause_minutes: int) -> Dict[str, str]:
    start_dt = datetime.combine(date.today(), start_value)
    work_delta = timedelta(hours=ORE_LAVORO, minutes=MINUTI_LAVORO)
    pause_delta = timedelta(minutes=pause_minutes)
    total_delta = work_delta + pause_delta

    theoretical_exit = start_dt + total_delta
    minimum_exit = parse_hhmm(USCITA_MINIMA)
    minimum_exit = minimum_exit.replace(year=theoretical_exit.year, month=theoretical_exit.month, day=theoretical_exit.day)
    final_exit = max(theoretical_exit, minimum_exit)

    return {
        "theoretical_exit": format_time(theoretical_exit),
        "final_exit": format_time(final_exit),
        "total_duration": f"{int(total_delta.total_seconds() // 3600):02d}:{int((total_delta.total_seconds() // 60) % 60):02d}",
        "extra_block": str(final_exit - theoretical_exit) if final_exit > theoretical_exit else "00:00:00",
    }



def week_bounds(ref_day: date) -> tuple[date, date]:
    monday = ref_day - timedelta(days=ref_day.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday



def build_week_summary(records: List[Dict[str, str]], ref_day: date) -> List[Dict[str, str]]:
    monday, _ = week_bounds(ref_day)
    records_by_date = {row["date"]: row for row in records}
    summary: List[Dict[str, str]] = []

    for offset in range(7):
        current_day = monday + timedelta(days=offset)
        key = current_day.isoformat()
        row = records_by_date.get(key)
        summary.append(
            {
                "Giorno": f"{WEEKDAY_LABELS[current_day.weekday()]} {current_day.strftime('%d/%m')}",
                "Ingresso": row["start"] if row else "—",
                "Pausa": (f"{row['pause_minutes']} min" if row else "—"),
                "Agile": ("Sì" if row and row["agile"] == "True" else ("No" if row else "—")),
                "Uscita": row["final_exit"] if row else "—",
            }
        )
    return summary



def app_header() -> None:
    st.markdown('<div class="main-title">🕒 Orario di uscita</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Inserisci l’orario di inizio, scegli la pausa e salva la giornata. '
        'Il riepilogo della settimana resta sempre sotto.</div>',
        unsafe_allow_html=True,
    )



def render_reminder(selected_day: date) -> None:
    if selected_day.weekday() == 0:
        st.warning("Promemoria del lunedì: ricordati di inserire il lavoro agile della settimana.")



def main() -> None:
    inject_style()
    ensure_storage()
    app_header()

    today = date.today()
    default_start = time(hour=9, minute=15)

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_day = st.date_input("Giorno", value=today, format="DD/MM/YYYY")
        with col2:
            start_value = st.time_input("Orario di inizio", value=default_start, step=300)

        render_reminder(selected_day)

        col3, col4 = st.columns([1.2, 1])
        with col3:
            pause_label = st.radio("Pausa pranzo", ["30 minuti", "1 ora"], horizontal=True)
        with col4:
            agile = st.toggle("Lavoro agile", value=False)

        pause_minutes = 30 if pause_label == "30 minuti" else 60
        result = compute_exit(start_value, pause_minutes)

        st.caption(
            f"Lavoro fisso: {ORE_LAVORO}:{MINUTI_LAVORO:02d} · Pausa: {pause_minutes} min · Totale: {result['total_duration']}"
        )

    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-kicker">Puoi staccare alle</div>
            <div class="result-time">{result['final_exit']}</div>
            <div class="muted-note">Calcolo automatico: ingresso + 7:38 + pausa</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Uscita teorica", result["theoretical_exit"])
    m2.metric("Uscita minima", USCITA_MINIMA)
    m3.metric("Agile", "Sì" if agile else "No")

    if result["final_exit"] != result["theoretical_exit"]:
        st.info(
            f"L’orario teorico sarebbe {result['theoretical_exit']}, ma non puoi uscire prima delle {USCITA_MINIMA}."
        )

    if st.button("Salva giornata", use_container_width=True):
        record = {
            "date": selected_day.isoformat(),
            "weekday": WEEKDAY_LABELS[selected_day.weekday()],
            "start": start_value.strftime("%H:%M"),
            "pause_minutes": str(pause_minutes),
            "agile": str(agile),
            "theoretical_exit": result["theoretical_exit"],
            "final_exit": result["final_exit"],
        }
        upsert_record(record)
        st.success(f"Giornata del {selected_day.strftime('%d/%m/%Y')} salvata.")

    st.markdown('<div class="week-card">', unsafe_allow_html=True)
    monday, sunday = week_bounds(selected_day)
    st.subheader("Riepilogo settimana")
    st.caption(f"Da {monday.strftime('%d/%m')} a {sunday.strftime('%d/%m')}")

    records = load_records()
    weekly_data = build_week_summary(records, selected_day)
    st.dataframe(weekly_data, use_container_width=True, hide_index=True)

    saved_days = sum(1 for row in weekly_data if row["Ingresso"] != "—")
    agile_days = sum(1 for row in weekly_data if row["Agile"] == "Sì")
    c1, c2 = st.columns(2)
    c1.metric("Giorni salvati", str(saved_days))
    c2.metric("Giorni in agile", str(agile_days))
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("Come funziona"):
        st.write(
            """
            - Inserisci **giorno** e **orario di inizio**.
            - Scegli **30 minuti** oppure **1 ora** di pausa.
            - Attiva **Lavoro agile** quando serve.
            - Il lunedì compare un promemoria per ricordartelo.
            - Premi **Salva giornata** per aggiornare il riepilogo della settimana.
            """
        )
        st.caption(
            "Nota: i dati vengono salvati in un file CSV locale dell’app. Se in futuro vuoi un salvataggio più stabile su più dispositivi, possiamo collegarla a Google Sheets."
        )


if __name__ == "__main__":
    main()
