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
# --- SECTION 1 : PARTICIPANTS (4 STATUTS CHRONO-COMPATIBLES) ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres de la sortie")
    
    # Zone de saisie dynamique hors formulaire pour la réactivité visuelle
    col1, col2, col3, col4 = st.columns(4)
    saisie_brute = col1.text_input("Prénom et Nom (ex: Arthur Perrin) :", key="saisie_nom_unique")
    genre_p = col2.selectbox("Genre :", ["Homme", "Femme"])
    age_p = col3.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
    
    # Intégration des 4 statuts officiels d'ABIMES
    statut_p = col4.selectbox(
        "Statut Club :", 
        [
            "Membre club", 
            "Débutant", 
            "Fédéré", 
            "Accompagnant"
        ]
    )
    
    # Initialisation des variables par défaut
    ass_p = "Aucune"
    matos_p = False
    
    # Affichage conditionnel strict : uniquement pour le statut "Débutant"
    if statut_p == "Débutant":
        st.write("---")
        st.caption("🎒 **Options obligatoires pour l'initiation du Débutant :**")
        col_opt1, col_opt2 = st.columns(2)
        ass_p = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
        matos_p = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")
        
    st.write("---")
    
    # Bouton d'enregistrement
    if st.button("➕ Enregistrer le participant") or (st.session_state.saisie_nom_unique and st.session_state.get('last_saisie') != st.session_state.saisie_nom_unique):
        if saisie_brute:
            # Enregistrement du nom pour éviter les doubles déclenchements avec Entrée
            st.session_state['last_saisie'] = saisie_brute
            
            # Formatage "Prénom N" automatique
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[-1][0].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            # Stockage de la fiche profil
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if statut_p == "Débutant" else "Aucune",
                "Materiel": matos_p if statut_p == "Débutant" else False
            }
            
            # Initialisations annexes par défaut
            st.session_state.nuits_data[nom_propre] = 2.0
            st.session_state.repas_data[nom_propre] = 4.0
            
            st.success(f"Fiche validée : {nom_propre} ({statut_p}) est inscrit !")
            # Petite astuce pour vider le champ texte après validation
            st.session_state.saisie_nom_unique = ""
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres actuellement inscrits sur la sortie :")
        for p in tous_participants:
            info = st.session_state.presents_data[p]
            col_l1, col_l2 = st.columns([4, 1])
            
            # Affichage personnalisé de la ligne selon le profil
            if info['Statut'] == "Débutant":
                details_init = f" (Assurance: {info['Assurance']} | Matos: {'Oui' if info['Materiel'] else 'Non'})"
            else:
                details_init = ""
                
            col_l1.text(f"• {p} | {info['Genre']} | {info['Age']} | Statut: {info['Statut']}{details_init}")
            
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.session_state.nuits_data.pop(p, None)
                st.session_state.repas_data.pop(p, None)
                st.rerun()

# --- SECTIONS SUIVANTES EN ATTENTE PROPRE ---
else:
    st.info("🚧 Étape par étape : Les sections suivantes s'ouvriront dès que cette structure de profils sera entièrement validée de votre côté.")
