import streamlit as st
import pandas as pd
import re

# Configuration globale obligatoire
st.set_page_config(page_title="Comptes Sorties ABIMES", layout="wide")

# Barème officiel
IK_STANDARD = 0.15

# Fonction calculatrice simple
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

# Initialisation de la mémoire du serveur
if 'presents_data' not in st.session_state:
    st.session_state.presents_data = {}
if 'vehicules' not in st.session_state:
    st.session_state.vehicules = []

# Menu simple à deux choix à gauche
st.sidebar.header("📋 ABIMES - Pas à Pas")
section_choisie = st.sidebar.radio(
    "Aller à la section :",
    ["👥 1. Saisie des Participants", "🚗 2. Transports & Covoiturage"]
)

tous_participants = list(st.session_state.presents_data.keys())

# --- SECTION 1 : AJOUT DES PARTICIPANTS ---
if section_choisie == "👥 1. Saisie des Participants":
    st.subheader("Étape 1 : Ajoutez les membres de la sortie")
    
    def ajouter_le_participant():
        nom_saisi = st.session_state.temp_nom
        if nom_saisi:
            st.session_state.presents_data[nom_saisi] = {"Enregistré": True}
            st.session_state.temp_nom = "" 

    nom_p = st.text_input("Entrez un prénom, puis appuyez sur Entrée :", key="temp_nom", on_change=ajouter_le_participant)
    st.button("➕ Enregistrer", on_click=ajouter_le_participant)

    if tous_participants:
        st.write("---")
        st.write("**Membres présents sur la sortie :**")
        for p in tous_participants:
            col_l1, col_l2 = st.columns(2)
            col_l1.text(f"• {p}")
            if col_l2.button("Supprimer", key=f"del_p_{p}"):
                del st.session_state.presents_data[p]
                st.rerun()

# --- SECTION 2 : LE FAMEUX FORMULAIRE TRANSPORT COMPLET ---
else:
    st.subheader("Étape 2 : Déclarer les véhicules et trajets de la sortie")
    
    if not tous_participants:
        st.info("💡 Veuillez ajouter au moins un participant dans l'étape 1 pour débloquer les transports.")
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
            c_abandon = st.checkbox("💡 Abandon de frais (Don des IK au club)", key="abandon_transp_v")
            
            st.write("**👥 Cochez les membres à bord et ajustez leurs kilomètres :**")
            c_passagers_details = {}
            for p in tous_participants:
                if st.checkbox(f"Présent dans la voiture : {p}", value=(p == c_proprio), key=f"transp_p_actif_{p}"):
                    p_km_indiv = st.number_input(f"  ↳ Kilomètres parcourus à bord par {p} :", min_value=0, max_value=max(1, c_km), value=c_km, key=f"transp_p_km_{p}")
                    c_passagers_details[p] = p_km_indiv
                    
            if st.button("🚗 Enregistrer cette voiture collective", key="btn_save_voiture_coll"):
                if not c_passagers_details: 
                    st.error("Le véhicule doit contenir au moins un passager.")
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
            i_km_solo = st.number_input("Kilomètres réels effectués :", min_value=0, value=0, key="km_voy_indiv")
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
