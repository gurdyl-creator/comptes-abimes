import streamlit as st
import datetime
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# --- DICTIONNAIRE DES DÉPARTEMENTS POUR AUTOCOMPLÉTION ---
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

# --- FONCTION CALCULATRICE INTÉGRÉE ---
def evaluer_operation(texte_formule):
    if not texte_formule:
        return 0.0
    formule_propre = str(texte_formule).replace(",", ".").replace(" ", "")
    if not re.match(r"^[0-9.+\s]*$", formule_propre):
        return None
    try:
        return float(eval(formule_propre, {"__builtins__" : None}, {}))
    except:
        return None

# --- INITIALISATION DE LA MEMOIRE DE SESSION ---
if 'participants' not in st.session_state: st.session_state.participants = {}
if 'factures_gite' not in st.session_state: st.session_state.factures_gite = []
if 'factures_nourriture' not in st.session_state: st.session_state.factures_nourriture = []

# Variables d'en-tête (Volet gauche précieux)
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = ""
if 'dept_saisie' not in st.session_state: st.session_state.dept_saisie = ""
if 'cavites' not in st.session_state: st.session_state.cavites = ""
if 'nom_manuel' not in st.session_state: st.session_state.nom_manuel = ""
if 'date_deb' not in st.session_state: st.session_state.date_deb = datetime.date(2026, 7, 4)
if 'date_f' not in st.session_state: st.session_state.date_f = datetime.date(2026, 7, 5)

# =====================================================================
# 🏛️ VOLET VERTICAL DE GAUCHE : INFORMATIONS SORTIE
# =====================================================================
st.sidebar.header("🦇 ABIMES")
st.sidebar.subheader("📋 Informations Sortie")

st.session_state.date_deb = st.sidebar.date_input("Date de début :", value=st.session_state.date_deb, format="DD/MM/YYYY")
st.session_state.date_f = st.sidebar.date_input("Date de fin :", value=st.session_state.date_f, format="DD/MM/YYYY")

st.session_state.cavites = st.sidebar.text_input("Cavités :", value=st.session_state.cavites, placeholder="Abimes des Fraisiers")
st.session_state.nom_manuel = st.sidebar.text_input("Nom de la sortie :", value=st.session_state.nom_manuel)

type_act = st.sidebar.selectbox("Type d'activité :", ["classique", "Exploration", "formation/entrainement", "plongée", "secours", "scientifique", "canyon", "réunion"], index=1)

dept_input = st.sidebar.text_input("N° département / Pays :", value=st.session_state.dept_saisie, placeholder="21, Côte d'Or").strip()
if dept_input and "," not in dept_input:
    code = dept_input.upper()
    if code in DICTIONNAIRE_DEP:
        dept_input = f"{code}, {DICTIONNAIRE_DEP[code]}"
st.session_state.dept_saisie = dept_input

st.session_state.lieu_gite = st.sidebar.text_input("Lieu du gîte :", value=st.session_state.lieu_gite, placeholder="Le Fabilie, Val-Suzon")

nom_sortie = st.session_state.nom_manuel if st.session_state.nom_manuel.strip() else (st.session_state.cavites.split(",")[0].strip() if st.session_state.cavites.strip() else "Abimes des Fraisiers")

st.sidebar.write("---")
st.sidebar.markdown("### 🗂️ Fiche Récapitulative")
st.sidebar.info(
    f"🦇 **Sortie :** {nom_sortie}\n\n"
    f"📅 **Dates :** Du {st.session_state.date_deb.strftime('%d/%m/%Y')} au {st.session_state.date_f.strftime('%d/%m/%Y')}\n\n"
    f"📍 **Gîte :** {st.session_state.lieu_gite if st.session_state.lieu_gite else 'Le Fabilie, Val-Suzon'} ({st.session_state.dept_saisie if st.session_state.dept_saisie else '21, Côte d\'Or'})\n\n"
    f"⚙️ **Activité :** {type_act}\n\n"
    f"🕳️ **Cavités :** {st.session_state.cavites if st.session_state.cavites else 'Abimes des Fraisiers'}"
)

if st.sidebar.button("🗑️ Réinitialiser tout"):
    st.session_state.participants = {}
    st.session_state.factures_gite = []
    st.session_state.factures_nourriture = []
    st.rerun()

# =====================================================================
# 🧭 ZONE CENTRALE : NAVIGATION HORIZONTALE PAR ONGLETS (TABS)
# =====================================================================
onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs([
    "👥 1. Participants", 
    "🏠 2. Logement & Gîte", 
    "🥑 3. Nourriture & Courses", 
    "🚗 4. Transports & Covoiturage",
    "📊 5. Bilan Global"
])

list_p = list(st.session_state.participants.keys())

# --- ONGLETS 1 : PARTICIPANTS ---
with onglet1:
    st.subheader("👥 Saisie des participants")
    
    statut = st.selectbox("Statut Club :", ["Membre club", "Débutant", "Fédéré", "Accompagnant"], key="sel_statut")
    
    with st.form(key="formulaire_ajout_speleo", clear_on_submit=True):
        col_n, col_g, col_a = st.columns(3)
        nom_saisi = col_n.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        genre = col_g.selectbox("Genre :", ["Homme", "Femme"])
        age = col_a.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
        
        assurance = "Aucune"
        matos = False
        
        if statut == "Débutant":
            st.write("---")
            col_o1, col_o2 = st.columns(2)
            assurance = col_o1.selectbox("Assurance Temporaire FFS :", ["Aucune", "1 Jour (7.20€)", "3 Jours (15.50€)"])
            matos = col_o2.checkbox("Prêt de matériel club (5.00€)")
            
        bouton_valider = st.form_submit_button("➕ Enregistrer le participant")
        
        if bouton_valider and nom_saisi.strip():
            mots = nom_saisi.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                nom_propre = f"{prenom} {mots[-1].upper()}"
            else:
                nom_propre = nom_saisi.strip().capitalize()
                
            st.session_state.participants[nom_propre] = {
                "Genre": genre, "Age": age, "Statut": statut, "Assurance": assurance, "Materiel": matos,
                "Nuits": 2.0, "Repas": 4.0
            }
            st.rerun()

    if list_p:
        st.write("---")
        st.subheader("Membres actuellement inscrits")
        for p in list_p:
            info = st.session_state.participants[p]
            col_t, col_b = st.columns([4, 1])
            col_t.text(f"• {p} | {info['Statut']} | {info['Genre']} | {info['Age']}")
            if col_b.button("🗑️ Supprimer", key=f"del_{p}"):
                del st.session_state.participants[p]
                st.rerun()

# --- ONGLETS 2 : LOGEMENT & GÎTE ---
with onglet2:
    st.subheader("🏠 Frais de Logement")
    if not list_p:
        st.info("💡 Ajoutez d'abord des participants dans le premier onglet.")
    else:
        col_p, col_m = st.columns(2)
        payeur = col_p.selectbox("Qui a avancé l'argent du gîte ?", list_p, key="payeur_gite")
        montant_txt = col_m.text_input("Montant de la facture (€) :", value="0", key="txt_gite")
        
        if st.button("Enregistrer facture gîte", key="btn_save_gite"):
            val_g = evaluer_operation(montant_txt)
            if val_g and val_g > 0:
                st.session_state.factures_gite.append({"Payeur": payeur, "Montant": val_g})
                st.success("Facture de gîte enregistrée !")
                st.rerun()
                
        if st.session_state.factures_gite:
            st.write("---")
            for idx, dg in enumerate(st.session_state.factures_gite):
                col_txt, col_del = st.columns([4, 1])
                col_txt.write(f"• {dg['Payeur']} a payé {dg['Montant']:.2f} €")
                if col_del.button("Supprimer", key=f"del_g_{idx}"):
                    st.session_state.factures_gite.pop(idx)
                    st.rerun()
                    
        st.write("---")
        st.subheader("🏠 Nombre de nuitées passées par personne")
        for p in list_p:
            st.session_state.participants[p]["Nuits"] = st.number_input(f"Nuitées pour {p} :", min_value=0.0, value=float(st.session_state.participants[p]["Nuits"]), step=0.5, key=f"nuits_{p}")

# --- ONGLETS 3 : NOURRITURE ---
