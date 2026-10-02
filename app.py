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
    if not texte_formule:
        return 0.0
    formule_propre = texte_formule.replace(",", ".").replace(" ", "")
    if not re.match(r"^[0-9.+\s]*$", formule_propre):
        return None
    try:
        return float(eval(formule_propre, {"__builtins__": None}, {}))
    except:
        return None

# --- INITIALISATION SÉCURISÉE DE LA SESSION ---
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
            col_l1, col_l2 = st.columns(2)
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

# --- TAB 3 : TRANSPORTS (Gestion double : Collectif vs Individuel) ---
with tab3:
    st.header("Gestion des transports de la sortie")
    st.caption("Déclarez les trajets collectifs (covoiturages) ou individuels (train, voiture solo, etc.).")
    
    if tous_participants:
        # Sélection du type de transport (Nouveauté demandée)
        type_transport = st.radio("Type de transport à ajouter :", ["🚗 Véhicule Collectif (Covoiturage)", "🚆 Transport Individuel (Train, Solo, Autre)"])
        
        st.write("---")
        if type_transport == "🚗 Véhicule Collectif (Covoiturage)":
            col_v1, col_v2, col_v3, col_v4 = st.columns(4)
            proprio = col_v1.selectbox("Chauffeur / Propriétaire :", tous_participants, key="sel_prop")
            km_voiture = col_v2.number_input("Kilomètres totaux de la voiture :", min_value=0, value=0, key="num_km_v")
            carb_texte = col_v3.text_input("Montant Carburant (€) :", value="0", key="txt_carb")
            peage_texte = col_v4.text_input("Montant Péages (€) :", value="0", key="txt_peag")
                
            abandon_frais_chk = st.checkbox("💡 Abandon de Frais (Don des IK au club)", key="chk_abandon")
            
            st.write("**👥 Qui voyage dans cette voiture et combien de kilomètres ?**")
            passagers_details = {}
            col_pass = st.columns(3)
            for idx, p in enumerate(tous_participants):
                with col_pass[idx % 3]:
                    actif = st.checkbox(p, value=(p == proprio), key=f"v_pass_actif_{p}")
                    if actif:
                        km_indiv = st.number_input(f"↳ KM pour {p} :", min_value=0, max_value=max(1, km_voiture), value=km_voiture, key=f"v_pass_km_{p}")
                        passagers_details[p] = km_indiv
            
            if st.button("🚗 Enregistrer ce véhicule collectif"):
                valeur_carb = evaluer_operation(carb_texte)
                valeur_peage = evaluer_operation(peage_texte)
                if valeur_carb is None or valeur_peage is None:
                    st.error("Formule invalide. Utilisez des chiffres et le signe +.")
                elif not passagers_details:
                    st.error("Le véhicule doit contenir au moins un passager.")
                else:
                    st.session_state.vehicules.append({
                        "Type": "Collectif", "Conducteur": proprio, "KM_Voiture": km_voiture,
                        "Carburant": valeur_carb, "Peage": valeur_peage, "AbandonFrais": abandon_frais_chk, "PassagersDetails": passagers_details
                    })
                    st.success("Véhicule collectif enregistré !")
                    st.rerun()
                    
        else:  # --- CAS TRANSPORT INDIVIDUEL (Train, Solo...) ---
            col_i1, col_i2 = st.columns(2)
            voyageur = col_i1.selectbox("Participant concerné :", tous_participants, key="sel_indiv")
            frais_indiv_txt = col_i2.text_input("Coût total du transport individuel (€) :", value="0", key="txt_indiv", help="Ex: 45+45 pour un billet de train")
            
            if st.button("🚆 Enregistrer ce transport individuel"):
                valeur_frais = evaluer_operation(frais_indiv_txt)
                if valeur_frais is None:
                    st.error("Formule invalide.")
                else:
                    st.session_state.vehicules.append({
                        "Type": "Individuel", "Conducteur": voyageur, "FraisIndiv": valeur_frais, "FormuleTxt": frais_indiv_txt
                    })
                    st.success(f"Transport individuel de {voyageur} enregistré ({valeur_frais:.2f} €) !")
                    st.rerun()
            
        # Affichage de la liste globale
        if st.session_state.vehicules:
            st.write("---")
            st.subheader("📋 Liste des transports enregistrés :")
            for idx, v in enumerate(st.session_state.vehicules):
                if v["Type"] == "Collectif":
                    don_txt = " (DON DES IK)" if v['AbandonFrais'] else ""
                    txt_p = [f"{nom} ({k} km)" for nom, k in v["PassagersDetails"].items()]
                    st.text(f"🚗 Voiture de {v['Conducteur']}{don_txt} | {v['KM_Voiture']} km | Frais : {v['Carburant']+v['Peage']:.2f}€\n   👥 Trajets : {' | '.join(txt_p)}")
                else:
                    st.text(f"🚆 Transport Individuel | {v['Conducteur']} | Coût : {v['FraisIndiv']:.2f} € (Détail : {v['FormuleTxt']})")
                
                if st.button("Supprimer", key=f"del_v_{idx}"):
                    st.session_state.vehicules.pop(idx)
                    st.rerun()
    else:
        st.info("Veuillez d'abord ajouter des participants dans l'onglet 1.")

# --- TAB 4 : SCAN TICKETS ---
with tab4:
