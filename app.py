import streamlit as st

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
# --- SECTION 1 : PARTICIPANTS (SÉCURISÉE SANS CONFLIT DE WIDGET) ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres de la sortie")
    
    # Utilisation d'un vrai st.form : la SEULE méthode propre pour que la touche Entrée 
    # fonctionne ET que la case se vide instantanément (clear_on_submit=True) sans aucun bug
    with st.form(key="formulaire_speleo_abimes", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        
        saisie_brute = col1.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        genre_p = col2.selectbox("Genre :", ["Homme", "Femme"])
        age_p = col3.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
        statut_p = col4.selectbox("Statut Club :", ["Membre club", "Débutant", "Fédéré", "Accompagnant"])
        
        st.write("---")
        st.caption("🎒 **Options d'initiation (Prises en compte UNIQUEMENT pour le statut Débutant) :**")
        col_opt1, col_opt2 = st.columns(2)
        ass_p = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
        matos_p = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")
        
        bouton_valider = st.form_submit_button("➕ Enregistrer le participant")
        
        if bouton_valider and saisie_brute:
            # Formatage automatique au format "Prénom N"
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[-1].upper()[0]  # On prend la première lettre du nom
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            # Enregistrement strict selon les profils validés
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if statut_p == "Débutant" else "Aucune",
                "Materiel": matos_p if statut_p == "Débutant" else False
            }
            
            # Initialisations par défaut pour la suite
            st.session_state.nuits_data[nom_propre] = 2.0
            st.session_state.repas_data[nom_propre] = 4.0
            
            st.success(f"Fiche validée : {nom_propre} ({statut_p}) est inscrit !")
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres actuellement inscrits sur la sortie :")
        for p in tous_participants:
            info = st.session_state.presents_data[p]
            col_l1, col_l2 = st.columns([4, 1])
            
            # Affichage des détails d'assurance uniquement s'il est Débutant
            if info['Statut'] == "Débutant":
                details_init = f" (Assurance: {info['Assurance']} | Matos: {'Oui' if info['Materiel'] else 'Non'})"
            else:
                details_init = ""
                
            col_l1.text(f"• {p} | {info['Genre']} | {info['Age']} | Statut : {info['Statut']}{details_init}")
            
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.session_state.nuits_data.pop(p, None)
                st.session_state.repas_data.pop(p, None)
                st.rerun()

# --- SECTIONS SUIVANTES EN ATTENTE PROPRE ---
else:
    st.info("🚧 Étape par étape : Les sections suivantes s'ouvriront dès que cette structure de profils sans bug sera entièrement validée de votre côté.")
