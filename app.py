import streamlit as st
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- INITIALISATION SÉCURISÉE DE LA SESSION ---
if 'presents_data' not in st.session_state: 
    st.session_state.presents_data = {}
if 'nuits_data' not in st.session_state: 
    st.session_state.nuits_data = {}
if 'repas_data' not in st.session_state: 
    st.session_state.repas_data = {}

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

st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# =====================================================================
# --- SECTION 1 : PARTICIPANTS (INTERACTIVE ET CORRIGÉE) ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres de la sortie (Validation par Entrée ou Bouton)")
    
    with st.form(key="formulaire_participant", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        
        saisie_brute = col1.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        genre_p = col2.selectbox("Genre :", ["Homme", "Femme"])
        age_p = col3.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
        statut_p = col4.selectbox("Statut Club :", ["Membre Club", "Initié / Non-membre"])
        
        # AJUSTEMENT ERGONOMIQUE : Les options FFS s'affichent uniquement pour un non-membre
        # Comme tout est dans un bloc st.form, on utilise un st.checkbox ou selectbox dynamique
        # Pour une réactivité parfaite dans un formulaire Streamlit, nous laissons les options
        # se valider au moment de la soumission globale.
        st.write("---")
        st.caption("🎒 Options d'initiation (Prises en compte uniquement si Statut = Initié / Non-membre) :")
        col_opt1, col_opt2 = st.columns(2)
        ass_p = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
        matos_p = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")
        
        bouton_valider = st.form_submit_button("➕ Enregistrer le participant")
        
        if bouton_valider and saisie_brute:
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[1][0].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            # Clivage des données selon le statut réel choisi
            est_initie = (statut_p == "Initié / Non-membre")
            
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if est_initie else "Aucune",
                "Materiel": matos_p if est_initie else False
            }
            
            st.session_state.nuits_data[nom_propre] = 2.0
            st.session_state.repas_data[nom_propre] = 4.0
            
            st.success(f"Fiche validée : {nom_propre} est inscrit !")
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres actuellement inscrits sur la sortie :")
        for p in tous_participants:
            info = st.session_state.presents_data[p]
            col_l1, col_l2 = st.columns([5, 1])
            
            # Affichage clair et formaté de la ligne
            texte_matos = "Oui" if info['Materiel'] else "Non"
            col_l1.text(f"• {p} | {info['Genre']} | {info['Age']} | {info['Statut']} (Assurance: {info['Assurance']} | Matos: {texte_matos})")
            
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.session_state.nuits_data.pop(p, None)
                st.session_state.repas_data.pop(p, None)
                st.rerun()

# --- SECTIONS SUIVANTES EN ATTENTE PROPRE ---
else:
    st.info("🚧 Étape par étape : Les sections suivantes rouvriront dès que cette fiche d'inscription complète sera validée.")
