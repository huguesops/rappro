import streamlit as st
import pandas as pd
from auth.session import check_auth
from db.queries import get_dossiers, creer_dossier

# Configuration de la page
st.set_page_config(page_title="Sélection Dossier | SKAB", page_icon="📂", layout="wide")

# Vérification stricte de l'authentification (stoppe l'exécution si non connecté)
check_auth()

st.title("📂 Sélection et Gestion des Dossiers")
st.markdown("Un dossier correspond au suivi d'un compte bancaire spécifique pour un exercice comptable donné.")

# --- LISTE DES DOSSIERS EXISTANTS ---
st.header("Vos dossiers actifs")
dossiers = get_dossiers()

if dossiers:
    # Affichage sous forme de liste interactive
    for dossier in dossiers:
        # Mise en évidence visuelle si c'est le dossier actuellement actif
        is_active = False
        if st.session_state.dossier_actif and st.session_state.dossier_actif['id'] == dossier['id']:
            is_active = True
            
        container = st.container(border=True)
        with container:
            col1, col2 = st.columns([4, 1])
            with col1:
                if is_active:
                    st.markdown(f"🟢 **{dossier['banque']}** - Compte Odoo: `{dossier['compte_banque_odoo']}` *(Actif)*")
                else:
                    st.markdown(f"**{dossier['banque']}** - Compte Odoo: `{dossier['compte_banque_odoo']}`")
                st.caption(f"Entité: {dossier['entite_compte']} | Exercice: {dossier['exercice']} | Solde Initial: {dossier['solde_initial']:,.2f}")
            
            with col2:
                # Utilisation d'un label différent si le dossier est déjà ouvert
                btn_label = "Dossier en cours" if is_active else "Ouvrir ce dossier"
                if st.button(btn_label, key=f"btn_open_{dossier['id']}", disabled=is_active, use_container_width=True):
                    st.session_state.dossier_actif = dossier
                    st.success(f"Dossier {dossier['banque']} activé avec succès !")
                    st.rerun()
else:
    st.info("Aucun dossier trouvé. Veuillez en créer un via le formulaire ci-dessous.")

st.markdown("---")

# --- CRÉATION D'UN NOUVEAU DOSSIER ---
st.header("Créer un nouveau dossier")
with st.form("nouveau_dossier_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        banque = st.text_input("Nom de la banque (ex: BGFI, UBA, CCA...)")
        compte_odoo = st.text_input("Compte Odoo (ex: 52110503)")
        exercice = st.number_input("Exercice (Année)", min_value=2020, max_value=2050, value=2026)
    with col2:
        entite = st.text_input("Entité du groupe (ex: DISTRIBUTION)")
        solde_initial = st.number_input("Solde initial au 1er Janvier", value=0.0, format="%.2f", step=1000.0)
        
    submitted = st.form_submit_button("Enregistrer le dossier", type="primary")
    
    if submitted:
        if banque and compte_odoo and entite:
            nouveau = creer_dossier(banque, compte_odoo, entite, exercice, solde_initial)
            if nouveau:
                st.success("Dossier créé avec succès !")
                # On active automatiquement le nouveau dossier
                st.session_state.dossier_actif = nouveau
                st.rerun()
        else:
            st.warning("⚠️ Veuillez remplir les champs obligatoires (Banque, Compte Odoo, Entité).")
