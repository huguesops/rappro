import streamlit as st
from supabase import create_client, Client
import os

@st.cache_resource
def init_supabase() -> Client:
    """
    Initialise et retourne le client Supabase.
    Utilise st.secrets pour la sécurité (déploiement et local).
    """
    # Récupération sécurisée des secrets
    url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("⚠️ Identifiants Supabase introuvables. Vérifiez st.secrets (secrets.toml).")
        st.stop()
        
    return create_client(url, key)

# Instance globale à importer dans les autres modules
supabase = init_supabase()
