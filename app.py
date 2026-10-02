import streamlit as st
import pandas as pd
import io
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- BARÈMES OFFICIELS ABIMES ---
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
    st.sidebar.success("Données réinitialisées avec succès !")
    st.rerun()

st.title("🦇 ABIMES - Application Sorties & Justificatifs")

# Extraction dynamique de la liste des participants
tous_participants = list(st.session_state.presents_data.keys())

# Structure à 7 onglets stables
tab1, tab_logement, tab_nourriture, tab3, tab4, tab_recap, tab5 = st.tabs([
    "👥 Participants", "🏠 Logement / Gîte", "🥑 Nourriture", "🚗 Transports", "📸 Scan Tickets", "📋 Journal des Répartitions", "📊 Bilan & Exports"
])

# --- TAB 1 : PARTICIPANTS ---
with tab1:
    st.header("Gestion des participants")
    def ajouter_le_participant():
        nom_saisi = st.session_state.temp_nom
        if nom_saisi:
            st.session_state.presents_data[nom_saisi] = {
                "Genre": st.session_state.temp_genre, 
                "Age": st.session_state.temp_age, 
                "Statut": st.session_state.temp_statut,
                "Assurance": st.session_state.get("temp_ass", "Aucune"), 
                "Materiel": st.session_state.get("temp_mat", False)
            }
            st.session_state.temp_nom = "" 

    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
    nom_p = col_add1.text_input("Prénom N :", key="temp_nom", on_change=ajouter_le_participant)
    genre_p = col_add2.selectbox("Genre :", ["Homme", "Femme"], key="temp_genre")
    cat_p = col_add3.selectbox("Âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"], key="temp_age")
    type_p = col_add4.selectbox("Statut :", ["Membre Club", "Initié / Non-membre"], key="temp_statut")
        
    if st.session_state.get("temp_statut") == "Initié / Non-membre":
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

# --- TAB 2 : LOGEMENT ---
with tab_logement:
    st.header("🏠 Frais de Logement & Gîte")
    if tous_participants:
        col_g1, col_g2 = st.columns(2)
        payeur_gite = col_g1.selectbox("Qui a payé le gîte ?", tous_participants, key="p_gite")
        frais_gite_txt = col_g2.text_input("Montant payé pour le gîte (€) :", value="0", key="txt_gite_val")
        
        cible_gite = st.radio("À qui profite cette dépense de logement ?", ["🌍 Tout le collectif", "👥 Un petit comité / Individuels"], key="radio_cible_gite")
        beneficiaires_gite = tous_participants.copy()
        if cible_gite == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les bénéficiaires de cette facture d'hébergement :**")
            beneficiaires_gite = []
            col_chk_g = st.columns(4)
            for idx in range(len(tous_participants)):
                p_nom = tous_participants[idx]
                with col_chk_g[idx % 4]:
                    if st.checkbox(p_nom, value=True, key=f"gite_cible_{p_nom}_{frais_gite_txt}"):
                        beneficiaires_gite.append(p_nom)
                        
        if st.button("🏠 Enregistrer ce frais de gîte"):
            val_g = evaluer_operation(frais_gite_txt)
            if val_g is not None and val_g > 0:
                if not list(beneficiaires_gite): st.error("Veuillez cocher au moins un bénéficiaire.")
                else:
                    st.session_state.depenses_gite.append({"Payeur": payeur_gite, "Montant": val_g, "Txt": frais_gite_txt, "Beneficiaires": list(beneficiaires_gite)})
                    st.success("Frais de gîte enregistré !")
                    st.rerun()
        
        if st.session_state.depenses_gite:
            st.write("---")
            for idx in range(len(st.session_state.depenses_gite)):
                dg = st.session_state.depenses_gite[idx]
                liste_bg = "Tout le collectif" if len(dg.get("Beneficiaires", tous_participants)) == len(tous_participants) else ", ".join(dg.get("Beneficiaires", tous_participants))
                st.text(f"• {dg['Payeur']} a payé {dg['Montant']:.2f} € pour [{liste_bg}]")
                if st.button("Supprimer cette facture", key=f"del_dg_{idx}"):
                    st.session_state.depenses_gite.pop(idx)
                    st.rerun()
                    
        total_gite_somme = sum(dg["Montant"] for dg in st.session_state.depenses_gite)
        st.metric("Total Gîte cumulé", f"{total_gite_somme:.2f} €")
        st.write("---")
        st.subheader("🏠 Nuits passées au gîte par personne")
        data_nuits = []
        for idx in range(len(tous_participants)):
            p_nom = tous_participants[idx]
            nuits = st.number_input(f"Nombre de nuits pour {p_nom} :", min_value=0, value=2, key=f"nuits_seules_{p_nom}")
            data_nuits.append({"Participant": p_nom, "Nuits": nuits})
        df_nuits = pd.DataFrame(data_nuits)
    else: st.info("Veuillez d'abord ajouter des participants dans l'onglet 1.")

# --- TAB 3 : NOURRITURE ---
with tab_nourriture:
    st.header("🥑 Frais de Nourriture / Courses")
    if tous_participants:
        col_n1, col_n2 = st.columns(2)
        payeur_nourr = col_n1.selectbox("Qui a payé les courses ?", tous_participants, key="p_nourr")
        frais_nourr_txt = col_n2.text_input("Montant des courses (€) :", value="0", key="txt_nourr_val")
        
        cible_nourr = st.radio("À qui profite cette dépense de nourriture ?", ["🌍 Tout le collectif", "👥 Un petit comité / Individuels"], key="radio_cible_nourr")
        beneficiaires_repas = tous_participants.copy()
        if cible_nourr == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les bénéficiaires de cette course :**")
            beneficiaires_repas = []
            col_chk_n = st.columns(4)
            for idx in range(len(tous_participants)):
                p_nom = tous_participants[idx]
                with col_chk_n[idx % 4]:
                    if st.checkbox(p_nom, value=True, key=f"repas_cible_{p_nom}_{frais_nourr_txt}"): beneficiaires_repas.append(p_nom)
        
        if st.button("🥑 Enregistrer ce frais de nourriture"):
            val_n = evaluer_operation(frais_nourr_txt)
            if val_n is not None and val_n > 0:
                if not list(beneficiaires_repas): st.error("Veuillez cocher au moins un bénéficiaire.")
                else:
                    st.session_state.depenses_nourriture.append({"Payeur": payeur_nourr, "Montant": val_n, "Txt": frais_nourr_txt, "Beneficiaires": list(beneficiaires_repas)})
                    st.success("Frais de courses enregistré !")
                    st.rerun()
        
        if st.session_state.depenses_nourriture:
            st.write("---")
            for idx in range(len(st.session_state.depenses_nourriture)):
                dn = st.session_state.depenses_nourriture[idx]
                liste_b = "Tout le monde" if len(dn["Beneficiaires"]) == len(tous_participants) else ", ".join(dn["Beneficiaires"])
                st.text(f"• {dn['Payeur']} a payé {dn['Montant']:.2f} € pour [{liste_b}]")
                if st.button("Supprimer ce ticket de courses", key=f"del_dn_{idx}"):
                    st.session_state.depenses_nourriture.pop(idx)
                    st.rerun()
                    
        total_nourr_somme = sum(dn["Montant"] for dn in st.session_state.depenses_nourriture)
