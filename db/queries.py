import streamlit as st
from db.client import supabase

def get_dossiers():
    """Récupère les dossiers accessibles par l'utilisateur connecté (filtré via RLS)."""
    try:
        response = supabase.table('dossiers').select('*').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Erreur lors de la récupération des dossiers : {e}")
        return []

def creer_dossier(banque: str, compte_odoo: str, entite: str, exercice: int, solde_initial: float):
    """Crée un nouveau dossier rattaché à l'utilisateur connecté."""
    try:
        user = st.session_state.user
        if not user:
            raise Exception("Utilisateur non connecté")
            
        data = {
            "user_id": user.id,
            "banque": banque,
            "compte_banque_odoo": compte_odoo,
            "entite_compte": entite,
            "exercice": exercice,
            "solde_initial": solde_initial
        }
        response = supabase.table('dossiers').insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Erreur lors de la création du dossier : {e}")
        return None
