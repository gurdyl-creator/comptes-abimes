import streamlit as st

# Configuration globale
st.set_page_config(page_title="Test ABIMES", layout="wide")

st.title("🦇 ABIMES - Test Étape 1 (Formulaire Fluide)")

# Initialisation de la mémoire vive
if 'presents_data' not in st.session_state:
    st.session_state.presents_data = {}

st.subheader("👥 Inscription des spéléos")

# Utilisation d'un vrai formulaire Streamlit pour gérer la touche Entrée et le vidage de la case
with st.form(key="formulaire_participant", clear_on_submit=True):
    nom_saisi = st.text_input("Prénom du participant :")
    bouton_valider = st.form_submit_button("➕ Enregistrer")
    
    if bouton_valider and nom_saisi:
        # On enregistre le prénom dans la mémoire vive
        st.session_state.presents_data[nom_saisi] = True
        st.success(f"{nom_saisi} est inscrit !")
        st.rerun()

# Récupération et affichage de la liste en temps réel
tous_participants = list(st.session_state.presents_data.keys())

if tous_participants:
    st.write("---")
    st.write("**Membres présents :**")
    for p in tous_participants:
        st.text(f"• {p}")
