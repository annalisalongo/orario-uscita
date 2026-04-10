from __future__ import annotations

from datetime import date, datetime, time, timedelta
import streamlit as st


DEFAULT_START = time(9, 15)
DEFAULT_MIN_EXIT = time(16, 38)
DEFAULT_TOTAL_DURATION = "08:08"
DEFAULT_WORK_DURATION = "07:38"
DEFAULT_BREAK_DURATION = "00:30"


class DurationParseError(ValueError):
    """Raised when a duration is not in HH:MM format."""


def parse_hhmm_duration(value: str) -> timedelta:
    value = value.strip()
    parts = value.split(":")

    if len(parts) != 2:
        raise DurationParseError("Usa il formato HH:MM, per esempio 08:08")

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
    except ValueError as exc:
        raise DurationParseError("Ore e minuti devono essere numeri") from exc

    if hours < 0 or minutes < 0:
        raise DurationParseError("Ore e minuti non possono essere negativi")

    if minutes >= 60:
        raise DurationParseError("I minuti devono essere compresi tra 00 e 59")

    return timedelta(hours=hours, minutes=minutes)


def format_timedelta(delta: timedelta) -> str:
    total_minutes = int(delta.total_seconds() // 60)
    sign = "-" if total_minutes < 0 else ""
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def combine_today(t: time) -> datetime:
    return datetime.combine(date.today(), t)


def reset_defaults() -> None:
    st.session_state.start_time = DEFAULT_START
    st.session_state.minimum_exit_time = DEFAULT_MIN_EXIT
    st.session_state.mode = "Durata totale"
    st.session_state.total_duration = DEFAULT_TOTAL_DURATION
    st.session_state.work_duration = DEFAULT_WORK_DURATION
    st.session_state.break_duration = DEFAULT_BREAK_DURATION


def compute_exit(start_time: time, minimum_exit_time: time, total_duration: timedelta) -> dict[str, object]:
    start_dt = combine_today(start_time)
    min_exit_dt = combine_today(minimum_exit_time)
    calculated_exit_dt = start_dt + total_duration

    if calculated_exit_dt.date() > start_dt.date() and min_exit_dt < start_dt:
        min_exit_dt += timedelta(days=1)

    final_exit_dt = max(calculated_exit_dt, min_exit_dt)
    added_for_minimum = final_exit_dt - calculated_exit_dt if final_exit_dt > calculated_exit_dt else timedelta(0)
    above_minimum = final_exit_dt - min_exit_dt if final_exit_dt > min_exit_dt else timedelta(0)

    return {
        "start_dt": start_dt,
        "min_exit_dt": min_exit_dt,
        "calculated_exit_dt": calculated_exit_dt,
        "final_exit_dt": final_exit_dt,
        "added_for_minimum": added_for_minimum,
        "above_minimum": above_minimum,
    }


def pretty_dt_label(dt: datetime, reference: datetime) -> str:
    label = dt.strftime("%H:%M")
    if dt.date() > reference.date():
        return f"{label} (+1 giorno)"
    return label


st.set_page_config(
    page_title="Orario di uscita",
    page_icon="🕒",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "start_time" not in st.session_state:
    reset_defaults()

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 860px;
        }
        .hero {
            padding: 1.25rem 1.25rem 1.1rem 1.25rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(99,102,241,0.16), rgba(16,185,129,0.14));
            border: 1px solid rgba(255,255,255,0.12);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
        }
        .hero p {
            margin: 0.45rem 0 0 0;
            opacity: 0.88;
        }
        .glass-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 22px;
            padding: 1rem 1rem 0.35rem 1rem;
            margin-bottom: 1rem;
        }
        .result-card {
            padding: 1.2rem;
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(99,102,241,0.22), rgba(16,185,129,0.18));
            border: 1px solid rgba(255,255,255,0.10);
            margin: 0.4rem 0 1rem 0;
        }
        .result-label {
            font-size: 0.95rem;
            opacity: 0.9;
            margin-bottom: 0.15rem;
        }
        .result-value {
            font-size: 2.4rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 0.3rem;
        }
        .result-note {
            opacity: 0.88;
            font-size: 0.96rem;
        }
        .tiny {
            font-size: 0.92rem;
            opacity: 0.8;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 0.6rem 0.8rem;
        }
        .footer-note {
            text-align: center;
            opacity: 0.72;
            font-size: 0.9rem;
            margin-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🕒 Orario di uscita</h1>
        <p>Calcola subito a che ora puoi staccare, con durata totale oppure lavoro + pausa, e con vincolo minimo di uscita.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_a, col_b, col_c = st.columns(3)
col_a.caption("Ingresso default")
col_a.write("**09:15**")
col_b.caption("Durata standard")
col_b.write("**08:08**")
col_c.caption("Non prima delle")
col_c.write("**16:38**")

with st.container(border=False):
    top1, top2 = st.columns([0.75, 0.25])
    with top1:
        st.markdown(
            "<div class='tiny'>Inserisci gli orari nel formato standard. Le durate vanno scritte come <strong>HH:MM</strong>.</div>",
            unsafe_allow_html=True,
        )
    with top2:
        st.button("Ripristina", use_container_width=True, on_click=reset_defaults)

st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
with st.form("exit_form"):
    c1, c2 = st.columns(2)
    with c1:
        start_time = st.time_input(
            "Orario di ingresso",
            key="start_time",
            step=60,
            help="Quando hai iniziato a lavorare.",
        )
    with c2:
        minimum_exit_time = st.time_input(
            "Non prima delle",
            key="minimum_exit_time",
            step=60,
            help="Orario minimo sotto il quale non puoi uscire.",
        )

    mode = st.radio(
        "Come vuoi inserire la durata?",
        options=["Durata totale", "Lavoro + pausa"],
        horizontal=True,
        key="mode",
    )

    total_duration_text: str | None = None
    work_duration_text: str | None = None
    break_duration_text: str | None = None

    if mode == "Durata totale":
        total_duration_text = st.text_input(
            "Durata totale (HH:MM)",
            key="total_duration",
            placeholder="08:08",
        )
    else:
        c3, c4 = st.columns(2)
        with c3:
            work_duration_text = st.text_input(
                "Lavoro effettivo (HH:MM)",
                key="work_duration",
                placeholder="07:38",
            )
        with c4:
            break_duration_text = st.text_input(
                "Pausa (HH:MM)",
                key="break_duration",
                placeholder="00:30",
            )

    submitted = st.form_submit_button("Calcola l'orario di uscita", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if not submitted:
    st.info("Compila i campi e premi il pulsante per vedere il risultato.")

if submitted:
    try:
        if mode == "Durata totale":
            assert total_duration_text is not None
            total_duration = parse_hhmm_duration(total_duration_text)
            work_duration = None
            break_duration = None
        else:
            assert work_duration_text is not None and break_duration_text is not None
            work_duration = parse_hhmm_duration(work_duration_text)
            break_duration = parse_hhmm_duration(break_duration_text)
            total_duration = work_duration + break_duration

        result = compute_exit(
            start_time=start_time,
            minimum_exit_time=minimum_exit_time,
            total_duration=total_duration,
        )

        start_dt = result["start_dt"]
        min_exit_dt = result["min_exit_dt"]
        calculated_exit_dt = result["calculated_exit_dt"]
        final_exit_dt = result["final_exit_dt"]
        added_for_minimum = result["added_for_minimum"]
        above_minimum = result["above_minimum"]

        reason = (
            f"È stato applicato il minimo di uscita delle {minimum_exit_time.strftime('%H:%M')}."
            if final_exit_dt == min_exit_dt and calculated_exit_dt < min_exit_dt
            else "L'orario calcolato rispetta già il vincolo minimo."
        )

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">Puoi staccare alle</div>
                <div class="result-value">{pretty_dt_label(final_exit_dt, start_dt)}</div>
                <div class="result-note">{reason}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Ingresso", start_time.strftime("%H:%M"))
        m2.metric("Durata totale", format_timedelta(total_duration))
        m3.metric("Uscita minima", pretty_dt_label(min_exit_dt, start_dt))

        m4, m5 = st.columns(2)
        m4.metric("Uscita teorica", pretty_dt_label(calculated_exit_dt, start_dt))
        if final_exit_dt == min_exit_dt and calculated_exit_dt < min_exit_dt:
            m5.metric("Tempo aggiunto", format_timedelta(added_for_minimum))
            st.warning(
                f"L'uscita teorica era **{pretty_dt_label(calculated_exit_dt, start_dt)}**, ma non puoi staccare prima di **{minimum_exit_time.strftime('%H:%M')}**."
            )
        else:
            m5.metric("Oltre il minimo", format_timedelta(above_minimum))
            st.success("Perfetto: l'orario teorico è già compatibile con l'uscita minima.")

        if work_duration is not None and break_duration is not None:
            st.subheader("Composizione della durata")
            d1, d2 = st.columns(2)
            d1.metric("Lavoro effettivo", format_timedelta(work_duration))
            d2.metric("Pausa", format_timedelta(break_duration))

        summary_text = (
            f"Ingresso {start_time.strftime('%H:%M')} + durata {format_timedelta(total_duration)} = "
            f"uscita {pretty_dt_label(final_exit_dt, start_dt)}"
        )
        st.code(summary_text, language="text")

        with st.expander("Come funziona il calcolo"):
            st.write(
                "1. Somma l'orario di ingresso e la durata totale.\n"
                "2. Confronta il risultato con l'orario minimo di uscita.\n"
                "3. Mostra il più tardo tra i due."
            )

    except DurationParseError as exc:
        st.error(str(exc))

st.markdown(
    "<div class='footer-note'>Pronta per Streamlit Community Cloud: carica questi file su GitHub e fai il deploy.</div>",
    unsafe_allow_html=True,
)
