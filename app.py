import streamlit as st
import pandas as pd
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- BARÈMES OFFICIELS ABIMES ---
IK_STANDARD = 0.15
SUBV_KM = 0.02

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
if 'depenses_gite' not in st.session_state: st.session_state.depenses_gite = []
if 'nuits_data' not in st.session_state: st.session_state.nuits_data = {}

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
nom_sortie = st.sidebar.text_input("Nom de la sortie :", "Hotton")
date_debut = st.sidebar.date_input("Date de début :")
st.sidebar.info(f"📅 Date : {date_debut.strftime('%d/%m/%Y')}")
gite_lieu = st.sidebar.text_input("Lieu du gîte :", "Hotton")

st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# --- SECTION 1 : PARTICIPANTS ---
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres (Format : Jean Dupont)")
    
    with st.form(key="formulaire_participant", clear_on_submit=True):
        saisie_brute = st.text_input("Prénom et Nom :")
        bouton_valider = st.form_submit_button("➕ Enregistrer")
        
        if bouton_valider and saisie_brute:
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[1][0].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            st.session_state.presents_data[nom_propre] = True
            st.success(f"Format validé : {nom_propre} est inscrit !")
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres inscrits")
        for p in tous_participants:
            col_l1, col_l2 = st.columns(2)
            col_l1.text(f"• {p}")
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.session_state.nuits_data.pop(p, None)
                st.rerun()

# --- SECTION 2 : LOGEMENT (DÉBLOQUÉE EN MODE PAS-À-PAS) ---
elif section_choisie == "🏠 2. Logement & Gîte":
    if not tous_participants:
        st.info("💡 Ajoutez d'abord des participants dans la section 1.")
    else:
        st.subheader("Déclarer les frais d'hébergement")
        col_g1, col_g2 = st.columns(2)
        payeur_gite = col_g1.selectbox("Qui a payé le gîte ?", tous_participants, key="p_gite")
        frais_gite_txt = col_g2.text_input("Montant total payé (€) :", value="0", key="txt_gite_val")
        
        cible_gite = st.radio("À qui s'applique cette facture ?", ["🌍 Tout le collectif", "👥 Liste des bénéficiaires"], key="r_c_gite")
        
        beneficiaires_gite = []
        if cible_gite == "👥 Liste des bénéficiaires":
            st.write("👉 **Cochez uniquement les bénéficiaires de cette nuitée :**")
            for p in tous_participants:
                if st.checkbox(f"A dormi au gîte : {p}", value=True, key=f"gite_cb_{p}"):
                    beneficiaires_gite.append(p)
        else:
            beneficiaires_gite = tous_participants.copy()
            
        if st.button("🏠 Enregistrer cette dépense"):
            val_g = evaluer_operation(frais_gite_txt)
            if val_g and val_g > 0:
                if not beneficiaires_gite: st.error("Cochez au moins un bénéficiaire.")
                else:
                    st.session_state.depenses_gite.append({"Payeur": payeur_gite, "Montant": val_g, "Cible": beneficiaires_gite})
                    st.success("Dépense de gîte enregistrée !")
                    st.rerun()
                    
        if st.session_state.depenses_gite:
            st.write("---")
            st.subheader("Historique Logement")
            for idx, dg in enumerate(st.session_state.depenses_gite):
                st.text(f"• {dg['Payeur']} a payé {dg['Montant']:.2f} € pour {len(dg['Cible'])} pers.")
                if st.button("Supprimer", key=f"del_g_{idx}"):
                    st.session_state.depenses_gite.pop(idx)
                    st.rerun()

        st.write("---")
        st.subheader("🏠 Nombre de nuitées par personne")
        for p in tous_participants:
            st.session_state.nuits_data[p] = st.number_input(f"Nuitées pour {p} :", min_value=0.0, value=float(st.session_state.nuits_data.get(p, 2.0)), step=0.5, key=f"n_s_{p}")

# --- SECTIONS SUIVANTES EN ATTENTE PROPRE ---
else:
    st.info("🚧 Étape par étape : Les sections suivantes sont en attente le temps de valider la grille d'hébergement.")
