-- ==============================================================================
-- CONDOHUB / SGC - SCRIPT DE MIGRAÇÃO COMPLETA PARA PRODUÇÃO (ONLINE)
-- ==============================================================================
-- Este script é 100% IDEMPOTENTE (pode ser executado quantas vezes quiser sem erros).
-- Ele NÃO apaga dados existentes em condomínios ativos.
-- Apenas adiciona colunas, índices e tabelas novas que faltarem no banco da nuvem.
--
-- NOTA: O backend FastAPI (main.py) JÁ EXECUTA essas migrações automaticamente
--       ao reiniciar o serviço na nuvem (lifespan).
--       Este arquivo serve caso queira executar manualmente via pgAdmin / DBeaver / psql.
-- ==============================================================================

BEGIN;

-- 1. Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Tabela de Condomínios (Tenants)
CREATE TABLE IF NOT EXISTS condominios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    slug VARCHAR(100) UNIQUE,
    cnpj VARCHAR(20) UNIQUE,
    endereco VARCHAR(255),
    telefone VARCHAR(50),
    email_contato VARCHAR(150),
    plano VARCHAR(50) DEFAULT 'PRO' NOT NULL,
    limite_unidades INT DEFAULT 100 NOT NULL,
    status VARCHAR(20) DEFAULT 'ATIVO' NOT NULL,
    motivo_bloqueio VARCHAR(255),
    cor_primaria VARCHAR(20) DEFAULT '#2563eb' NOT NULL,
    cor_secundaria VARCHAR(20) DEFAULT '#1d4ed8' NOT NULL,
    cor_sidebar VARCHAR(20) DEFAULT '#09090b' NOT NULL,
    cor_fundo VARCHAR(20) DEFAULT 'AUTO',
    tipo_gestao VARCHAR(30) DEFAULT 'AUTOGESTAO' NOT NULL,
    administradora_nome VARCHAR(150),
    administradora_email VARCHAR(150),
    logo_url VARCHAR(255),
    criado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Colunas extras para condominios existentes
ALTER TABLE condominios 
    ADD COLUMN IF NOT EXISTS slug VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS cor_sidebar VARCHAR(20) DEFAULT '#09090b',
    ADD COLUMN IF NOT EXISTS cor_fundo VARCHAR(20) DEFAULT 'AUTO',
    ADD COLUMN IF NOT EXISTS tipo_gestao VARCHAR(30) DEFAULT 'AUTOGESTAO',
    ADD COLUMN IF NOT EXISTS administradora_nome VARCHAR(150) NULL,
    ADD COLUMN IF NOT EXISTS administradora_email VARCHAR(150) NULL;

-- Garante que condomínios antigos sem slug recebam um slug automático
UPDATE condominios 
SET slug = LOWER(REGEXP_REPLACE(nome, '[^a-zA-Z0-9]+', '-', 'g')) 
WHERE slug IS NULL OR slug = '';

CREATE UNIQUE INDEX IF NOT EXISTS idx_condominios_slug ON condominios(slug);

-- 3. Tabela de Usuários (Controle de Acesso)
ALTER TABLE usuarios 
    ADD COLUMN IF NOT EXISTS condominio_id INT NULL,
    ADD COLUMN IF NOT EXISTS status_cadastro VARCHAR(30) DEFAULT 'ATIVO',
    ADD COLUMN IF NOT EXISTS token_convite VARCHAR(255) NULL,
    ADD COLUMN IF NOT EXISTS token_convite_expira_em TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS token_version INT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS cpf VARCHAR(20) NULL,
    ADD COLUMN IF NOT EXISTS precisa_trocar_senha BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_usuarios_condominio ON usuarios(condominio_id);
CREATE INDEX IF NOT EXISTS idx_usuarios_token_convite ON usuarios(token_convite);

-- 4. Tabela de Áreas Comuns
ALTER TABLE areas_comuns 
    ADD COLUMN IF NOT EXISTS condominio_id INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS intervalo_dias_prioridade INT DEFAULT 30,
    ADD COLUMN IF NOT EXISTS max_reservas_ativas INT DEFAULT 2,
    ADD COLUMN IF NOT EXISTS prazo_standby_horas INT DEFAULT 48;

CREATE INDEX IF NOT EXISTS idx_areas_comuns_condominio ON areas_comuns(condominio_id);

-- 5. Tabela de Reservas
ALTER TABLE reservas 
    ADD COLUMN IF NOT EXISTS prioridade VARCHAR(20) DEFAULT 'ALTA',
    ADD COLUMN IF NOT EXISTS prioridade_queimada BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS oferta_retomada_ate TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS chave_entregue BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS chave_entregue_por INT NULL,
    ADD COLUMN IF NOT EXISTS chave_entregue_para VARCHAR(150) NULL,
    ADD COLUMN IF NOT EXISTS chave_entregue_em TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS chave_devolvida BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS chave_devolvida_em TIMESTAMP WITH TIME ZONE NULL;

-- 6. Tabela de Convidados de Reserva
CREATE TABLE IF NOT EXISTS convidados_reserva (
    id SERIAL PRIMARY KEY,
    reserva_id INT NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
    nome_completo VARCHAR(150) NOT NULL,
    documento VARCHAR(50) NULL,
    email VARCHAR(150) NULL,
    convite_enviado BOOLEAN DEFAULT FALSE NOT NULL,
    entrada_registrada BOOLEAN DEFAULT FALSE NOT NULL,
    entrada_em TIMESTAMP WITH TIME ZONE NULL,
    saida_registrada BOOLEAN DEFAULT FALSE NOT NULL,
    saida_em TIMESTAMP WITH TIME ZONE NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

ALTER TABLE convidados_reserva ALTER COLUMN documento DROP NOT NULL;
ALTER TABLE convidados_reserva 
    ADD COLUMN IF NOT EXISTS convite_enviado BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS entrada_registrada BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS entrada_em TIMESTAMP WITH TIME ZONE NULL,
    ADD COLUMN IF NOT EXISTS saida_registrada BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS saida_em TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS idx_convidados_reserva_id ON convidados_reserva(reserva_id);

-- 7. Configurações de Condomínio
ALTER TABLE configuracoes_condominio 
    ADD COLUMN IF NOT EXISTS condominio_id INT DEFAULT 1,
    ADD COLUMN IF NOT EXISTS dias_penalidade_queima INT DEFAULT 30;

-- 8. Configurações Globais da Plataforma (SaaS)
CREATE TABLE IF NOT EXISTS configuracoes_plataforma (
    id SERIAL PRIMARY KEY,
    suporte_email VARCHAR(150) NOT NULL DEFAULT 'suporte@corsini.inf.br',
    suporte_telefone VARCHAR(50) NOT NULL DEFAULT '(11) 98765-4321',
    suporte_horario VARCHAR(100) DEFAULT 'Segunda a Sexta, das 08h às 18h',
    titulo_regularizacao VARCHAR(150) DEFAULT 'O que fazer para regularizar?',
    mensagem_regularizacao TEXT DEFAULT 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.',
    titulo_suspensao VARCHAR(150) DEFAULT 'Acesso ao Condomínio Suspenso',
    subtitulo_suspensao VARCHAR(255) DEFAULT 'O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.',
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO configuracoes_plataforma (id, suporte_email, suporte_telefone, suporte_horario, titulo_regularizacao, mensagem_regularizacao)
VALUES (1, 'suporte@corsini.inf.br', '(11) 98765-4321', 'Segunda a Sexta, das 08h às 18h', 'O que fazer para regularizar?', 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.')
ON CONFLICT (id) DO NOTHING;

-- 9. Ajuste de chaves condominio_id nulas em dados legados (sem conflito de unicidade)
UPDATE usuarios 
SET condominio_id = 1 
WHERE condominio_id IS NULL AND tipo_usuario NOT IN ('SUPERADMIN', 'DIRETORIA');

DELETE FROM unidades u
WHERE u.condominio_id IS NULL
  AND EXISTS (
    SELECT 1 FROM unidades b
    WHERE b.condominio_id = 1 AND b.bloco = u.bloco AND b.numero = u.numero
  );
UPDATE unidades SET condominio_id = 1 WHERE condominio_id IS NULL;

DELETE FROM areas_comuns a
WHERE a.condominio_id IS NULL 
  AND EXISTS (
    SELECT 1 FROM areas_comuns b 
    WHERE b.condominio_id = 1 AND b.nome = a.nome
  );
UPDATE areas_comuns SET condominio_id = 1 WHERE condominio_id IS NULL;

UPDATE encomendas SET condominio_id = 1 WHERE condominio_id IS NULL;
UPDATE avisos SET condominio_id = 1 WHERE condominio_id IS NULL;
UPDATE ocorrencias SET condominio_id = 1 WHERE condominio_id IS NULL;
UPDATE visitantes SET condominio_id = 1 WHERE condominio_id IS NULL;

COMMIT;
