import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import base64
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- email config ---
EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
PASSWORD_SENDER = st.secrets["EMAIL_PASSWORD"]
EMAIL_RECEIVER = st.secrets["EMAIL_RECEIVER"]

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
    
    /* --- deleting blank header space --- */
    .block-container {
        padding-top: 1rem !important; /* Ancora più stretto in alto! */
        padding-bottom: 1rem !important;
    }
    header[data-testid="stHeader"] {
        display: none !important; 
    }
            
    /* --- field labels more compact --- */
    label[data-testid="stWidgetLabel"] p {
        font-size: 1.1rem !important; /* Leggermente ridotto */
        font-weight: 600 !important;  
        color: #1a1a1a !important;
        margin-bottom: 2px !important; /* Quasi azzerato lo spazio sotto il titolo */
    }
            
    /* --- less height of fields --- */
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextInput"] input {
        font-size: 1.2rem !important; /* Da 1.4 a 1.2 per recuperare altezza */
        font-weight: 500 !important;
        color: #1a1a1a !important;
        padding: 8px 12px !important; /* Ridotto il "grasso" (padding) interno */
    }
    
    div[data-testid="stDateInput"] div:focus-within,
    div[data-testid="stTextInput"] div:focus-within {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.2) !important;
    }

    /* --- RADIO BUTTONS (Griglia super elastica mobile-friendly) --- */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        justify-content: center !important; 
        gap: 4px !important; /* Spazio ridotto al minimo vitale */
        width: 100% !important;
    }

    div[role="radiogroup"] label > div:first-child, 
    div[role="radiogroup"] input[type="radio"] {
        display: none !important; 
    }

    div[role="radiogroup"] label {
        background-color: #f8f9fa !important;
        border: 2px solid #e9ecef !important;
        border-radius: 10px !important;
        padding: 0 5px !important; /* Margini interni quasi azzerati */
        margin: 0 !important;
        cursor: pointer !important;
        min-height: 42px !important; /* Ancora più bassi */
        min-width: 0 !important; /* LIBERIAMO LA LARGHEZZA! */
        flex: 1 1 auto !important; /* Magia: i bottoni diventano fluidi ed elastici */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease;
    }

    div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[role="radiogroup"] label p {
        font-size: 1.05rem !important; /* Testo leggermente più piccolo per farcelo stare */
        font-weight: 500 !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
        width: 100% !important;
        line-height: 1 !important;
        color: #333 !important;
    }

    div[role="radiogroup"] label:has(input:checked),
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
        box-shadow: 0 4px 6px rgba(255, 75, 75, 0.3) !important; 
    }
    
    div[role="radiogroup"] label:has(input:checked) p,
    div[role="radiogroup"] label[data-checked="true"] p {
        color: white !important;
    }
            
    </style>
""", unsafe_allow_html=True)

# set step status (Ora sono 5 step)
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
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  
        server.login(EMAIL_SENDER, PASSWORD_SENDER)
        server.send_message(msg)
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)
        
# Function to save data to Google Sheets
def save_to_google_sheet(dati):
    try:
        # 1. Define scopes (read/write access to Drive and Sheets)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # 2. Load credentials from Streamlit secrets
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), #using dict to avoid streamlit secrets parsing issues
            scopes=scopes
        )
        
        # 3. Authorize and connect to Google Sheets
        client = gspread.authorize(creds)
        
        # 4. Open the specific Google Sheet by name
        sheet = client.open_by_key("1qIMZyCwPRVGoms7WErW37LAbYjCCO2HjzLeHqr1Lv4E").sheet1
        
        # 5. Prepare the row data to append
        # Columns: Date | Time | Guests | Name | Phone | Email | Notes | Final Check
        nuova_riga = [
            dati['date'],
            dati['time'],
            dati['guests'],
            dati['name'],
            dati['phone'],
            dati['email'],
            dati['notes'],
            False 
        ]
        
        # 6. insert the row to the start of the sheet
        sheet.insert_row(nuova_riga, index=2, value_input_option='USER_ENTERED')
        return True, ""
        
    except Exception as e:
        return False, str(e)

@st.dialog("🎉 Prenotazione Confermata!")
def show_popup_confirm():
    st.write("La tua richiesta all'**Antica Vaccheria** è andata a buon fine.")
    st.image("https://media.giphy.com/media/1108D2tVaUN3eo/giphy.gif", use_container_width=True)
    
    if st.button("Torna al sito", use_container_width=True):
        st.markdown('<meta http-equiv="refresh" content="0;URL=https://anticavaccheria.it">', unsafe_allow_html=True)

if st.session_state.show_success:
    show_popup_confirm()
    st.session_state.show_success = False

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

# 3. logo title image (Cliccabile)
logo_path = "assets/logo.png"
website_url = "https://anticavaccheria.it"

col_spazio_sx, col_logo, col_spazio_dx = st.columns([1, 2, 1])

with col_logo:
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
            
        html_logo = f"""
        <div style="text-align: center;">
            <a href="{website_url}" target="_self">
                <img src="data:image/png;base64,{encoded_image}" style="width: 100%; max-width: 300px; cursor: pointer; transition: transform 0.2s;">
            </a>
        </div>
        """
        st.markdown(html_logo, unsafe_allow_html=True)
    else:
        html_testo = f"""
        <a href="{website_url}" target="_self" style="text-decoration: none;">
            <h1 style='text-align: center; font-weight: 600; color: #1a1a1a;'>Antica Vaccheria</h1>
        </a>
        """
        st.markdown(html_testo, unsafe_allow_html=True)
        st.caption("Salva il logo in 'assets/logo.png' per sostituire questo testo.")

st.markdown("<p style='text-align: center; color: #666; margin-top: -10px; font-size: 1.1em;'>Prenotazione Tavolo Online</p>", unsafe_allow_html=True)
st.divider()

# Barra divisa in 5 step ora
st.progress(st.session_state.step / 5)

# --- STEP 1: NUMERO OSPITI ---
if st.session_state.step == 1:
    st.subheader("Quante persone sarete?")
    
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
        # Spazio rimosso, andiamo diretti al bottone
        st.markdown("<br>", unsafe_allow_html=True) # Un micro-spazio controllato
        if st.button("Scegli Data e Ora", type="primary", use_container_width=True):
            next_step()
            st.rerun()

# --- STEP 2: DATA E ORA ---
elif st.session_state.step == 2:
    st.subheader("Quando ci verrete a trovare?")
    
    st.session_state.date = st.date_input(
        "Data della prenotazione", 
        min_value=datetime.today(),
        value=st.session_state.get('date', datetime.today()),
        format="DD/MM/YYYY" 
    )
    
    hours_options = ["19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"]
    st.session_state.time = st.radio("Orario di arrivo", options=hours_options, index=None if not st.session_state.get('time') else hours_options.index(st.session_state.get('time')), horizontal=True)        
    
    # Rimosso il <br> per non spingere i bottoni in basso
    col1, col2 = st.columns(2)
    with col1:
        st.button("Indietro", on_click=prev_step, use_container_width=True)
    with col2:
        if st.button("Prosegui ai recapiti", type="primary", use_container_width=True):
            if not st.session_state.time:
                st.error("Per favore, seleziona l'orario di arrivo.")
            else:
                next_step()
                st.rerun()

# --- STEP 3: RECAPITI OBBLIGATORI ---
elif st.session_state.step == 3:
    st.subheader("I tuoi recapiti")
    
    # Usiamo un "form" invisibile (border=False) per ingannare l'autocompletamento di Chrome
    with st.form("form_recapiti", border=False):
        name_val = st.text_input("Nome e Cognome *", value=st.session_state.get('name', ''))
        email_val = st.text_input("Indirizzo Email *", value=st.session_state.get('email', ''))
        phone_val = st.text_input("Numero di Telefono *", value=st.session_state.get('phone', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            # I bottoni dentro un form devono essere st.form_submit_button
            btn_back = st.form_submit_button("Indietro", use_container_width=True)
        with col2:
            btn_next = st.form_submit_button("Prosegui alle Note", type="primary", use_container_width=True)
            
        # Logica dei bottoni gestita fuori dalle colonne ma dentro il form
        if btn_back:
            prev_step()
            st.rerun()
            
        if btn_next:
            if name_val and email_val and phone_val:
                # Salviamo i dati catturati nel session_state
                st.session_state.name = name_val
                st.session_state.email = email_val
                st.session_state.phone = phone_val
                next_step()
                st.rerun()
            else:
                st.error("⚠️ Nome, Email e Telefono sono obbligatori.")

# --- STEP 4: NOTE E RICHIESTE (OPZIONALE) ---
elif st.session_state.step == 4:
    st.subheader("Hai richieste particolari?")
    st.caption("Allergie, seggioloni, o preferenze per il tavolo. (Opzionale)") 
    
    st.session_state.notes = st.text_area("Scrivi qui le tue note", value=st.session_state.get('notes', ''), height=150)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Indietro", on_click=prev_step, use_container_width=True)
    with col2:
        if st.button("Vai al riepilogo", type="primary", use_container_width=True):
            next_step()
            st.rerun()

# --- STEP 5: RIEPILOGO E GDPR ---
elif st.session_state.step == 5:
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
    
    # --- CHECKBOX GDPR OBBIGATORIO ---
    privacy_accepted = st.checkbox(
        "Ho letto e accetto la [Privacy Policy](https://anticavaccheria.it/privacy-policy) per la gestione della prenotazione. *",
        value=False
    )
    
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Indietro", on_click=prev_step, use_container_width=True)
        
    with col2:
        if st.button("Conferma Prenotazione", type="primary", use_container_width=True):
            
            # Controllo GDPR
            if not privacy_accepted:
                st.error("⚠️ Devi accettare la Privacy Policy per inviare la richiesta.")
            else:
                payload = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "date": formatted_date,
                    "time": time,
                    "guests": guests,
                    "notes": notes
                }
                
                with st.spinner('Saving reservation...'):
                    # 1. Try to save on Google Sheets FIRST
                    success_sheets, error_msg_sheets = save_to_google_sheet(payload)
                    
                    # If it fails, STOP EVERYTHING and show the exact error!
                    if not success_sheets:
                        st.error(f"🚨 GOOGLE SHEETS ERROR: {error_msg_sheets}")
                        st.stop() # <--- THE MAGIC COMMAND THAT HALTS THE APP
                    
                    # 2. If it gets here, Sheets worked! Let's also send the backup email:
                    send_email_reservation(payload) 
                    
                    # 3. Clean up session state and rerun to show the success popup
                    keys_to_clear = ['name', 'email', 'phone', 'notes', 'time', 'people', 'date']
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                            
                    st.session_state.step = 1
                    st.session_state.show_success = True
                    st.rerun()