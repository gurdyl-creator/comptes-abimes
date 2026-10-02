import streamlit as st
import pandas as pd
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import PIL.Image

try:
    import easyocr
    import numpy as np
    @st.cache_resource
    def load_ocr_reader():
        return easyocr.Reader(['fr'])
    ocr_disponible = True
except ImportError:
    ocr_disponible = False

st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")
st.title("🦇 ABIMES - Application Sorties & Justificatifs")

# --- BARÈMES OFFICIELS ABIMES (2025/2026) ---
IK_STANDARD = 0.15
SUBV_KM = 0.02
FRAIS_MATOS = 5.00
ASS_1J = 7.20
ASS_3J = 15.50

# --- INITIALISATION DE LA SESSION ---
if 'presents_data' not in st.session_state:
    st.session_state.presents_data = {}
if 'vehicules' not in st.session_state:
    st.session_state.vehicules = []
if 'tickets' not in st.session_state:
    st.session_state.tickets = []

# --- BARRE LATÉRALE ---
st.sidebar.header("📋 Informations Sortie")
nom_sortie = st.sidebar.text_input("Nom de la sortie :", "Sortie Spéléo")
date_debut = st.sidebar.date_input("Date de début :")
date_fin = st.sidebar.date_input("Date de fin :")
dates_sortie = f"Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"
type_act = st.sidebar.selectbox("Type d'activité :", ["classique", "explo", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"])
gite_lieu = st.sidebar.text_input("Lieu du gîte :", "Montrond-le-Château")

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Zone de Danger")
if st.sidebar.button("🗑️ Réinitialiser toute la sortie"):
    st.session_state.presents_data = {}
    st.session_state.vehicules = []
    st.session_state.tickets = []
    st.sidebar.success("Données réinitialisées avec succès !")
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Participants", "🏠 Logement & Nourriture", "🚗 Transports", "📸 Scan Tickets", "📊 Bilan & Exports"])

# --- TAB 1 : PARTICIPANTS ---
with tab1:
    st.header("Gestion des participants")
    def ajouter_le_participant():
        nom_saisi = st.session_state.temp_nom
        if nom_saisi:
            st.session_state.presents_data[nom_saisi] = {
                "Genre": st.session_state.temp_genre, "Age": st.session_state.temp_age, "Statut": st.session_state.temp_statut,
                "Assurance": st.session_state.get("temp_ass", "Aucune"), "Materiel": st.session_state.get("temp_mat", False)
            }
            st.session_state.temp_nom = "" 

    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
    nom_p = col_add1.text_input("Prénom N :", key="temp_nom")
    genre_p = col_add2.selectbox("Genre :", ["Homme", "Femme"], key="temp_genre")
    cat_p = col_add3.selectbox("Âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"], key="temp_age")
    type_p = col_add4.selectbox("Statut :", ["Membre Club", "Initié / Non-membre"], key="temp_statut")
        
    if type_p == "Initié / Non-membre":
        st.subheader("🎒 Options de l'initié")
        col_opt1, col_opt2 = st.columns(2)
        col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"], key="temp_ass")
        col_opt2.checkbox("Prêt de matériel individuel club (5.00€)", key="temp_mat")

    st.button("➕ Enregistrer le participant", on_click=ajouter_le_participant)

    if st.session_state.presents_data:
        st.subheader("Personnes enregistrées")
        for k, v in list(st.session_state.presents_data.items()):
            col_l1, col_l2 = st.columns()
            col_l1.text(f"• {k} | {v['Genre']} | {v['Age']} | {v['Statut']}")
            if col_l2.button("Supprimer", key=f"del_p_{k}"):
                del st.session_state.presents_data[k]
                st.rerun()

tous_participants = list(st.session_state.presents_data.keys())

# --- TAB 2 : REPARTITIONS ---
with tab2:
    st.header("Frais de séjour")
    col_f1, col_f2 = st.columns(2)
    total_gite = col_f1.number_input("Coût total du Gîte (€) :", min_value=0.0, step=10.0)
    total_nourriture = col_f2.number_input("Coût total Nourriture (€) :", min_value=0.0, step=10.0)
        
    if tous_participants:
        st.subheader("Nombre de nuits et de repas")
        data_sejour = []
        for p in tous_participants:
            col_p1, col_p2 = st.columns(2)
            nuits = col_p1.number_input(f"Nuits pour {p} :", min_value=0, value=2, key=f"nuits_{p}")
            repas = col_p2.number_input(f"Repas pour {p} :", min_value=0.0, value=4.0, step=0.5, key=f"repas_{p}")
            data_sejour.append({"Participant": p, "Nuits": nuits, "Repas": repas})
        df_sejour = pd.DataFrame(data_sejour)

# --- TAB 3 : TRANSPORTS COLLECTIFS (Mise à jour complète) ---
with tab3:
    st.header("Gestion des véhicules collectifs et covoiturages")
    st.caption("Déclarez chaque voiture, son chauffeur, et sélectionnez précisément les passagers qui ont voyagé dedans.")
    
    if tous_participants:
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            proprio = st.selectbox("Chauffeur / Propriétaire du véhicule :", tous_participants, key="v_proprio")
        with col_v2:
            km = st.number_input("Kilomètres réels parcourus :", min_value=0, value=0, key="v_km")
        with col_v3:
            peages_carb = st.number_input("Péages + Carburant payés par le chauffeur (€) :", min_value=0.0, value=0.0, key="v_frais")
            
        abandon_frais_chk = st.checkbox("💡 Abandon de Frais (Le conducteur fait don de ses IK au club)")
        
        # Sélection des passagers (Covoiturage spécifique demandé)
        st.write("**Qui voyage dans cette même voiture (Chauffeur compris) ?**")
        passagers_cochés = []
        col_pass = st.columns(4)
        for idx, p in enumerate(tous_participants):
            # Le chauffeur est coché d'office mais on laisse le choix visuel
            est_chauffeur = (p == proprio)
            with col_pass[idx % 4]:
                if st.checkbox(p, value=est_chauffeur, key=f"chk_pass_{p}"):
                    passagers_cochés.append(p)
        
        if st.button("🚗 Enregistrer le véhicule et ses passagers"):
            if not passagers_cochés:
                st.error("Une voiture doit contenir au moins un passager (le chauffeur !).")
            else:
                st.session_state.vehicules.append({
                    "Conducteur": proprio,
                    "KM": km,
                    "Frais": peages_carb,
                    "AbandonFrais": abandon_frais_chk,
                    "Passagers": passagers_cochés
                })
                st.success(f"Véhicule de {proprio} enregistré avec {len(passagers_cochés)} personnes à bord !")
                st.rerun()
            
        if st.session_state.vehicules:
            st.write("---")
            st.subheader("Véhicules enregistrés pour le weekend :")
            for idx, v in enumerate(st.session_state.vehicules):
                don_txt = " (DON DES IK)" if v['AbandonFrais'] else ""
                liste_passagers = ", ".join(v['Passagers'])
                st.text(f"🚗 Voiture de {v['Conducteur']}{don_txt} | {v['KM']} km | Frais : {v['Frais']}€\n👥 Équipage : {liste_passagers}")
                if st.button("Supprimer cette voiture", key=f"del_v_{idx}"):
                    st.session_state.vehicules.pop(idx)
                    st.rerun()
    else:
        st.info("Veuillez d'abord ajouter des participants dans l'onglet 1.")

# --- TAB 4 : SCAN TICKETS ---
with tab4:
    st.header("📸 Saisie automatique et numérisation des tickets")
    if not ocr_disponible:
        st.warning("⚠️ Pour activer l'analyse automatique, veuillez installer EasyOCR : `pip install easyocr torch`")
    fichier_ticket = st.file_uploader("Prendre en photo ou importer un ticket de caisse", type=["png", "jpg", "jpeg"])
    montant_detecte = 0.0
    desc_detectee = ""
    if fichier_ticket and ocr_disponible:
        if st.button("🔍 Lancer la lecture automatique du ticket"):
            with st.spinner("Analyse du ticket en cours..."):
                reader = load_ocr_reader()
                image_bytes = fichier_ticket.read()
                fichier_ticket.seek(0)
                img_pil = PIL.Image.open(io.BytesIO(image_bytes))
                img_np = np.array(img_pil)
                results = reader.readtext(img_np, detail=0)
                texte_complet = " ".join(results).upper()
                prix_trouves = re.findall(r"(?:TOTAL|NET|PAYER|EUR)[\s:]*([\d.,]+)", texte_complet)
                if prix_trouves:
                    nettoye = prix_trouves[-1].replace(",", ".").replace(" ", "")
                    try:
                        montant_detecte = float(nettoye)
                        st.success(f"Montant détecté automatiquement : {montant_detecte:.2f} €")
                    except ValueError:
                        pass
                if any(x in texte_complet for x in ["SUPER", "AUCHAN", "CARREFOUR", "E.LECLERC", "LIDL"]): desc_detectee = "Courses Nourriture"
                elif any(x in texte_complet for x in ["TOTAL", "REPSOL", "SHELL", "AVIA", "STATION"]): desc_detectee = "Carburant / Transport"
                else: desc_detectee = "Achat Weekend"

    st.write("---")
    st.subheader("✍️ Validation et correction manuelle")
    col_v1, col_v2, col_v3 = st.columns(3)
    payeur_ticket = col_v1.selectbox("Qui a payé ?", tous_participants if tous_participants else ["Aucun"], key="tk_payeur")
    desc_final = col_v2.text_input("Description du ticket :", value=desc_detectee, key="tk_desc")
    montant_final = col_v3.number_input("Montant validé (€) :", min_value=0.0, value=montant_detecte, step=1.0, key="tk_montant")
        
    if st.button("💾 Enregistrer définitivement ce justificatif") and fichier_ticket:
        st.session_state.tickets.append({
