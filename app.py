import streamlit as st
import pandas as pd
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
if 'presents_data' not in st.session_state: st.session_state.presents_data = {}
if 'vehicules' not in st.session_state: st.session_state.vehicules = []
if 'tickets' not in st.session_state: st.session_state.tickets = []
if 'depenses_gite' not in st.session_state: st.session_state.depenses_gite = []
if 'depenses_nourriture' not in st.session_state: st.session_state.depenses_nourriture = []
if 'nuits_data' not in st.session_state: st.session_state.nuits_data = {}
if 'repas_data' not in st.session_state: st.session_state.repas_data = {}

# --- BARRE LATÉRALE : NAVIGATION ---
st.sidebar.header("📋 ABIMES - Menu")
section_choisie = st.sidebar.radio(
    "Aller à la section :",
    [
        "👥 1. Participants", 
        "🏠 2. Logement & Gîte", 
        "🥑 3. Nourriture & Courses", 
        "🚗 4. Transports & Covoiturage", 
        "📸 5. Justificatifs & Tickets", 
        "📈 6. Visualisation des Dépenses",
        "📊 7. Bilan Global & Répartitions"
    ]
)

st.sidebar.write("---")
st.sidebar.subheader("📋 Informations Sortie")
nom_sortie = st.sidebar.text_input("Nom de la sortie :", "Sortie Spéléo")
gite_lieu = st.sidebar.text_input("Lieu :", "Montrond-le-Château")

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Zone de Danger")
if st.sidebar.button("🗑️ Réinitialiser tout"):
    st.session_state.presents_data = {}
    st.session_state.vehicules = []
    st.session_state.tickets = []
    st.session_state.depenses_gite = []
    st.session_state.depenses_nourriture = []
    st.session_state.nuits_data = {}
    st.session_state.repas_data = {}
    st.success("Données nettoyées !")
    st.rerun()

st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# =====================================================================
# --- SECTION 1 : PARTICIPANTS (FONCTIONNEL) ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Gestion des participants")
    def ajouter_le_participant():
        nom_saisi = st.session_state.temp_nom
        if nom_saisi:
            st.session_state.presents_data[nom_saisi] = {
                "Genre": st.session_state.temp_genre, "Age": st.session_state.temp_age, "Statut": st.session_state.temp_statut,
                "Assurance": st.session_state.get("temp_ass", "Aucune"), "Materiel": st.session_state.get("temp_mat", False)
            }
            st.session_state.nuits_data[nom_saisi] = 2
            st.session_state.repas_data[nom_saisi] = 4.0
            st.session_state.temp_nom = "" 

    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
    nom_p = col_add1.text_input("Prénom N :", key="temp_nom", on_change=ajouter_le_participant)
    genre_p = col_add2.selectbox("Genre :", ["Homme", "Femme"], key="temp_genre")
    cat_p = col_add3.selectbox("Âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"], key="temp_age")
    type_p = col_add4.selectbox("Statut :", ["Membre Club", "Initié / Non-membre"], key="temp_statut")
        
    if st.session_state.get("temp_statut") == "Initié / Non-membre":
        st.write("🎒 **Options de l'initié :**")
        col_opt1, col_opt2 = st.columns(2)
        col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"], key="temp_ass")
        col_opt2.checkbox("Prêt de matériel individuel club (5.00€)", key="temp_mat")

    st.button("➕ Enregistrer le participant", on_click=ajouter_le_participant)

    if tous_participants:
        st.write("---")
        st.subheader("Membres enregistrés")
        for p in tous_participants:
            col_l1, col_l2 = st.columns(2)
            col_l1.text(f"• {p} ({st.session_state.presents_data[p]['Statut']})")
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.session_state.nuits_data.pop(p, None)
                st.session_state.repas_data.pop(p, None)
                st.rerun()

# =====================================================================
# --- SECTION 2 : LOGEMENT (FONCTIONNEL AVEC PETITS COMITÉS) ---
# =====================================================================
elif section_choisie == "🏠 2. Logement & Gîte":
    if not tous_participants:
        st.info("💡 Ajoutez d'abord des participants dans la section 1.")
    else:
        col_g1, col_g2 = st.columns(2)
        payeur_gite = col_g1.selectbox("Qui a payé le gîte ?", tous_participants, key="p_gite")
        frais_gite_txt = col_g2.text_input("Montant paid pour le gîte (€) :", value="0", key="txt_gite_val")
        
        cible_gite = st.radio("À qui profite cette dépense ?", ["🌍 Tout le collectif", "👥 Un petit comité / Individuels"], key="r_c_gite")
        
        beneficiaires_gite = []
        if cible_gite == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les bénéficiaires de cet hébergement :**")
            for p in tous_participants:
                if st.checkbox(f"Profite à {p}", value=True, key=f"gite_cb_{p}"):
                    beneficiaires_gite.append(p)
        else:
            beneficiaires_gite = tous_participants.copy()
        
        if st.button("🏠 Enregistrer cette facture de gîte"):
            val_g = evaluer_operation(frais_gite_txt)
            if val_g and val_g > 0:
                if not beneficiaires_gite: st.error("Cochez au moins un bénéficiaire.")
                else:
                    st.session_state.depenses_gite.append({"Payeur": payeur_gite, "Montant": val_g, "Cible": beneficiaires_gite})
                    st.success("Frais enregistré !")
                    st.rerun()
                
        if st.session_state.depenses_gite:
            st.write("---")
            for idx, dg in enumerate(st.session_state.depenses_gite):
                st.text(f"• {dg['Payeur']} a payé {dg['Montant']:.2f} € pour {len(dg.get('Cible', tous_participants))} pers.")
                if st.button("Supprimer cette facture", key=f"del_g_{idx}"):
                    st.session_state.depenses_gite.pop(idx)
                    st.rerun()
                    
        st.write("---")
        st.subheader("🏠 Nombre de nuits passées par personne (pour le prorata)")
        for p in tous_participants:
            st.session_state.nuits_data[p] = st.number_input(f"Nuits pour {p} :", min_value=0, value=int(st.session_state.nuits_data.get(p, 2)), key=f"n_s_{p}")

# =====================================================================
# --- SECTION 3 : NOURRITURE (FONCTIONNEL AVEC PETITS COMITÉS) ---
# =====================================================================
elif section_choisie == "🥑 3. Nourriture & Courses":
    if not tous_participants:
        st.info("💡 Ajoutez d'abord des participants dans la section 1.")
    else:
        col_n1, col_n2 = st.columns(2)
        payeur_nourr = col_n1.selectbox("Qui a payé les courses ?", tous_participants, key="p_nourr")
        frais_nourr_txt = col_n2.text_input("Montant des courses (€) :", value="0", key="txt_nourr_val")
        
        cible_nourr = st.radio("À qui profite cette dépense ?", ["🌍 Tout le collectif", "👥 Un petit comité / Individuels"], key="r_c_nourr")
        
        beneficiaires_nourr = []
        if cible_nourr == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les bénéficiaires de ces courses :**")
            for p in tous_participants:
                if st.checkbox(f"Mange du repas : {p}", value=True, key=f"nourr_cb_{p}"):
                    beneficiaires_nourr.append(p)
        else:
            beneficiaires_nourr = tous_participants.copy()
        
        if st.button("🥑 Enregistrer ces courses"):
            val_n = evaluer_operation(frais_nourr_txt)
            if val_n and val_n > 0:
                if not list(beneficiaires_nourr): st.error("Cochez au moins un bénéficiaire.")
                else:
                    st.session_state.depenses_nourriture.append({"Payeur": payeur_nourr, "Montant": val_n, "Cible": beneficiaires_nourr})
                    st.success("Courses enregistrées !")
                    st.rerun()
                
        if st.session_state.depenses_nourriture:
            st.write("---")
            for idx, dn in enumerate(st.session_state.depenses_nourriture):
                st.text(f"• {dn['Payeur']} a payé {dn['Montant']:.2f} € pour {len(dn.get('Cible', tous_participants))} pers.")
                if st.button("Supprimer ces courses", key=f"del_n_{idx}"):
                    st.session_state.depenses_nourriture.pop(idx)
                    st.rerun()
                    
        st.write("---")
        st.subheader("🥑 Nombre de repas consommés par personne")
        for p in tous_participants:
            st.session_state.repas_data[p] = st.number_input(f"Repas pour {p} :", min_value=0.0, value=float(st.session_state.repas_data.get(p, 4.0)), step=0.5, key=f"r_s_{p}")

# =====================================================================
# --- SECTION 4 : TRANSPORTS (L'ONGLET À FAIRE FONCTIONNER) ---
# =====================================================================
elif section_choisie == "🚗 4. Transports & Covoiturage":
