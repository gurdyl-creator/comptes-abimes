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

# --- FONCTION CALCULATRICE INTÉGRÉE ---
def evaluer_operation(texte_formule):
    """Évalue une formule mathématique simple (ex: 22,20+25+33) et retourne le total float"""
    if not texte_formule:
        return 0.0
    # Nettoyage : remplacer les virgules par des points et enlever les espaces
    formule_propre = texte_formule.replace(",", ".").replace(" ", "")
    # Sécurité : n'autoriser que les chiffres, les points et les signes +
    if not re.match(r"^[0-9.+\s]*$", formule_propre):
        return None
    try:
        # Évaluation sécurisée de l'addition
        return float(eval(formule_propre, {"__builtins__": None}, {}))
    except:
        return None

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

# --- TAB 3 : TRANSPORTS (Version Calculatrice Intégrée) ---
with tab3:
    st.header("Gestion des véhicules collectifs et covoiturages")
    st.caption("Déclarez chaque voiture. Vous pouvez taper des opérations directement dans les cases Carburant et Péages (ex: 22,20+25+33).")
    
    if tous_participants:
        col_v1, col_v2, col_v3, col_v4 = st.columns(4)
        with col_v1:
            proprio = st.selectbox("Chauffeur / Propriétaire :", tous_participants, key="v_proprio")
        with col_v2:
            km = st.number_input("Kilomètres réels :", min_value=0, value=0, key="v_km")
        with col_v3:
            # Transformation en champ texte pour accepter l'opération mathématique
            carb_texte = st.text_input("Montant Carburant (€) :", value="0", key="v_carb_txt", help="Exemple : 45.50+20+15")
            valeur_carb = evaluer_operation(carb_texte)
            if valeur_carb is None:
                st.error("Formule carburant invalide. Utilisez uniquement des chiffres et le signe +.")
                valeur_carb = 0.0
            elif carb_texte != "0" and "+" in carb_texte:
                st.info(f"Total Carburant calculé : {valeur_carb:.2f} €")
                
        with col_v4:
            # Idem pour les péages
            peage_texte = st.text_input("Montant Péages (€) :", value="0", key="v_peage_txt", help="Exemple : 7.20+11.50")
            valeur_peage = evaluer_operation(peage_texte)
            if valeur_peage is None:
                st.error("Formule péages invalide. Utilisez uniquement des chiffres et le signe +.")
                valeur_peage = 0.0
            elif peage_texte != "0" and "+" in peage_texte:
                st.info(f"Total Péages calculé : {valeur_peage:.2f} €")
            
        abandon_frais_chk = st.checkbox("💡 Abandon de Frais (Le conducteur fait don de ses IK au club)")
        
        st.write("**Qui voyage dans cette même voiture (Chauffeur compris) ?**")
        passagers_cochés = []
        col_pass = st.columns(4)
        for idx, p in enumerate(tous_participants):
            est_chauffeur = (p == proprio)
            with col_pass[idx % 4]:
                if st.checkbox(p, value=est_chauffeur, key=f"chk_pass_{p}"):
                    passagers_cochés.append(p)
        
        if st.button("🚗 Enregistrer le véhicule et ses passagers"):
            if not passagers_cochés:
                st.error("Une voiture doit contenir au moins un passager.")
            else:
                st.session_state.vehicules.append({
                    "Conducteur": proprio,
                    "KM": km,
                    "CarburantTxt": carb_texte,  # On mémorise la formule texte originale
                    "Carburant": valeur_carb,     # On stocke le résultat chiffré
                    "PeageTxt": peage_texte,      # On mémorise la formule texte originale
                    "Peage": valeur_peage,         # On stocke le résultat chiffré
                    "AbandonFrais": abandon_frais_chk,
                    "Passagers": passagers_cochés
                })
                # Remise à zéro des champs textes après enregistrement
                st.session_state.v_carb_txt = "0"
                st.session_state.v_peage_txt = "0"
                st.success(f"Véhicule de {proprio} enregistré !")
                st.rerun()
            
        if st.session_state.vehicules:
            st.write("---")
            st.subheader("Véhicules enregistrés :")
            for idx, v in enumerate(st.session_state.vehicules):
                don_txt = " (DON DES IK)" if v['AbandonFrais'] else ""
                liste_passagers = ", ".join(v['Passagers'])
                total_frais = v['Carburant'] + v['Peage']
                
                # Affichage de la formule originale si elle existe
                carb_details = f" ({v['CarburantTxt']})" if "+" in v['CarburantTxt'] else ""
                peage_details = f" ({v['PeageTxt']})" if "+" in v['PeageTxt'] else ""
                
                st.text(f"🚗 Voiture de {v['Conducteur']}{don_txt} | {v['KM']} km\n⛽ Carburant : {v['Carburant']:.2f}€{carb_details} | 🎫 Péages : {v['Peage']:.2f}€{peage_details} (Total Frais : {total_frais:.2f} €)\n👥 Équipage : {liste_passagers}")
                if st.button("Supprimer cette voiture", key=f"del_v_{idx}"):
                    st.session_state.vehicules.pop(idx)
                    st.rerun()
    else:
        st.info("Veuillez d'abord ajouter des participants dans l'onglet 1.")

# --- TAB 4 : SCAN TICKETS ---
