import pandas as pd
import numpy as np

def calculer_montant_signe_gl(df_gl: pd.DataFrame) -> pd.DataFrame:
    """Calcule le montant signé du GL (Débit - Crédit) pour correspondre au relevé."""
    df = df_gl.copy()
    # Gestion des valeurs nulles
    df['debit'] = df['debit'].fillna(0)
    df['credit'] = df['credit'].fillna(0)
    df['montant_signe'] = df['debit'] - df['credit']
    return df

def executer_rapprochement(df_releve: pd.DataFrame, df_gl: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le score de rapprochement pour chaque ligne du relevé.
    Sans boucle for, via des jointures pandas pour la performance.
    """
    if df_releve.empty:
        return df_releve
        
    df_r = df_releve.copy()
    
    if df_gl.empty:
        df_r['nb_match_montant'] = 0
        df_r['nb_match_montant_date'] = 0
    else:
        df_g = calculer_montant_signe_gl(df_gl)
        
        # S'assurer que les dates sont bien des datetime pour le calcul d'écart
        df_r['date_op'] = pd.to_datetime(df_r['date_op'])
        df_g['date_mvt'] = pd.to_datetime(df_g['date_mvt'])
        
        # Jointure sur le montant pour trouver les correspondances
        merged = pd.merge(
            df_r[['id', 'montant', 'date_op']], 
            df_g[['id', 'montant_signe', 'date_mvt']], 
            left_on='montant', 
            right_on='montant_signe', 
            how='inner',
            suffixes=('_rel', '_gl')
        )
        
        # Calcul de l'écart de jours absolu
        merged['ecart_jours'] = (merged['date_op'] - merged['date_mvt']).dt.days.abs()
        
        # Compter les correspondances par montant
        match_montant = merged.groupby('id_rel').size().reset_index(name='nb_match_montant')
        
        # Compter les correspondances par montant ET date (<= 15 jours)
        match_date = merged[merged['ecart_jours'] <= 15].groupby('id_rel').size().reset_index(name='nb_match_montant_date')
        
        # Intégration des comptages dans le dataframe original du relevé
        df_r = df_r.merge(match_montant, left_on='id', right_on='id_rel', how='left').drop(columns=['id_rel'])
        df_r = df_r.merge(match_date, left_on='id', right_on='id_rel', how='left').drop(columns=['id_rel'])
        
        df_r['nb_match_montant'] = df_r['nb_match_montant'].fillna(0).astype(int)
        df_r['nb_match_montant_date'] = df_r['nb_match_montant_date'].fillna(0).astype(int)

    # Calcul du score : 80 si date et montant OK, 60 si montant OK seulement, 0 sinon
    df_r['score_rapprochement'] = np.where(
        df_r['nb_match_montant_date'] > 0, 80,
        np.where(df_r['nb_match_montant'] > 0, 60, 0)
    )
    
    # Détermination du statut de rapprochement
    # Priorité absolue au lettrage manuel
    conditions = [
        df_r['lettrage_manuel'].isin(['X', 'Lettré']),
        df_r['score_rapprochement'] >= 80,
        df_r['nb_match_montant'] > 0
    ]
    
    choices = [
        'Rapproché manuel',
        'Rapproché auto',
        'Montant OK / date à vérifier'
    ]
    
    df_r['statut_rapprochement'] = np.select(conditions, choices, default='Suspens')
    
    # Nettoyage des colonnes temporaires
    cols_to_drop = ['nb_match_montant', 'nb_match_montant_date']
    df_r = df_r.drop(columns=[c for c in cols_to_drop if c in df_r.columns])
    
    return df_r
