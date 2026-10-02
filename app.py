import streamlit as st

# Configuration globale
st.set_page_config(page_title="Test ABIMES", layout="wide")

st.title("🦇 ABIMES - Test Étape 1")

# Initialisation de la mémoire vive
if 'presents_data' not in st.session_state:
    st.session_state.presents_data = {}

# Formulaire ultra-simple
st.subheader("👥 Inscription des spéléos")
nom_saisi = st.text_input("Prénom du participant :")

if st.button("➕ Enregistrer"):
    if nom_saisi:
        st.session_state.presents_data[nom_saisi] = True
        st.success(f"{nom_saisi} est inscrit !")
        st.rerun()

# Affichage de la liste
tous_participants = list(st.session_state.presents_data.keys())

if tous_participants:
    st.write("---")
    st.write("**Membres présents :**")
    for p in tous_participants:
        st.text(f"• {p}")
