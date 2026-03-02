import streamlit as st
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- email config ---
EMAIL_SENDER = "anticavaccheriasocial@gmail.com"  # La mail che invia
PASSWORD_SENDER = st.secrets["EMAIL_PASSWORD"]
EMAIL_RECEIVER = "anticavaccheriasocial@gmail.com" # La mail che riceve (i dipendenti)

# 1. page matadata
st.set_page_config(
    page_title="Antica Vaccheria | Prenotazione", 
    layout="centered", 
    initial_sidebar_state="collapsed",
    page_icon="assets/favicon.png"
)

# 2. advanced css
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap');

    html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, span, label, div {
        font-family: 'Montserrat', sans-serif !important;
    }
            
    /* --- INGRANDIMENTO DI TUTTE LE ETICHETTE (LABEL) DEI CAMPI --- */
    label[data-testid="stWidgetLabel"] p {
        font-size: 1.2rem !important; /* Misura perfetta e coerente per il mobile */
        font-weight: 400 !important;  /* Grassetto per dare enfasi al titolo del campo */
        color: #1a1a1a !important;
        margin-bottom: 8px !important; /* Dà il giusto respiro tra il titolo e il box/bottoni */
    }
            
    /* --- dates style --- */
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextInput"] input {
        font-size: 1.4rem !important; /* Testo gigante dentro la box */
        font-weight: 500 !important;
        color: #1a1a1a !important;
        padding: 12px 15px !important;
    }
    
    /* Evidenzia il bordo dei campi quando ci clicchi dentro */
    div[data-testid="stDateInput"] div:focus-within,
    div[data-testid="stTextInput"] div:focus-within {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.2) !important;
    }

/* --- radio buttons style --- */
    
    /* 1. DISPOSIZIONE OTTIMIZZATA (Più bottoni per riga, centrati) */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: center !important; /* Li tiene belli centrati */
        gap: 12px !important; /* Spazio giusto tra i bottoni */
        width: 100% !important;
    }

    /* 2. KILLER DEL PALLINO (Nasconde il toggle di default) */
    div[role="radiogroup"] label > div:first-child, 
    div[role="radiogroup"] input[type="radio"] {
        display: none !important; 
    }

    /* 3. LA FORMA DEL BOTTONE (Con respiro per gli orari) */
    div[role="radiogroup"] label {
        background-color: #f8f9fa !important;
        border: 2px solid #e9ecef !important;
        border-radius: 12px !important;
        padding: 0 20px !important; /* 15px di spazio laterale per non schiacciare "19:30" */
        margin: 0 !important;
        cursor: pointer !important;
        min-height: 55px !important;
        min-width: 70px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease;
    }

    /* 4. IL CONTENITORE DEL TESTO E IL NUMERO (Centratura assoluta) */
    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 0 !important;
        margin-left: 0 !important; /* IL KILLER DEL DECENTRAMENTO A DESTRA */
        padding: 0 !important;
    }

    div[role="radiogroup"] label p {
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
        width: 100% !important;
        line-height: 1 !important;
        color: #333 !important;
    }

    /* 5. EFFETTO "ACCESO" (Illuminazione quando cliccato) */
    div[role="radiogroup"] label:has(input:checked),
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
        box-shadow: 0 4px 6px rgba(255, 75, 75, 0.3) !important; /* Piccolo alone figo */
    }
    
    /* Fa diventare bianco il testo quando il bottone si accende di rosso */
    div[role="radiogroup"] label:has(input:checked) p,
    div[role="radiogroup"] label[data-checked="true"] p {
        color: white !important;
    }
            
    </style>
""", unsafe_allow_html=True)

# set step status
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# alert email for new reservations
def send_email_reservation(dati):
    msg = MIMEMultipart()
    msg['From'] = f"Sito Antica Vaccheria <{EMAIL_SENDER}>"
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🔴 NUOVA PRENOTAZIONE: {dati['name']} - {dati['date']} ore {dati['time']}"

    corpo = f"""
    Hai ricevuto una nuova richiesta di prenotazione dal sito web!
    
    DETTAGLI TAVOLO:
    - Data: {dati['date']}
    - Orario: {dati['time']}
    - Ospiti: {dati['guests']} persone
    
    DATI CLIENTE:
    - Nome: {dati['name']}
    - Telefono: {dati['phone']}
    - Email: {dati['email']}
    
    NOTE E RICHIESTE SPECIALI:
    {dati['notes'] if dati['notes'] else "Nessuna nota inserita."}
    """
    
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        # conn to gmail server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  
        server.login(EMAIL_SENDER, PASSWORD_SENDER)
        server.send_message(msg)
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)


@st.dialog("🎉 Prenotazione Confermata!")
def show_popup_confirm():
    st.write("La tua richiesta all'**Antica Vaccheria** è andata a buon fine.")
    st.image("https://media.giphy.com/media/1108D2tVaUN3eo/giphy.gif", use_container_width=True)
    
    if st.button("Chiudi e torna alla Home", use_container_width=True):
        st.rerun()

if st.session_state.show_success:
    show_popup_confirm()
    st.session_state.show_success = False

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# 3. logo title image
logo_path = "assets/logo.png"

col_spazio_sx, col_logo, col_spazio_dx = st.columns([1, 2, 1])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; font-weight: 600; color: #1a1a1a;'>Antica Vaccheria</h1>", unsafe_allow_html=True)
        st.caption("Salva il logo in 'assets/logo.svg' per sostituire questo testo.")

st.markdown("<p style='text-align: center; color: #666; margin-top: -10px; font-size: 1.1em;'>Prenotazione Tavolo Online</p>", unsafe_allow_html=True)
st.divider()

st.progress(st.session_state.step / 3)

# --- phase 1: reservation details ---
if st.session_state.step == 1:
    st.subheader("Dettagli della prenotazione")
    st.write("Seleziona le preferenze per il tuo tavolo.")
    
    people_options = ["1", "2", "3", "4", "5", "6", "7", "8", "9+"]
    st.session_state.people = st.radio("Numero di ospiti", options=people_options, index=people_options.index(st.session_state.get('people', "2")), horizontal=True)    
    
    if st.session_state.people == "9+":
        st.info(
            "☎️ **Prenotazioni per gruppi numerosi**\n\n"
            "Per tavolate superiori a 8 persone amiamo dedicare un'attenzione particolare "
            "e concordare il menù o la disposizione della sala. \n\n"
            "Ti preghiamo di contattarci direttamente al numero **+39 012 345 6789** "
            "o scriverci a **anticavaccheriasocial@gmail.com**."
        )
    else:
        st.session_state.date = st.date_input(
            "Data della prenotazione", 
            min_value=datetime.today(),
            value=st.session_state.get('date', datetime.today()),
            format="DD/MM/YYYY" 
        )
        
        hours_options = ["19:00 ", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"]
        st.session_state.time = st.radio("Orario di arrivo", options=hours_options, index=None, horizontal=True)        
        
        st.write("")
        
        if st.button("Prosegui ai recapiti", type="primary", use_container_width=True):
            if not st.session_state.time:
                st.error("Per favore, seleziona l'orario di arrivo.")
            else:
                next_step()
                st.rerun()

# --- phase 2: user data ---
elif st.session_state.step == 2:
    st.subheader("I tuoi recapiti")
    st.write("Inserisci i tuoi dati per confermare la disponibilità.")
    st.caption("I campi contrassegnati con l'asterisco ( * ) sono obbligatori.") # Messaggio di avviso
    
    # Aggiunti gli asterischi alle etichette
    st.session_state.name = st.text_input("Nome e Cognome *", value=st.session_state.get('name', ''))
    st.session_state.email = st.text_input("Indirizzo Email *", value=st.session_state.get('email', ''))
    st.session_state.phone = st.text_input("Numero di Telefono *", value=st.session_state.get('phone', ''))
    
    # Lasciamo questo chiaramente opzionale
    st.session_state.notes = st.text_area("Richieste particolari (opzionale)", value=st.session_state.get('notes', ''), height=100)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Indietro", on_click=prev_step, use_container_width=True)
    with col2:
        if st.button("Vai al riepilogo", type="primary", use_container_width=True):
            if st.session_state.name and st.session_state.email and st.session_state.phone:
                next_step()
                st.rerun()
            else:
                st.error("⚠️ Attenzione: Nome, Email e Telefono sono campi obbligatori.")

# --- phase 3: summary and confirmation ---
elif st.session_state.step == 3:
    st.subheader("Riepilogo e Conferma")
    st.write("Controlla i dati inseriti prima di inviare la richiesta.")
    
    selected_date = st.session_state.get('date', datetime.today())
    try:
        formatted_date = selected_date.strftime('%d/%m/%Y')
    except AttributeError:
        formatted_date = str(selected_date)
        
    time = st.session_state.get('time', 'Non specificato')
    guests = st.session_state.get('people', 'Non specificato')
    name = st.session_state.get('name', 'N/A')
    email = st.session_state.get('email', 'N/A')
    phone = st.session_state.get('phone', 'N/A')
    notes = st.session_state.get('notes', 'Nessuna nota')

    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; color: #333;">
        <p style="margin-bottom: 5px;"><strong>Ristorante:</strong> Antica Vaccheria</p>
        <p style="margin-bottom: 5px;"><strong>Data:</strong> {formatted_date}</p>
        <p style="margin-bottom: 5px;"><strong>Orario:</strong> {time}</p>
        <p style="margin-bottom: 5px;"><strong>Ospiti:</strong> {guests}</p>
        <hr style="border-top: 1px solid #dee2e6; margin: 15px 0;">
        <p style="margin-bottom: 5px;"><strong>Nome:</strong> {name}</p>
        <p style="margin-bottom: 5px;"><strong>Contatti:</strong> {phone} | {email}</p>
        <p style="margin-bottom: 5px; font-size: 0.9em; color: #666;"><strong>Note:</strong> {notes}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Indietro", on_click=prev_step, use_container_width=True)
        
    with col2:
        if st.button("Conferma Prenotazione", type="primary", use_container_width=True):
            
            payload = {
                "name": name,
                "email": email,
                "phone": phone,
                "date": formatted_date,
                "time": time,
                "guests": guests,
                "notes": notes
            }
            
            with st.spinner('Invio richiesta in corso...'):
                # python func instead than n8n
                success, error_msg = send_email_reservation(payload)
                
                if success:
                    keys_to_clear = ['name', 'email', 'phone', 'notes', 'time', 'people', 'date']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                            
                    st.session_state.step = 1
                    st.session_state.show_success = True
                    st.rerun()
                else:
                    st.error(f"Errore durante l'invio dell'email: {error_msg}")