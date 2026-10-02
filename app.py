import streamlit as st
import datetime
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- DICTIONNAIRE DES DÉPARTEMENTS FRANÇAIS ET PAYS ABIMES ---
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
    "94": "Val-de-Marne", "95": "Val-d'Oise", "BE": "Belgique", "CH": "Suisse",
    "ES": "Espagne", "IT": "Italie", "GR": "Grèce"
}

# --- INITIALISATION SÉCURISÉE DE LA SESSION ---
if 'nom_sortie_manuel' not in st.session_state: st.session_state.nom_sortie_manuel = ""
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = ""
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

# Saisie des dates au format JJ/MM/AAAA
dates_saisies = st.sidebar.date_input("Dates du séjour (Début et Fin) :", value=st.session_state.dates_weekend)
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

# Saisie du département avec placeholder en gris
saisie_departement = st.sidebar.text_input(
    "N° département / Pays :",
    value=st.session_state.dept_saisie_brute,
    placeholder="21, Côte d'Or"
).strip()

# Analyse de la saisie pour l'autocomplétion
dept_formate = saisie_departement
if saisie_departement:
    parties = [p.strip() for p in saisie_departement.split(",") if p.strip()]
    if parties:
        code_isole = parties[0]
        if code_isole in DICTIONNAIRE_DEP and "," not in saisie_departement:
            dept_formate = f"{code_isole}, {DICTIONNAIRE_DEP[code_isole]}"

st.session_state.dept_saisie_brute = dept_formate

# FIX VISUEL : Intégration du placeholder en gris indicatif dans la case lieu du gîte
st.session_state.lieu_gite = st.sidebar.text_input(
    "Lieu du gîte :", 
    value=st.session_state.lieu_gite,
    placeholder="Le Fabilie, Val-Suzon"
)

# Logique du nom de sortie par défaut
liste_cavites = [c.strip() for c in st.session_state.cavites_sortie.split(",") if c.strip()]
premiere_cavite = liste_cavites[0] if liste_cavites else "Abimes des Fraisiers"

if st.session_state.nom_sortie_manuel.strip():
    nom_definitif_sortie = st.session_state.nom_sortie_manuel
else:
    nom_definitif_sortie = premiere_cavite

# Formatage des dates pour la fiche
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
    f"📍 **Gîte :** {st.session_state.lieu_gite if st.session_state.lieu_gite else 'Le Fabilie, Val-Suzon'} ({st.session_state.dept_saisie_brute if st.session_state.dept_saisie_brute else '21, Côte d\'Or'})\n\n"
    f"⚙️ **Activité :** {st.session_state.type_act}\n\n"
    f"🕳️ **Cavités :** {st.session_state.cavites_sortie if st.session_state.cavites_sortie else 'Abimes des Fraisiers'}"
)

# =====================================================================
# ZONE CENTRALE EN ATTENTE STRICTE
# =====================================================================
st.title("🦇 ABIMES - Mode Focus En-tête")
st.info("🚧 La zone centrale et les onglets horizontaux sont temporairement bloqués le temps de valider à 100 % ce volet Informations Sortie.")
