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

# Initialisation des variables du bandeau d'en-tête (Exemple Francheville)
if 'nom_sortie_manuel' not in st.session_state: st.session_state.nom_sortie_manuel = ""
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = "Exploration à Francheville"
if 'dept_sortie' not in st.session_state: st.session_state.dept_sortie = "21"
if 'type_act' not in st.session_state: st.session_state.type_act = "Exploration"
if 'cavites_sortie' not in st.session_state: st.session_state.cavites_sortie = "Fraisiers"

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
st.sidebar.subheader("⚙️ Zone de Danger")
if st.sidebar.button("🗑️ Réinitialiser toute la sortie"):
    st.session_state.presents_data = {}
    st.session_state.nuits_data = {}
    st.session_state.repas_data = {}
    st.session_state.nom_sortie_manuel = ""
    st.session_state.cavites_sortie = "Fraisiers"
    st.success("Toutes les données ont été effacées.")
    st.rerun()


# =====================================================================
# 🏛️ BANDEAU D'INFORMATIONS GENERALES DE LA SORTIE
# =====================================================================
st.markdown("### 🗺️ Fiche d'Information Sortie Officielle")
with st.expander("✏️ Cliquez ici pour modifier les informations générales de l'en-tête", expanded=False):
    col_b1, col_b2 = st.columns(2)
    date_debut = col_b1.date_input("Date de début du séjour :")
    date_fin = col_b2.date_input("Date de fin du séjour :")
    
    col_b3, col_b4, col_b5 = st.columns(3)
    st.session_state.cavites_sortie = col_b3.text_input("Liste des cavités visitées (séparées par une virgule) :", value=st.session_state.cavites_sortie)
    st.session_state.nom_sortie_manuel = col_b4.text_input("Nom de la sortie (Laisser vide pour prendre la 1ère cavité) :", value=st.session_state.nom_sortie_manuel)
    st.session_state.type_act = col_b5.selectbox(
        "Type d'activité :", 
        ["classique", "Exploration", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"],
        index=1 if st.session_state.type_act == "Exploration" else 0
    )
    
    col_b6, col_b7 = st.columns(2)
    st.session_state.dept_sortie = col_b6.text_input("N° département / Pays :", value=st.session_state.dept_sortie)
    st.session_state.lieu_gite = col_b7.text_input("Lieu du gîte :", value=st.session_state.lieu_gite)

# LOGIQUE DE CALCUL AUTOMATIQUE DU NOM PAR DEFAUT
# On extrait la première cavité saisie s'il n'y a pas de nom manuel défini
liste_cavites_I = [c.strip() for c in st.session_state.cavites_sortie.split(",") if c.strip()]
premiere_cavite = liste_cavites_I[0] if liste_cavites_I else "Sortie Sans Nom"

if st.session_state.nom_sortie_manuel.strip():
    nom_definitif_sortie = st.session_state.nom_sortie_manuel
else:
    nom_definitif_sortie = premiere_cavite

# Affichage du bandeau horizontal pour le suivi
st.info(
    f"🦇 **Sortie :** {nom_definitif_sortie} | "
    f"📅 **Dates :** Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')} | "
    f"📍 **Gîte :** {st.session_state.lieu_gite} ({st.session_state.dept_sortie}) | "
    f"⚙️ **Activité :** {st.session_state.type_act} | "
    f"🕳️ **Cavités :** {st.session_state.cavites_sortie}"
)
st.write("---")


st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# =====================================================================
# --- SECTION 1 : PARTICIPANTS ---
# =====================================================================
if section_choisie == "👥 1. Participants":
    st.subheader("Inscrivez les membres de la sortie")
    
    col_g, col_a, col_s = st.columns(3)
    genre_p = col_g.selectbox("Genre :", ["Homme", "Femme"])
    age_p = col_a.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
    statut_p = col_s.selectbox("Statut Club :", ["Membre club", "Débutant", "Fédéré", "Accompagnant"])
    
    ass_p = "Aucune"
    matos_p = False

    with st.form(key="form_saisie_speleo", clear_on_submit=True):
        saisie_brute = st.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        
        if statut_p == "Débutant":
            st.write("---")
            st.markdown("🎒 **Options obligatoires pour l'initiation du Débutant :**")
            col_opt1, col_opt2 = st.columns(2)
            ass_p = col_opt1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
            matos_p = col_opt2.checkbox("Prêt de matériel individuel club (5.00€)")
            
        st.write("---")
        bouton_valider = st.form_submit_button("➕ Enregistrer le participant")
        
        if bouton_valider and saisie_brute:
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots.capitalize()
                initiale_nom = mots[-1].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots.capitalize()
                
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if statut_p == "Débutant" else "Aucune",
                "Materiel": matos_p if statut_p == "Débutant" else False
            }
            
            st.session_state.nuits_data[nom_propre] = 2.0
            st.session_state.repas_data[nom_propre] = 4.0
            
            st.success(f"Fiche validée : {nom_propre} ({statut_p}) est inscrit !")
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres actuellement inscrits sur la sortie :")
        for p in tous_participants:
            info = st.session_state.presents_data[p]
            col_l1, col_l2 = st.columns()
            
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
    st.info("🚧 Étape par étape : Les sections suivantes s'ouvriront dès que ce bandeau révisé sera validé.")
