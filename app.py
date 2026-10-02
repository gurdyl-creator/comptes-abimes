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
# --- SECTION 1 : PARTICIPANTS (AFFICHAGE ULTRA-DYNAMIQUE) ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres de la sortie")
    
    # 1. On affiche d'abord les menus de profil pour capter le choix du statut en direct
    col_g, col_a, col_s = st.columns(3)
    genre_p = col_g.selectbox("Genre :", ["Homme", "Femme"])
    age_p = col_a.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
    statut_p = col_s.selectbox("Statut Club :", ["Membre club", "Débutant", "Fédéré", "Accompagnant"])
    
    # Variables de secours par défaut
    ass_p = "Aucune"
    matos_p = False

    # 2. Le formulaire de saisie du prénom s'adapte en fonction du statut choisi au-dessus
    with st.form(key="form_saisie_speleo", clear_on_submit=True):
        
        saisie_brute = st.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        
        # EFFET MAGIQUE : On ne dessine ces lignes QUE si le statut est Débutant
        if statut_p == "Débutant":
            st.write("---")
            st.markdown("🎒 **Options obligatoires pour l'initiation du Débutant :**")
            col_opt1, col_opt2 = st.columns(2)
            ass_p = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
            matos_p = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")
            
        st.write("---")
        bouton_valider = st.form_submit_button("➕ Enregistrer le participant")
        
        if bouton_valider and saisie_brute:
            # Formatage automatique au format "Prénom N"
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[-1][0].upper()  # Première lettre du nom de famille
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            # Enregistrement en mémoire
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if statut_p == "Débutant" else "Aucune",
                "Materiel": matos_p if statut_p == "Débutant" else False
            }
            
            # Initialisations par défaut
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
    st.info("🚧 Étape par étape : Les sections suivantes s'ouvriront dès que ce comportement d'affichage dynamique sera validé.")
