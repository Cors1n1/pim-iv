-- ==============================================================================
-- MIGRATION: SUPORTE MULTI-TENANT CONDOMINIAL
-- ==============================================================================

-- 1. Criação da Tabela de Condomínios (Tenants)
CREATE TABLE IF NOT EXISTS condominios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    cnpj VARCHAR(20) UNIQUE,
    endereco VARCHAR(255),
    telefone VARCHAR(50),
    email_contato VARCHAR(150),
    plano VARCHAR(50) DEFAULT 'PRO' NOT NULL, -- 'BASICO', 'PRO', 'ENTERPRISE'
    limite_unidades INT DEFAULT 100 NOT NULL,
    status VARCHAR(20) DEFAULT 'ATIVO' NOT NULL, -- 'ATIVO', 'BLOQUEADO', 'CANCELADO'
    motivo_bloqueio VARCHAR(255),
    cor_primaria VARCHAR(20) DEFAULT '#2563eb' NOT NULL,
    cor_secundaria VARCHAR(20) DEFAULT '#1d4ed8' NOT NULL,
    logo_url VARCHAR(255),
    criado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE condominios ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(255);
ALTER TABLE condominios ADD COLUMN IF NOT EXISTS cor_sidebar VARCHAR(20) DEFAULT '#09090b';
ALTER TABLE condominios ADD COLUMN IF NOT EXISTS cor_fundo VARCHAR(20) DEFAULT 'AUTO';
ALTER TABLE condominios ADD COLUMN IF NOT EXISTS tipo_gestao VARCHAR(30) DEFAULT 'AUTOGESTAO';
ALTER TABLE condominios ADD COLUMN IF NOT EXISTS administradora_nome VARCHAR(150);
ALTER TABLE condominios ADD COLUMN IF NOT EXISTS administradora_email VARCHAR(150);

-- 2. Inserção do Condomínio Pioneiro (Residencial Bela Vista)
INSERT INTO condominios (
    id, nome, cnpj, endereco, telefone, email_contato, plano, limite_unidades, status, cor_primaria, cor_secundaria
) VALUES (
    1, 
    'Residencial Bela Vista', 
    '12.345.678/0001-90', 
    'Av. Central, 1200 - Bairro das Flores', 
    '(11) 98765-4321', 
    'administracao@condominio.com', 
    'ENTERPRISE', 
    100, 
    'ATIVO', 
    '#2563eb', 
    '#1d4ed8'
) ON CONFLICT (id) DO NOTHING;

SELECT setval('condominios_id_seq', COALESCE((SELECT MAX(id) FROM condominios), 1));

-- 3. Adição da Coluna condominio_id nas tabelas operacionais

-- Tabela: usuarios
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name = 'condominio_id') THEN
        ALTER TABLE usuarios ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE usuarios SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_usuarios_condominio ON usuarios(condominio_id);

-- Tabela: unidades
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'unidades' AND column_name = 'condominio_id') THEN
        ALTER TABLE unidades ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE unidades SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_unidades_condominio ON unidades(condominio_id);

-- Tabela: areas_comuns
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'areas_comuns' AND column_name = 'condominio_id') THEN
        ALTER TABLE areas_comuns ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE areas_comuns SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_areas_comuns_condominio ON areas_comuns(condominio_id);

-- Tabela: encomendas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'encomendas' AND column_name = 'condominio_id') THEN
        ALTER TABLE encomendas ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE encomendas SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_encomendas_condominio ON encomendas(condominio_id);

-- Tabela: avisos
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'avisos' AND column_name = 'condominio_id') THEN
        ALTER TABLE avisos ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE avisos SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_avisos_condominio ON avisos(condominio_id);

-- Tabela: ocorrencias
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ocorrencias' AND column_name = 'condominio_id') THEN
        ALTER TABLE ocorrencias ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE ocorrencias SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_ocorrencias_condominio ON ocorrencias(condominio_id);

-- Tabela: visitantes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'visitantes' AND column_name = 'condominio_id') THEN
        ALTER TABLE visitantes ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE RESTRICT;
    END IF;
END $$;
UPDATE visitantes SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_visitantes_condominio ON visitantes(condominio_id);

-- Tabela: logs_acesso
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'logs_acesso' AND column_name = 'condominio_id') THEN
        ALTER TABLE logs_acesso ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE SET NULL;
    END IF;
END $$;
UPDATE logs_acesso SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_logs_acesso_condominio ON logs_acesso(condominio_id);

-- Tabela: configuracoes_condominio
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'configuracoes_condominio' AND column_name = 'condominio_id') THEN
        ALTER TABLE configuracoes_condominio ADD COLUMN condominio_id INT REFERENCES condominios(id) ON DELETE CASCADE;
    END IF;
END $$;
UPDATE configuracoes_condominio SET condominio_id = 1 WHERE condominio_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_configuracoes_condominio_unique ON configuracoes_condominio(condominio_id);

-- 4. Criação do Usuário SUPERADMIN inicial (dono do SaaS)
-- Senha padrão inicial criptografada com Bcrypt: 'admin123'
-- Email: superadmin@condohub.com.br
INSERT INTO usuarios (
    nome, 
    email, 
    senha_hash, 
    tipo_usuario, 
    ativo, 
    precisa_trocar_senha, 
    condominio_id
) VALUES (
    'Super Administrador SaaS',
    'superadmin@condohub.com.br',
    '$2b$12$Z0bV7Wv4Wk25o8wO7mK7he561K4oNf0hUf4GZfM34r5v8K321c17C', -- Bcrypt para 'admin123'
    'SUPERADMIN',
    TRUE,
    FALSE,
    NULL -- SuperAdmin tem acesso global
) ON CONFLICT (email) DO NOTHING;
