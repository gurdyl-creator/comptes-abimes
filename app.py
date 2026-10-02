import streamlit as st

# Configuration globale
st.set_page_config(page_title="Test ABIMES", layout="wide")

st.title("🦇 ABIMES - Test Étape 1 (Format Prénom N)")

# Initialisation de la mémoire vive
if 'presents_data' not in st.session_state:
    st.session_state.presents_data = {}

st.subheader("👥 Inscription des spéléos")

# Formulaire fluide avec vidage automatique
with st.form(key="formulaire_participant", clear_on_submit=True):
    saisie_brute = st.text_input("Entrez le Prénom et le Nom (ex: Jean Dupont) :")
    bouton_valider = st.form_submit_button("➕ Enregistrer")
    
    if bouton_valider and saisie_brute:
        # Nettoyage intelligent : on sépare les mots tapés par l'utilisateur
        mots = saisie_brute.strip().split()
        
        if len(mots) >= 2:
            # Si l'utilisateur a tapé au moins deux mots (un prénom et un nom)
            prenom = mots[0].capitalize()
            initiale_nom = mots[1][0].upper()
            nom_propre = f"{prenom} {initiale_nom}"
        else:
            # Si l'utilisateur n'a tapé qu'un seul mot, on le garde tel quel avec une majuscule
            nom_propre = mots[0].capitalize()
            
        # On enregistre le nom propre calibré dans la mémoire vive
        st.session_state.presents_data[nom_propre] = True
        st.success(f"Format validé : {nom_propre} est inscrit !")
        st.rerun()

# Récupération et affichage de la liste en temps réel
tous_participants = list(st.session_state.presents_data.keys())

if tous_participants:
    st.write("---")
    st.write("**Membres présents (Format Officiel) :**")
    for p in tous_participants:
        st.text(f"• {p}")
