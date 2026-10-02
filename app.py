import streamlit as st
import pandas as pd
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import PIL.Image

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

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
if 'depenses_gite' not in st.session_state:
    st.session_state.depenses_gite = []
if 'depenses_nourriture' not in st.session_state:
    st.session_state.depenses_nourriture = []

if 'form_carb_txt' not in st.session_state:
    st.session_state.form_carb_txt = "0"
if 'form_peage_txt' not in st.session_state:
    st.session_state.form_peage_txt = "0"
if 'form_indiv_txt' not in st.session_state:
    st.session_state.form_indiv_txt = "0"

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
    st.session_state.depenses_gite = []
    st.session_state.depenses_nourriture = []
    st.session_state.form_carb_txt = "0"
    st.session_state.form_peage_txt = "0"
    st.session_state.form_indiv_txt = "0"
    st.sidebar.success("Données réinitialisées avec succès !")
    st.rerun()

st.title("🦇 ABIMES - Application Sorties & Justificatifs")
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
    nom_p = col_add1.text_input("Prénom N :", key="temp_nom", on_change=ajouter_le_participant)
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

# --- TAB 2 : REPARTITIONS (Gestion Collectif vs Petit Comité Intégrée) ---
with tab2:
    st.header("Frais de séjour et Présences réelles")
    
    if tous_participants:
        col_g, col_n = st.columns(2)
        
        with col_g:
            st.subheader("🏠 Dépenses de Logement / Gîte")
            col_g1, col_g2 = st.columns(2)
            payeur_gite = col_g1.selectbox("Qui a payé ?", tous_participants, key="p_gite")
            frais_gite_txt = col_g2.text_input("Montant payé (€) :", value="0", key="txt_gite_val")
            if st.button("➕ Enregistrer ce frais de gîte"):
                val_g = evaluer_operation(frais_gite_txt)
                if val_g is not None and val_g > 0:
                    st.session_state.depenses_gite.append({"Payeur": payeur_gite, "Montant": val_g, "Txt": frais_gite_txt})
                    st.session_state.txt_gite_val = "0"
                    st.rerun()
            
            if st.session_state.depenses_gite:
                for idx, dg in enumerate(st.session_state.depenses_gite):
                    st.text(f"• {dg['Payeur']} a payé {dg['Montant']:.2f} € ({dg['Txt']})")
                    if st.button("Supprimer", key=f"del_dg_{idx}"):
                        st.session_state.depenses_gite.pop(idx)
                        st.rerun()

        with col_n:
            st.subheader("🥑 Dépenses de Nourriture / Courses")
            col_n1, col_n2 = st.columns(2)
            payeur_nourr = col_n1.selectbox("Qui a payé ?", tous_participants, key="p_nourr")
            frais_nourr_txt = col_n2.text_input("Montant payé (€) :", value="0", key="txt_nourr_val")
            
            # Logique d'imputation "Petit comité / Individuel" demandée
            cible_nourr = st.radio("À qui est imputée cette dépense de nourriture ?", ["🌍 Tout le collectif", "👥 Un petit comité / Individuels"])
            
            beneficiaires_repas = tous_participants.copy()
            if cible_nourr == "👥 Un petit comité / Individuels":
                st.write("👉 **Cochez uniquement les bénéficiaires de cette course :**")
                beneficiaires_repas = []
                col_chk_n = st.columns(4)
                for idx, p in enumerate(tous_participants):
                    with col_chk_n[idx % 4]:
                        if st.checkbox(p, value=True, key=f"repas_cible_{p}_{frais_nourr_txt}"):
                            beneficiaires_repas.append(p)
            
            if st.button("➕ Enregistrer ce frais de courses"):
                val_n = evaluer_operation(frais_nourr_txt)
                if val_n is not None and val_n > 0:
                    if not beneficiaires_repas:
                        st.error("Veuillez cocher au moins un bénéficiaire.")
                    else:
                        st.session_state.depenses_nourriture.append({
                            "Payeur": payeur_nourr, 
                            "Montant": val_n, 
                            "Txt": frais_nourr_txt,
                            "Beneficiaires": beneficiaires_repas
                        })
                        st.session_state.txt_nourr_val = "0"
                        st.rerun()
            
            if st.session_state.depenses_nourriture:
                for idx, dn in enumerate(st.session_state.depenses_nourriture):
                    liste_b = "Tout le monde" if len(dn["Beneficiaires"]) == len(tous_participants) else ", ".join(dn["Beneficiaires"])
                    st.text(f"• {dn['Payeur']} a payé {dn['Montant']:.2f} € pour [{liste_b}]")
                    if st.button("Supprimer", key=f"del_dn_{idx}"):
                        st.session_state.depenses_nourriture.pop(idx)
                        st.rerun()

        st.write("---")
        st.subheader("⏱️ Présence (Nombre de nuits et de repas pour le calcul des proratas)")
        data_sejour = []
        for p in tous_participants:
            col_p1, col_p2 = st.columns(2)
            nuits = col_p1.number_input(f"Nuits pour {p} :", min_value=0, value=2, key=f"nuits_{p}")
            repas = col_p2.number_input(f"Repas pour {p} :", min_value=0.0, value=4.0, step=0.5, key=f"repas_{p}")
            data_sejour.append({"Participant": p, "Nuits": nuits, "Repas": repas})
        df_sejour = pd.DataFrame(data_sejour)
    else:
        st.info("Veuillez d'abord ajouter des participants dans l'onglet 1.")

# --- TAB 3 : TRANSPORTS ---
with tab3:
    st.header("Gestion des transports de la sortie")
    st.caption("Déclarez les trajets collectifs (covoiturages) ou individuels (train, voiture solo, etc.).")
    if tous_participants:
        type_transport = st.radio("Type de transport à ajouter :", ["🚗 Véhicule Collectif (Covoiturage)", "🚆 Transport Individuel (Train, Solo, Autre)"])
        st.write("---")
        if type_transport == "🚗 Véhicule Collectif (Covoiturage)":
            col_v1, col_v2, col_v3, col_v4 = st.columns(4)
            proprio = col_v1.selectbox("Chauffeur / Propriétaire :", tous_participants, key="sel_prop")
            km_voiture = col_v2.number_input("Kilomètres totaux de la voiture :", min_value=0, value=0, key="num_km_v")
