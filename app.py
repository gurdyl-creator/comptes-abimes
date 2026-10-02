import streamlit as st
import datetime
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- BARÈMES OFFICIELS ABIMES ---
IK_STANDARD = 0.15

# --- DICTIONNAIRE DES DÉPARTEMENTS FRANÇAIS POUR AUTOCLAVAGE ---
DICTIONNAIRE_DEP = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube",
    "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal",
    "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault",
    "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura",
    "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique",
    "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire",
    "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle",
    "55": "Meuse", "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône",
    "70": "Haute-Saône", "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres",
    "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse",
    "85": "Vendée", "86": "Vienne", "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne",
    "90": "Territoire de Belfort", "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise", "971": "Guadeloupe", "972": "Martinique",
    "973": "Guyane", "974": "La Réunion", "976": "Mayotte", "BE": "Belgique", "CH": "Suisse",
    "ES": "Espagne", "IT": "Italie", "GR": "Grèce"
}

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

# Initialisation des variables de l'en-tête
if 'nom_sortie_manuel' not in st.session_state: st.session_state.nom_sortie_manuel = ""
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = "Exploration à Francheville"
if 'dept_saisie_brute' not in st.session_state: st.session_state.dept_saisie_brute = ""
if 'type_act' not in st.session_state: st.session_state.type_act = "Exploration"
if 'cavites_sortie' not in st.session_state: st.session_state.cavites_sortie = ""
if 'dates_weekend' not in st.session_state:
    st.session_state.dates_weekend = [datetime.date(2026, 7, 4), datetime.date(2026, 7, 5)]

# =====================================================================
# 🏛️ VOLET VERTICAL DE GAUCHE : UNIQUEMENT LES INFORMATIONS SORTIE
# =====================================================================
st.sidebar.header("🦇 ABIMES")
st.sidebar.subheader("📋 Informations Sortie")

# Saisie des dates configurées au format JJ/MM/AAAA
dates_saisies = st.sidebar.date_input(
    "Dates du séjour (Début et Fin) :", 
    value=st.session_state.dates_weekend
)
st.session_state.dates_weekend = dates_saisies

st.session_state.cavites_sortie = st.sidebar.text_input(
    "Cavités (séparées par une virgule) :", 
    value=st.session_state.cavites_sortie,
    placeholder="Abimes des Fraisiers"
)

st.session_state.nom_sortie_manuel = st.sidebar.text_input("Nom de la sortie (ou vide) :", value=st.session_state.nom_sortie_manuel)
st.sidebar.caption("Laissez vide pour prendre le nom de la 1ère cavité")

st.session_state.type_act = st.sidebar.selectbox(
    "Type d'activité :", 
    ["classique", "Exploration", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"],
    index=1 if st.session_state.type_act == "Exploration" else 0
)

# FIX VISUEL ET AUTOMATIQUE : Saisie du département avec placeholder explicite
saisie_departement = st.sidebar.text_input(
    "N° département / Pays :",
    value=st.session_state.dept_saisie_brute,
    placeholder="21, Côte d'Or"
).strip()

# Analyse dynamique de la saisie pour ajouter automatiquement le nom du département
dept_formate = saisie_departement
if saisie_departement:
    # On isole les premiers caractères au cas où l'utilisateur tape juste le numéro (ex: "21")
    code_isole = saisie_departement.split(",")[0].strip()
    # Si le code est dans notre dictionnaire et que le nom n'est pas déjà écrit, on l'autocomplète
    if code_isole in DICTIONNAIRE_DEP and "," not in saisie_departement:
        dept_formate = f"{code_isole}, {DICTIONNAIRE_DEP[code_isole]}"

st.session_state.dept_saisie_brute = dept_formate
st.session_state.lieu_gite = st.sidebar.text_input("Lieu du gîte :", value=st.session_state.lieu_gite)

# Logique du nom de sortie par défaut
liste_cavites = [c.strip() for c in st.session_state.cavites_sortie.split(",") if c.strip()]
premiere_cavite = liste_cavites[0] if liste_cavites else "Abimes des Fraisiers"

if st.session_state.nom_sortie_manuel.strip():
    nom_definitif_sortie = st.session_state.nom_sortie_manuel
else:
    nom_definitif_sortie = premiere_cavite

# Formatage en JJ/MM/AAAA pour la fiche récapitulative
str_debut = st.session_state.date_debut.strftime('%d/%m/%Y') if hasattr(st.session_state, 'date_debut') else ""
if isinstance(st.session_state.dates_weekend, (list, tuple)) and len(st.session_state.dates_weekend) == 2:
    str_debut = st.session_state.dates_weekend[0].strftime('%d/%m/%Y')
    str_fin = st.session_state.dates_weekend[1].strftime('%d/%m/%Y')
    texte_dates = f"Du {str_debut} au {str_fin}"
else:
    texte_dates = "Dates en cours de sélection"

st.sidebar.write("---")
st.sidebar.markdown("### 🗂️ Fiche Récapitulative")
st.sidebar.info(
    f"🦇 **Sortie :** {nom_definitif_sortie}\n\n"
    f"📅 **Dates :** {texte_dates}\n\n"
    f"📍 **Gîte :** {st.session_state.lieu_gite} ({st.session_state.dept_saisie_brute if st.session_state.dept_saisie_brute else '21, Côte d\'Or'})\n\n"
    f"⚙️ **Activité :** {st.session_state.type_act}\n\n"
    f"🕳️ **Cavités :** {st.session_state.cavites_sortie if st.session_state.cavites_sortie else 'Abimes des Fraisiers'}"
)

st.sidebar.write("---")
if st.sidebar.button("🗑️ Réinitialiser tout"):
    st.session_state.presents_data = {}
    st.session_state.nuits_data = {}
    st.session_state.repas_data = {}
    st.session_state.depenses_gite = []
    st.session_state.nom_sortie_manuel = ""
    st.session_state.cavites_sortie = ""
    st.session_state.dept_saisie_brute = ""
    st.success("Données effacées.")
    st.rerun()

# =====================================================================
# 🧭 ZONE CENTRALE : NAVIGATION HORIZONTALE PAR ONGLETS (TABS)
# =====================================================================
onglets_principaux = st.tabs([
    "👥 1. Participants", 
    "🏠 2. Logement & Gîte", 
    "🥑 3. Nourriture & Courses", 
    "🚗 4. Transports & Covoiturage", 
    "📸 5. Justificatifs & Tickets", 
    "📈 6. Visualisation",
    "📊 7. Bilan Global"
])

tous_participants = list(st.session_state.presents_data.keys())

# --- ONGLET 1 : PARTICIPANTS ---
with onglets_principaux[0]:
    st.subheader("Saisie des participants de la sortie")
    
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
                initiale_nom = mots[-1].upper()[0]
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            st.session_state.presents_data[nom_propre] = {
                "Genre": genre_p,
                "Age": age_p,
                "Statut": statut_p,
                "Assurance": ass_p if statut_p == "Débutant" else "Aucune",
