import pandas as pd
import numpy as np

def prep_releve_sens(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute la colonne sens (Crédit si montant > 0, Débit sinon)"""
    df = df.copy()
    df['sens'] = np.where(df['montant'] > 0, 'C', 'D')
    return df

def impute_automatiquement(df_releve: pd.DataFrame, df_mapping: pd.DataFrame, df_entites: pd.DataFrame, entite_defaut: str) -> pd.DataFrame:
    """
    Applique le moteur de règles pour déterminer le statut proposé et l'entité.
    Principe d'arbitrage : Priorité la plus haute, puis ordre d'apparition.
    """
    df = prep_releve_sens(df_releve)
    
    # Valeurs par défaut
    df['statut_propose'] = 'À classer'
    df['entite_proposee'] = entite_defaut
    df['libelle_comptable'] = df['libelle']
    
    # 1. Tri du mapping : on applique les priorités faibles d'abord, pour que les fortes écrasent à la fin
    # L'ordre d'apparition initial est conservé via l'index original si priorités égales
    mapping_sorted = df_mapping.sort_values(by=['priorite', 'id'], ascending=[True, False])
    
    # 2. Application vectorisée des règles de mots-clés pour les statuts
    for _, regle in mapping_sorted.iterrows():
        mot_cle = str(regle['mot_cle']).lower()
        sens_regle = regle['sens']
        
        # Le mot-clé est présent dans le libellé ?
        mask_contains = df['libelle'].str.lower().str.contains(mot_cle, regex=False, na=False)
        
        # Le sens correspond-il ? ('T' = Tous, sinon 'C' ou 'D')
        mask_sens = (sens_regle == 'T') | (df['sens'] == sens_regle)
        
        mask_final = mask_contains & mask_sens
        
        # Application des propositions
        df.loc[mask_final, 'statut_propose'] = regle['statut']
        if pd.notna(regle['libelle_comptable']):
             df.loc[mask_final, 'libelle_comptable'] = regle['libelle_comptable']

    # 3. Application vectorisée des règles d'entités
    for _, regle_ent in df_entites.iterrows():
        mot_cle_ent = str(regle_ent['mot_cle_entite']).lower()
        mask_ent = df['libelle'].str.lower().str.contains(mot_cle_ent, regex=False, na=False)
        df.loc[mask_ent, 'entite_proposee'] = regle_ent['entite']

    return df

def calculer_etat_et_anomalies(df_releve: pd.DataFrame, df_statuts_actifs: pd.DataFrame, df_plan_comptable: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'état (À traiter vs Validé) et cascade les anomalies selon les règles strictes.
    Prend en compte statut_override s'il existe.
    """
    df = df_releve.copy()
    
    # Résolution du statut final (Manuel prime sur Automatique)
    df['statut_final'] = np.where(df['statut_override'].notna() & (df['statut_override'] != ''), 
                                  df['statut_override'], 
                                  df['statut_propose'])
    
    # Jointure avec les référentiels pour récupérer les attributs du statut final
    df = df.merge(df_statuts_actifs, left_on='statut_final', right_on='statut', how='left')
    
    # Variables de base pour les contrôles
    is_montant_nul = (df['montant'] == 0)
    is_statut_vide = df['statut_final'].isna() | (df['statut_final'] == '') | (df['statut_final'] == 'À classer')
    is_compte_vide = df['compte_general'].isna() | (df['compte_general'] == '')
    is_journal_vide = df['journal'].isna() | (df['journal'] == '')
    
    # Vérification si compte_general existe dans le plan comptable
    comptes_valides = set(df_plan_comptable['compte'].astype(str))
    is_compte_hors_plan = ~df['compte_general'].astype(str).isin(comptes_valides) & ~is_compte_vide
    
    # Incohérence de sens (sens réel vs sens imposé par le statut actif)
    df['sens_reel'] = np.where(df['montant'] > 0, 'C', 'D')
    is_incoherence_sens = (df['sens'].notna()) & (df['sens'] != 'T') & (df['sens'] != df['sens_reel'])
    
    # Calcul de l'État (Workflow)
    df['etat_calcule'] = np.where(is_montant_nul | is_statut_vide | is_compte_vide, 'À traiter', 'Validé')
    
    # Cascade d'anomalies (numpy select s'arrête à la première condition vraie)
    conditions = [
        is_montant_nul,
        is_statut_vide,
        is_compte_vide,
        is_journal_vide,
        is_compte_hors_plan,
        is_incoherence_sens
    ]
    
    choices = [
        "Montant nul",
        "Imputation à classer",
        "Compte manquant",
        "Journal manquant",
        "Compte hors plan",
        "Incohérence sens (type/mouvement)"
    ]
    
    df['anomalie_detectee'] = np.select(conditions, choices, default=None)
    
    return df
