import streamlit as st
from auth.session import initialize_session_state, login, logout

# Configuration globale de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Rapprochement Bancaire | SKAB",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_session_state()

# Interface de connexion
if not st.session_state.user:
    st.title("🏢 SKAB - Système de Rapprochement Bancaire")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Authentification")
        with st.form("login_form"):
            email = st.text_input("Email professionnel")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submitted:
                if email and password:
                    login(email, password)
                else:
                    st.warning("Veuillez renseigner tous les champs.")
else:
    # L'utilisateur est connecté
    st.sidebar.success(f"Connecté : {st.session_state.user.email}")
    if st.sidebar.button("Déconnexion"):
        logout()
        
    st.title("Tableau de bord principal")
    
    if st.session_state.dossier_actif:
        dossier = st.session_state.dossier_actif
        st.info(f"📁 Dossier en cours : **{dossier['banque']}** - {dossier['compte_banque_odoo']} (Exercice {dossier['exercice']})")
        st.markdown("👈 Utilisez le menu latéral pour importer des données ou lancer le rapprochement.")
    else:
        st.warning("Aucun dossier sélectionné.")
        st.markdown("""
        ### Bienvenue dans le module de rapprochement.
        Pour commencer, veuillez vous rendre dans la page **📂 Sélection Dossier** via le menu latéral 
        pour choisir ou créer le compte bancaire sur lequel vous souhaitez travailler.
        """)
