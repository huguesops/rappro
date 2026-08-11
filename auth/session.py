import streamlit as st
from db.client import supabase

def initialize_session_state():
    """Initialise les variables de session si elles n'existent pas."""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'dossier_actif' not in st.session_state:
        st.session_state.dossier_actif = None

def login(email: str, password: str):
    """Tente une connexion via Supabase Auth."""
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if response.user:
            st.session_state.user = response.user
            st.success("Connexion réussie !")
            st.rerun()
    except Exception as e:
        st.error(f"Échec de la connexion : Identifiants incorrects ou compte inexistant.")

def logout():
    """Déconnecte l'utilisateur."""
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.dossier_actif = None
    st.rerun()

def check_auth():
    """
    À appeler au début de chaque page. 
    Stoppe l'exécution si l'utilisateur n'est pas connecté.
    """
    initialize_session_state()
    if not st.session_state.user:
        st.warning("🔒 Veuillez vous connecter pour accéder à cette page.")
        st.stop()
