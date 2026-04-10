# Orario di uscita - Streamlit app

Mini app Streamlit dal look più curato, pronta da usare in locale oppure da pubblicare su Streamlit Community Cloud.

## Funzioni

- calcolo dell'orario di uscita partendo dall'orario di ingresso
- modalità **durata totale** oppure **lavoro + pausa**
- vincolo **non prima delle**
- controllo errori per il formato `HH:MM`
- interfaccia semplice anche da telefono

## File del progetto

- `app.py` → app principale
- `requirements.txt` → dipendenze Python
- `.streamlit/config.toml` → tema grafico Streamlit

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

Poi apri nel browser:

```text
http://localhost:8501
```

## Deploy su Streamlit Community Cloud

1. Crea un repository GitHub
2. Carica dentro questi file
3. Vai su Streamlit Community Cloud
4. Fai **New app**
5. Seleziona il repository
6. Come file principale scegli `app.py`
7. Premi **Deploy**

## Esempio

- ingresso: `09:15`
- durata totale: `08:08`
- uscita minima: `16:38`

Risultato:

```text
17:23
```

## Nota

Le durate vanno sempre scritte nel formato `HH:MM`, per esempio:

- `08:08`
- `07:38`
- `00:30`
