import streamlit as st
import datetime
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- BARÈMES OFFICIELS ABIMES ---
IK_STANDARD = 0.15

# --- FONCTION CALCULATRICE INTÉGRÉE ---
def evaluer_operation(texte_formule):
    if not texte_formule:
        return 0.0
    formule_propre = texte_formule.replace(",", ".").replace(" ", "")
    if not re.match(r"^[0-9.+\s]*$", formule_propre):
        return None
    try:
        return float(eval(formule_propre, {"__builtins__" : None}, {}))
    except:
        return None

# --- INITIALISATION SÉCURISÉE DE LA SESSION ---
if 'presents_data' not in st.session_state: st.session_state.presents_data = {}
if 'nuits_data' not in st.session_state: st.session_state.nuits_data = {}
if 'repas_data' not in st.session_state: st.session_state.repas_data = {}
if 'depenses_gite' not in st.session_state: st.session_state.depenses_gite = []

# Initialisation des variables de l'en-tête (Exemple Francheville)
if 'nom_sortie_manuel' not in st.session_state: st.session_state.nom_sortie_manuel = ""
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = "Exploration à Francheville"
if 'dept_sortie' not in st.session_state: st.session_state.dept_sortie = "21"
if 'type_act' not in st.session_state: st.session_state.type_act = "Exploration"
if 'cavites_sortie' not in st.session_state: st.session_state.cavites_sortie = "Fraisiers"

# Initialisation des dates par défaut (04 au 05 juillet 2026) sous forme de liste pour la période
if 'dates_weekend' not in st.session_state:
    st.session_state.dates_weekend = [datetime.date(2026, 7, 4), datetime.date(2026, 7, 5)]

# =====================================================================
# 🏛️ VOLET VERTICAL DE GAUCHE : CONFIGURATION & FICHE D'INFORMATION
# =====================================================================
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
st.sidebar.subheader("🗺️ Configuration de la Sortie")

# CORRECTION DU SÉLECTEUR DE PÉRIODE : C'est le fait de donner une liste de 2 dates à value 
# qui active automatiquement le mode période ("range") sans provoquer de TypeError.
dates_saisies = st.sidebar.date_input(
    "Dates du séjour (Début et Fin) :", 
    value=st.session_state.dates_weekend
)
st.session_state.dates_weekend = dates_saisies

st.session_state.cavites_sortie = st.sidebar.text_input("Cavités (séparées par une virgule) :", value=st.session_state.cavites_sortie)
st.session_state.nom_sortie_manuel = st.sidebar.text_input("Nom de la sortie (ou vide) :", value=st.session_state.nom_sortie_manuel)
st.sidebar.caption("Laissez vide pour prendre le nom de la 1ère cavité")

st.session_state.type_act = st.sidebar.selectbox(
    "Type d'activité :", 
    ["classique", "Exploration", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"],
    index=1 if st.session_state.type_act == "Exploration" else 0
)
st.session_state.dept_sortie = st.sidebar.text_input("N° département / Pays :", value=st.session_state.dept_sortie)
st.session_state.lieu_gite = st.sidebar.text_input("Lieu du gîte :", value=st.session_state.lieu_gite)

# Logique du nom de sortie par défaut
liste_cavites = [c.strip() for c in st.session_state.cavites_sortie.split(",") if c.strip()]
premiere_cavite = liste_cavites[0] if liste_cavites else "Sortie Sans Nom"

if st.session_state.nom_sortie_manuel.strip():
    nom_definitif_sortie = st.session_state.nom_sortie_manuel
else:
    nom_definitif_sortie = premiere_cavite

# Sécurité d'affichage de la période selon la saisie de l'utilisateur
if isinstance(st.session_state.dates_weekend, (list, tuple)) and len(st.session_state.dates_weekend) == 2:
    str_debut = st.session_state.dates_weekend[0].strftime('%d/%m/%Y')
    str_fin = st.session_state.dates_weekend[1].strftime('%d/%m/%Y')
    texte_dates = f"Du {str_debut} au {str_fin}"
elif isinstance(st.session_state.dates_weekend, (list, tuple)) and len(st.session_state.dates_weekend) == 1:
    str_debut = st.session_state.dates_weekend[0].strftime('%d/%m/%Y')
    texte_dates = f"À partir du {str_debut} (Sélectionnez la fin)"
else:
    # Cas où l'utilisateur saisit une date unique au lieu d'une période
    try:
        str_debut = st.session_state.dates_weekend.strftime('%d/%m/%Y')
        texte_dates = f"Le {str_debut}"
    except:
        texte_dates = "Dates non définies"

st.sidebar.write("---")
st.sidebar.markdown("### 🗂️ Fiche Récapitulative")
st.sidebar.info(
    f"🦇 **Sortie :** {nom_definitif_sortie}\n\n"
    f"📅 **Dates :** {texte_dates}\n\n"
    f"📍 **Gîte :** {st.session_state.lieu_gite} ({st.session_state.dept_sortie})\n\n"
    f"⚙️ **Activité :** {st.session_state.type_act}\n\n"
    f"🕳️ **Cavités :** {st.session_state.cavites_sortie}"
)

st.sidebar.write("---")
st.sidebar.subheader("⚙️ Zone de Danger")
if st.sidebar.button("🗑️ Réinitialiser toute la sortie"):
    st.session_state.presents_data = {}
    st.session_state.nuits_data = {}
    st.session_state.repas_data = {}
    st.session_state.depenses_gite = []
    st.session_state.nom_sortie_manuel = ""
    st.session_state.cavites_sortie = "Fraisiers"
    st.success("Données effacées.")
    st.rerun()

# =====================================================================
# ZONE CENTRALE DE TRAVAIL
# =====================================================================
st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# --- SECTION 1 : PARTICIPANTS ---
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
                prenom = mots[0].capitalize()
                initiale_nom = mots[-1].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
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
            col_l1, col_l2 = st.columns(2)
            
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

# --- SECTION 2 : LOGEMENT & GÎTE ---
elif section_choisie == "🏠 2. Logement & Gîte":
    if not tous_participants:
        st.info("💡 Ajoutez d'abord des participants dans la section 1 pour débloquer la gestion de l'hébergement.")
    else:
        st.subheader("Déclarer une facture de Logement / Hébergement")
        col_g1, col_g2 = st.columns(2)
        payeur_gite = col_g1.selectbox("Qui a avancé les frais du gîte ?", tous_participants, key="p_gite")
        frais_gite_txt = col_g2.text_input("Montant total payé pour le gîte (€) :", value="0", key="txt_gite_val")
        
        cible_gite = st.radio("À qui s'applique cette facture d'hébergement ?", ["🌍 Tout le collectif présent", "👥 Un petit comité / Individuels"], key="r_c_gite")
        
        beneficiaires_gite = []
        if cible_gite == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les spéléos concernés par cette ligne :**")
            for p in tous_participants:
                if st.checkbox(f"A dormi au gîte : {p}", value=True, key=f"gite_cb_{p}"):
                    beneficiaires_gite.append(p)
        else:
