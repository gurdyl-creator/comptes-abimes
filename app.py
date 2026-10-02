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

# Variables de l'en-tête vertical de gauche
if 'nom_sortie_manuel' not in st.session_state: st.session_state.nom_sortie_manuel = ""
if 'lieu_gite' not in st.session_state: st.session_state.lieu_gite = ""
if 'dept_saisie_brute' not in st.session_state: st.session_state.dept_saisie_brute = ""
if 'type_act' not in st.session_state: st.session_state.type_act = "Exploration"
if 'cavites_sortie' not in st.session_state: st.session_state.cavites_sortie = ""
if 'date_debut' not in st.session_state: st.session_state.date_debut = datetime.date(2026, 7, 4)
if 'date_fin' not in st.session_state: st.session_state.date_fin = datetime.date(2026, 7, 5)

# =====================================================================
# 🏛️ VOLET VERTICAL DE GAUCHE : INFORMATIONS SORTIE (VERROUILLÉ)
# =====================================================================
st.sidebar.header("🦇 ABIMES")
st.sidebar.subheader("📋 Informations Sortie")

dates_saisies = st.sidebar.date_input("Date de début :", value=st.session_state.date_debut, format="DD/MM/YYYY")
st.session_state.date_debut = dates_saisies
date_fin_saisie = st.sidebar.date_input("Date de fin :", value=st.session_state.date_fin, format="DD/MM/YYYY")
st.session_state.date_fin = date_fin_saisie

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

saisie_departement = st.sidebar.text_input(
    "N° département / Pays :",
    value=st.session_state.dept_saisie_brute,
    placeholder="21, Côte d'Or"
).strip()

dept_formate = saisie_departement
if saisie_departement:
    if "," not in saisie_departement:
        code_saisi = saisie_departement.upper()
        if code_saisi in DICTIONNAIRE_DEP:
            dept_formate = f"{code_saisi}, {DICTIONNAIRE_DEP[code_saisi]}"

st.session_state.dept_saisie_brute = dept_formate

st.session_state.lieu_gite = st.sidebar.text_input(
    "Lieu du gîte :", 
    value=st.session_state.lieu_gite,
    placeholder="Le Fabilie, Val-Suzon"
)

liste_cavites = [c.strip() for c in st.session_state.cavites_sortie.split(",") if c.strip()]
premiere_cavite = liste_cavites if liste_cavites else "Abimes des Fraisiers"

if st.session_state.nom_sortie_manuel.strip():
    nom_definitif_sortie = st.session_state.nom_sortie_manuel
else:
    nom_definitif_sortie = premiere_cavite

str_debut = st.session_state.date_debut.strftime('%d/%m/%Y')
str_fin = st.session_state.date_fin.strftime('%d/%m/%Y')

st.sidebar.write("---")
st.sidebar.markdown("### 🗂️ Fiche Récapitulative")
st.sidebar.info(
    f"🦇 **Sortie :** {nom_definitif_sortie}\n\n"
    f"📅 **Dates :** Du {str_debut} au {str_fin}\n\n"
    f"📍 **Gîte :** {st.session_state.lieu_gite if st.session_state.lieu_gite else 'Le Fabilie, Val-Suzon'} ({st.session_state.dept_saisie_brute if st.session_state.dept_saisie_brute else '21, Côte d\'Or'})\n\n"
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
    st.session_state.lieu_gite = ""
    st.success("Données effacées.")
    st.rerun()

# =====================================================================
# 🧭 ZONE CENTRALE : CRÉATION DE LA LISTE D'ONGLETS HORIZONTAUX
# =====================================================================
onglet1, onglet2, onglet3, onglet4, onglet5, onglet6, onglet7 = st.tabs([
    "👥 1. Participants", 
    "🏠 2. Logement & Gîte", 
    "🥑 3. Nourriture & Courses", 
    "🚗 4. Transports & Covoiturage", 
    "📸 5. Justificatifs & Tickets", 
    "📈 6. Visualisation",
    "📊 7. Bilan Global"
])

tous_participants = list(st.session_state.presents_data.keys())

# --- FIX : DÉPLOIEMENT UNIQUE INDIVIDUEL DE L'ONGLET 1 ---
with onglet1:
    st.subheader("Saisie des participants de la sortie")
    
    with st.form(key="form_saisie_speleo", clear_on_submit=True):
        col_n, col_g, col_a, col_s = st.columns(4)
        
        saisie_brute = col_n.text_input("Prénom et Nom (ex: Arthur Perrin) :")
        genre_p = col_g.selectbox("Genre :", ["Homme", "Femme"])
        age_p = col_a.selectbox("Tranche d'âge :", ["Actif (26-64 ans)", "Jeune (< 26 ans)", "Sénior (>= 65 ans)"])
        statut_p = col_s.selectbox("Statut Club :", ["Membre club", "Débutant", "Fédéré", "Accompagnant"])
        
        st.write("---")
        st.markdown("🎒 **Options d'initiation (Prises en compte uniquement si Statut = Débutant) :**")
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
        st.subheader("Membres inscrits")
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

# --- FIX : DÉPLOIEMENT UNIQUE INDIVIDUEL DE L'ONGLET 2 ---
with onglet2:
    st.subheader("Gestion des frais de logement")
    if not tous_participants:
        st.info("💡 Ajoutez d'abord des participants dans le premier onglet pour débloquer la gestion de l'hébergement.")
    else:
        col_g1, col_g2 = st.columns(2)
        payeur_gite = col_g1.selectbox("Qui a avancé les frais du gîte ?", tous_participants, key="p_gite")
        frais_gite_txt = col_g2.text_input("Montant total payé pour le gîte (€) :", value="0", key="txt_gite_val")
        
        cible_gite = st.radio("À qui s'applique cette facture d'hébergement ?", ["🌍 Tout le collectif présent", "👥 Un petit comité / Individuels"], key="r_c_gite")
        
        beneficiaires_gite = []
        if cible_gite == "👥 Un petit comité / Individuels":
            st.write("👉 **Cochez uniquement les spéléos concernés :**")
            for p in tous_participants:
                if st.checkbox(f"A dormi au gîte : {p}", value=True, key=f"gite_cb_{p}"):
                    beneficiaires_gite.append(p)
        else:
            beneficiaires_gite = tous_participants.copy()
        
        if st.button("🏠 Enregistrer cette dépense de logement"):
            val_g = evaluer_operation(frais_gite_txt)
            if val_g and val_g > 0:
                st.session_state.depenses_gite.append({"Payeur": payeur_gite, "Montant": val_g, "Cible": beneficiaires_gite})
                st.success("Dépense d'hébergement enregistrée !")
                st.rerun()
                
