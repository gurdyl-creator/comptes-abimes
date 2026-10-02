import streamlit as st
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
        return float(eval(formule_propre, {"__builtins__": None}, {}))
    except:
        return None

# --- INITIALISATION SÉCURISÉE DE LA SESSION ---
if 'presents_data' not in st.session_state: 
    st.session_state.presents_data = {}
if 'vehicules' not in st.session_state: 
    st.session_state.vehicules = []

# --- BARRE LATÉRALE : NAVIGATION PAS-À-PAS ---
st.sidebar.header("📋 ABIMES - Menu")
section_choisie = st.sidebar.radio(
    "Aller à la section :",
    [
        "👥 1. Saisie des Participants", 
        "🚗 2. Transports & Covoiturage"
    ]
)

st.title(f"🦇 ABIMES - {section_choisie[5:]}")
tous_participants = list(st.session_state.presents_data.keys())

# =====================================================================
# --- SECTION 1 : PARTICIPANTS (VOTRE VERSION VALIDÉE) ---
# =====================================================================
if section_choisie == "👥 1. Saisie des Participants":
    st.subheader("Inscrivez les membres de la sortie (Format : Jean Dupont)")
    
    with st.form(key="formulaire_participant", clear_on_submit=True):
        saisie_brute = st.text_input("Prénom et Nom :")
        bouton_valider = st.form_submit_button("➕ Enregistrer")
        
        if bouton_valider and saisie_brute:
            mots = saisie_brute.strip().split()
            if len(mots) >= 2:
                prenom = mots[0].capitalize()
                initiale_nom = mots[1][0].upper()
                nom_propre = f"{prenom} {initiale_nom}"
            else:
                nom_propre = mots[0].capitalize()
                
            st.session_state.presents_data[nom_propre] = True
            st.success(f"Format validé : {nom_propre} est inscrit !")
            st.rerun()

    if tous_participants:
        st.write("---")
        st.subheader("Membres actuellement inscrits")
        for p in tous_participants:
            col_l1, col_l2 = st.columns(2)
            col_l1.text(f"• {p}")
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.rerun()

# =====================================================================
# --- SECTION 2 : LE GRAND FORMULAIRE TRANSPORT COMPTABLE ---
# =====================================================================
else:
    st.subheader("Déclarer les véhicules et trajets de la sortie")
    
    if not tous_participants:
        st.info("💡 Veuillez ajouter au moins un participant dans le menu 1 pour débloquer les transports.")
    else:
        mode = st.radio("Quel type de trajet voulez-vous ajouter ?", ["🚗 Un véhicule collectif (Covoiturage club)", "🚆 Un trajet individuel (Train, Voiture Solo...)"])
        st.write("---")
        
        if mode == "🚗 Un véhicule collectif (Covoiturage club)":
            c_proprio = st.selectbox("Conducteur / Propriétaire :", tous_participants, key="key_prop_transp")
            c_km = st.number_input("Kilomètres totaux effectués par le véhicule :", min_value=0, value=0, key="km_transp_v")
            c_carb = st.text_input("Dépense de Carburant (€) :", value="0", key="carb_transp_v")
            c_peage = st.text_input("Dépense de Péages (€) :", value="0", key="peage_transp_v")
            
            c_val_carb = evaluer_operation(c_carb) or 0.0
            c_val_peage = evaluer_operation(c_peage) or 0.0
            c_abandon = st.checkbox("💡 Abandon de frais (Don des IK au club pour reçu fiscal)", key="abandon_transp_v")
            
            st.write("**👥 Cochez les membres présents à bord et ajustez leurs kilomètres réels :**")
            c_passagers_details = {}
            for p in tous_participants:
                if st.checkbox(f"Présent dans la voiture : {p}", value=(p == c_proprio), key=f"transp_p_actif_{p}"):
                    p_km_indiv = st.number_input(f"  ↳ Distance parcourue à bord par {p} (km) :", min_value=0, max_value=max(1, c_km), value=c_km, key=f"transp_p_km_{p}")
                    if p_km_indiv > 0:
                        c_passagers_details[p] = p_km_indiv
                    
            if st.button("🚗 Enregistrer cette voiture collective", key="btn_save_voiture_coll"):
                if not c_passagers_details: 
                    st.error("Le véhicule doit contenir au moins un passager avec une distance supérieure à 0.")
                else:
                    st.session_state.vehicules.append({
                        "Type": "Collectif", "Conducteur": c_proprio, "KM": c_km, 
                        "Carburant": c_val_carb, "Peage": c_val_peage, "Abandon": c_abandon, "PassagersDetails": c_passagers_details
                    })
                    st.success("Voiture collective ajoutée avec succès !")
                    st.rerun()
        else:
            st.subheader("Déclarer un trajet individuel")
            i_voy = st.selectbox("Participant concerné :", tous_participants, key="key_voy_indiv")
            i_frais_txt = st.text_input("Montant financier payé (€) :", value="0", key="frais_voy_indiv")
            i_km_solo = st.number_input("Kilomètres réels effectués en solo :", min_value=0, value=0, key="km_voy_indiv")
            i_val_frais = evaluer_operation(i_frais_txt) or 0.0
            
            if st.button("🚆 Enregistrer ce trajet individuel", key="btn_save_voy_indiv"):
                st.session_state.vehicules.append({
                    "Type": "Individuel", "Conducteur": i_voy, "Frais": i_val_frais, "KM_Indiv": i_km_solo
                })
                st.success("Trajet individuel ajouté avec succès !")
                st.rerun()
                
        if st.session_state.vehicules:
            st.write("---")
            st.subheader("📋 Liste des transports enregistrés :")
            for idx, v in enumerate(st.session_state.vehicules):
                if v["Type"] == "Collectif":
                    st.text(f"• 🚗 Voiture de {v['Conducteur']} | {v['KM']} km | {len(v['PassagersDetails'])} pers. à bord")
                else:
                    st.text(f"• 🚆 Trajet solo de {v['Conducteur']} | Coût : {v['Frais']:.2f} €")
                if st.button("Supprimer ce trajet", key=f"del_v_{idx}"):
                    st.session_state.vehicules.pop(idx)
                    st.rerun()
