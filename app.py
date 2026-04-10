import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Calcolo Orario di Uscita",
    page_icon="🕒",
    layout="centered",
)

ORE_LAVORO = 7
MINUTI_LAVORO = 38
USCITA_MINIMA = "16:38"


def parse_time(time_str: str) -> datetime:
    return datetime.strptime(time_str.strip(), "%H:%M")


def format_duration(td: timedelta) -> str:
    total_minutes = int(td.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def main():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            color: #6b7280;
            margin-bottom: 1.2rem;
        }
        .result-card {
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            border: 1px solid rgba(120,120,120,0.18);
            background: rgba(255,255,255,0.04);
            margin-top: 1rem;
        }
        .result-time {
            font-size: 2rem;
            font-weight: 800;
            margin: 0.2rem 0;
        }
        .small-note {
            color: #6b7280;
            font-size: 0.95rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="main-title">🕒 Calcolo orario di uscita</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Inserisci solo l’orario di inizio e scegli la pausa pranzo. '
        'La durata di lavoro è fissa a 7:38.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        ingresso = st.text_input(
            "Orario di inizio",
            value="09:15",
            help="Formato HH:MM, per esempio 09:15",
            placeholder="09:15",
        )

        pausa_label = st.radio(
            "Pausa pranzo",
            options=["30 minuti", "1 ora"],
            horizontal=True,
        )

        pausa_minuti = 30 if pausa_label == "30 minuti" else 60
        lavoro = timedelta(hours=ORE_LAVORO, minutes=MINUTI_LAVORO)
        pausa = timedelta(minutes=pausa_minuti)
        durata_totale = lavoro + pausa

        st.caption(
            f"Lavoro fisso: {ORE_LAVORO}:{MINUTI_LAVORO:02d} · "
            f"Pausa: {format_duration(pausa)} · "
            f"Totale: {format_duration(durata_totale)}"
        )

    calcola = st.button("Calcola uscita", use_container_width=True)

    if calcola:
        try:
            ora_ingresso = parse_time(ingresso)
            uscita_minima = parse_time(USCITA_MINIMA)

            uscita_calcolata = ora_ingresso + durata_totale
            uscita_finale = max(uscita_calcolata, uscita_minima)

            delta_extra = uscita_finale - uscita_calcolata

            st.markdown(
                f"""
                <div class="result-card">
                    <div class="small-note">Puoi staccare alle</div>
                    <div class="result-time">{uscita_finale.strftime("%H:%M")}</div>
                    <div class="small-note">
                        Calcolo automatico: ingresso + 7:38 + pausa
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Uscita teorica", uscita_calcolata.strftime("%H:%M"))
            with c2:
                st.metric("Uscita minima", USCITA_MINIMA)

            if delta_extra > timedelta(0):
                st.info(
                    f"L’orario teorico sarebbe {uscita_calcolata.strftime('%H:%M')}, "
                    f"ma non puoi uscire prima delle {USCITA_MINIMA}."
                )
            else:
                st.success("L’orario calcolato rispetta già il vincolo di uscita minima.")

        except ValueError:
            st.error("Formato non valido. Inserisci l’orario come HH:MM, per esempio 09:15.")

    with st.expander("Come funziona"):
        st.write(
            """
            - Inserisci **solo** l’orario di inizio.
            - Scegli la pausa pranzo: **30 minuti** oppure **1 ora**.
            - L’app aggiunge in automatico **7 ore e 38 minuti** di lavoro.
            - Se il risultato è prima delle **16:38**, mostra comunque **16:38**.
            """
        )


if __name__ == "__main__":
    main()
