-- ==========================================
-- 1. EXTENSIONS & TABLES AUTHENTIFICATION
-- ==========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des rôles personnalisés (étend auth.users)
CREATE TABLE user_roles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('comptable', 'admin')) DEFAULT 'comptable'
);

-- Table des dossiers (comptes bancaires)
CREATE TABLE dossiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    banque VARCHAR(255) NOT NULL,
    compte_banque_odoo VARCHAR(50) NOT NULL,
    entite_compte VARCHAR(100) NOT NULL,
    exercice INT NOT NULL,
    solde_initial NUMERIC(15, 2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 2. RÉFÉRENTIELS GLOBAUX (Partagés)
-- ==========================================
CREATE TABLE ref_plan_comptable (
    compte VARCHAR(20) PRIMARY KEY,
    intitule VARCHAR(255) NOT NULL,
    classe VARCHAR(2) NOT NULL
);

CREATE TABLE statuts_actifs (
    statut VARCHAR(100) PRIMARY KEY,
    type_operation VARCHAR(100),
    sens VARCHAR(1) CHECK (sens IN ('C', 'D', 'T')),
    journal VARCHAR(50),
    compte_general VARCHAR(20) REFERENCES ref_plan_comptable(compte),
    observation TEXT,
    compte_tiers VARCHAR(50)
);

CREATE TABLE mapping_mots_cles (
    id SERIAL PRIMARY KEY,
    mot_cle VARCHAR(255) NOT NULL,
    sens VARCHAR(1) CHECK (sens IN ('C', 'D', 'T')),
    statut VARCHAR(100) REFERENCES statuts_actifs(statut),
    priorite INT DEFAULT 1,
    journal VARCHAR(50),
    compte_general VARCHAR(20) REFERENCES ref_plan_comptable(compte),
    compte_tiers VARCHAR(50),
    libelle_comptable VARCHAR(255)
);

CREATE TABLE ref_mapping_entites (
    mot_cle_entite VARCHAR(100) PRIMARY KEY,
    entite VARCHAR(100) NOT NULL
);

-- ==========================================
-- 3. TABLES OPÉRATIONNELLES (Par Dossier)
-- ==========================================
CREATE TABLE releve_brut (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dossier_id UUID REFERENCES dossiers(id) ON DELETE CASCADE,
    annee_mois VARCHAR(7) NOT NULL, -- Format 'YYYY-MM' pour anti-doublon
    date_op DATE NOT NULL,
    libelle VARCHAR(500) NOT NULL,
    montant NUMERIC(15, 2) NOT NULL,
    solde_courant NUMERIC(15, 2),
    -- Champs workflow (Proposé vs Validé)
    statut_propose VARCHAR(100),
    statut_override VARCHAR(100), -- Prime si renseigné
    entite_proposee VARCHAR(100),
    entite_override VARCHAR(100),
    -- Champs calculés
    etat_calcule VARCHAR(50) DEFAULT 'À traiter',
    anomalie_detectee VARCHAR(255),
    -- Rapprochement
    score_rapprochement INT DEFAULT 0,
    statut_rapprochement VARCHAR(50) DEFAULT 'Suspens',
    lettrage_manuel VARCHAR(20) CHECK (lettrage_manuel IN ('X', 'Lettré', 'À revoir', NULL)),
    UNIQUE(dossier_id, annee_mois, date_op, libelle, montant, solde_courant) -- Anti-doublon strict à l'import
);

CREATE TABLE grand_livre_odoo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dossier_id UUID REFERENCES dossiers(id) ON DELETE CASCADE,
    compte VARCHAR(50) NOT NULL,
    intitule VARCHAR(255),
    date_mvt DATE NOT NULL,
    piece_journal VARCHAR(100),
    communication VARCHAR(500),
    partenaire VARCHAR(255),
    debit NUMERIC(15, 2) DEFAULT 0,
    credit NUMERIC(15, 2) DEFAULT 0,
    solde NUMERIC(15, 2) DEFAULT 0,
    compte_tiers VARCHAR(50)
);

CREATE TABLE journal_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dossier_id UUID REFERENCES dossiers(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id),
    annee_mois VARCHAR(7) NOT NULL,
    action VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB
);

-- ==========================================
-- 4. POLITIQUES RLS (Row Level Security)
-- ==========================================
ALTER TABLE user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE dossiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE ref_plan_comptable ENABLE ROW LEVEL SECURITY;
ALTER TABLE statuts_actifs ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapping_mots_cles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ref_mapping_entites ENABLE ROW LEVEL SECURITY;
ALTER TABLE releve_brut ENABLE ROW LEVEL SECURITY;
ALTER TABLE grand_livre_odoo ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_audit ENABLE ROW LEVEL SECURITY;

-- Les utilisateurs gèrent leurs propres dossiers
CREATE POLICY "Users can manage their dossiers" ON dossiers
    FOR ALL USING (auth.uid() = user_id);

-- Lecture des référentiels pour tous les utilisateurs authentifiés
CREATE POLICY "Read access for all auth users on referentials" ON statuts_actifs
    FOR SELECT USING (auth.role() = 'authenticated');
-- (À dupliquer pour ref_plan_comptable, mapping_mots_cles, ref_mapping_entites)

-- Accès strict aux données opérationnelles via le dossier_id
CREATE POLICY "Users can access their releve" ON releve_brut
    FOR ALL USING (dossier_id IN (SELECT id FROM dossiers WHERE user_id = auth.uid()));

CREATE POLICY "Users can access their GL" ON grand_livre_odoo
    FOR ALL USING (dossier_id IN (SELECT id FROM dossiers WHERE user_id = auth.uid()));

CREATE POLICY "Users can access their audit" ON journal_audit
    FOR ALL USING (dossier_id IN (SELECT id FROM dossiers WHERE user_id = auth.uid()));
