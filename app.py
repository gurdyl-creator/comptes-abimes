import streamlit as st
import pandas as pd
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import PIL.Image

# --- TENTATIVE D'IMPORT DE L'OCR GRATUIT ---
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
st.title("Bat 🦇 ABIMES - Application Sorties & Justificatifs")

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

# --- BARRE LATÉRALE : PARAMÈTRES ET RÉINITIALISATION ---
st.sidebar.header("📋 Informations Sortie")
nom_sortie = st.sidebar.text_input("Nom de la sortie :", "Sortie Spéléo")
dates_sortie = st.sidebar.text_input("Dates de la sortie :", "Ce Weekend")
type_act = st.sidebar.selectbox("Type d'activité :", ["classique", "explo", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"])
gite_lieu = st.sidebar.text_input("Lieu du gîte :", "Montrond-le-Château")

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Zone de Danger")
if st.sidebar.button("🗑️ Réinitialiser toute la sortie", help="Efface tous les participants, véhicules et tickets enregistrés."):
    st.session_state.presents_data = {}
    st.session_state.vehicules = []
    st.session_state.tickets = []
    st.sidebar.success("Données réinitialisées avec succès !")
    st.rerun()

# --- ONGLETS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Participants", "🏠 Logement & Nourriture", "🚗 Transports & IK", "📸 Scan Tickets", "📊 Bilan & Exports"])

# --- TAB 1 : PARTICIPANTS (Correction des colonnes ici) ---
with tab1:
    st.header("Gestion des participants")
    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
    nom_p = col_add1.text_input("Prénom N :", key="add_p_name")
    genre_p = col_add2.selectbox("Genre :", ["Homme", "Femme"], key="add_p_genre")
    cat_p = col_add3.selectbox("Âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"], key="add_p_age")
    type_p = col_add4.selectbox("Statut :", ["Membre Club", "Initié / Non-membre"], key="add_p_statut")
        
    ass_i, mat_i = "Aucune", False
    if type_p == "Initié / Non-membre":
        st.subheader("🎒 Options de l'initié")
        col_opt1, col_opt2 = st.columns(2)
        ass_i = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
        mat_i = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")

    if st.button("➕ Enregistrer le participant") and nom_p:
        st.session_state.presents_data[nom_p] = {
            "Genre": genre_p, "Age": cat_p, "Statut": type_p, "Assurance": ass_i, "Materiel": mat_i
        }
        st.rerun()

    if st.session_state.presents_data:
        st.subheader("Personnes enregistrées")
        for k, v in list(st.session_state.presents_data.items()):
            col_l1, col_l2 = st.columns([4, 1])  # Correction : Ajout du ratio de colonnes
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

# --- TAB 3 : TRANSPORTS ---
with tab3:
    st.header("Gestion des véhicules collectifs")
    if tous_participants:
        col_v1, col_v2, col_v3 = st.columns(3)
        proprio = col_v1.selectbox("Conducteur :", tous_participants)
        km = col_v2.number_input("Kilomètres réels :", min_value=0, value=0)
        peages_carb = col_v3.number_input("Péages + Carburant payés (€) :", min_value=0.0, value=0.0)
        abandon_frais_chk = st.checkbox("💡 Abandon de Frais (Don des IK au club)")
        
        if st.button("Ajouter ce véhicule"):
            st.session_state.vehicules.append({"Conducteur": proprio, "KM": km, "Frais": peages_carb, "AbandonFrais": abandon_frais_chk})
            st.rerun()
            
        if st.session_state.vehicules:
            for idx, v in enumerate(st.session_state.vehicules):
                st.text(f"🚗 {v['Conducteur']} - {v['KM']} km - {v['Frais']}€ {'(DON)' if v['AbandonFrais'] else ''}")
                if st.button("Supprimer", key=f"del_v_{idx}"):
                    st.session_state.vehicules.pop(idx)
                    st.rerun()

# --- TAB 4 : SCAN DES TICKETS ---
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
                if any(x in texte_complet for x in ["SUPER", "AUCHAN", "CARREFOUR", "E.LECLERC", "LIDL"]):
                    desc_detectee = "Courses Nourriture"
                elif any(x in texte_complet for x in ["TOTAL", "REPSOL", "SHELL", "AVIA", "STATION"]):
                    desc_detectee = "Carburant / Transport"
                else:
                    desc_detectee = "Achat Weekend"

    st.write("---")
    st.subheader("✍️ Validation et correction manuelle")
    col_v1, col_v2, col_v3 = st.columns(3)
    payeur_ticket = col_v1.selectbox("Qui a payé ?", tous_participants if tous_participants else ["Aucun"], key="tk_payeur")
    desc_final = col_v2.text_input("Description du ticket :", value=desc_detectee, key="tk_desc")
    montant_final = col_v3.number_input("Montant validé (€) :", min_value=0.0, value=montant_detecte, step=1.0, key="tk_montant")
        
    if st.button("💾 Enregistrer définitivement ce justificatif") and fichier_ticket:
        st.session_state.tickets.append({
            "Payeur": payeur_ticket, "Description": desc_final, "Montant": montant_final,
            "Fichier": fichier_ticket.read(), "NomFichier": fichier_ticket.name
        })
        st.success(f"Ticket '{desc_final}' enregistré !")
        st.rerun()
        
    if st.session_state.tickets:
        st.write("**Tickets validés pour ce weekend :**")
        for idx, t in enumerate(st.session_state.tickets):
            col_tkl1, col_tkl2 = st.columns([4, 1])  # Correction : Ajout du ratio de colonnes
            col_tkl1.text(f"📎 {t['Description']} | Payé par : {t['Payeur']} | Montant : {t['Montant']:.2f} €")
            if col_tkl2.button("Supprimer", key=f"del_t_{idx}"):
                st.session_state.tickets.pop(idx)
                st.rerun()

# --- TAB 5 : BILAN & EXPORTS ---
with tab5:
    if tous_participants:
        total_nuits = df_sejour["Nuits"].sum()
        cout_nuitée = (total_gite / total_nuits) if total_nuits > 0 else 0
        df_sejour["Coût Gîte"] = df_sejour["Nuits"] * cout_nuitée
        total_repas = df_sejour["Repas"].sum()
        cout_repas = (total_nourriture / total_repas) if total_repas > 0 else 0
        df_sejour["Coût Nourriture"] = df_sejour["Repas"] * cout_repas
        total_km_sorties = sum(v["KM"] for v in st.session_state.vehicules)
        total_frais_transp = sum(v["Frais"] for v in st.session_state.vehicules)
        total_ik_club = total_km_sorties * IK_STANDARD
        part_transport_indiv = (total_frais_transp + total_ik_club) / len(tous_participants)
        df_sejour["Frais Initiation"] = 0.0
        df_sejour["Don au club (Abandon IK)"] = 0.0
        for idx, row in df_sejour.iterrows():
            p = row["Participant"]
            p_info = st.session_state.presents_data[p]
            frais_i = 0.0
