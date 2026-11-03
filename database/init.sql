-- ====================================================================
-- PROJETO INTEGRADO MULTIDISCIPLINAR - PIM IV
-- CURSO SUPERIOR DE TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS
-- SISTEMA DE GESTÃO DE CONDOMÍNIO (SGC)
-- ARQUIVO: init.sql - Script de Inicialização do Banco de Dados
-- MOTOR: PostgreSQL 15+
-- ====================================================================

-- 1. Criação do Banco de Dados (Executar se necessário)
-- CREATE DATABASE sgc_condominio WITH ENCODING 'UTF8';
-- \c sgc_condominio;

-- Garante suporte a funções criptográficas e UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ====================================================================
-- FUNÇÕES E TRIGGERS GLOBAIS (Requisito Formal do Manual)
-- ====================================================================

-- Função que atualiza automaticamente a coluna atualizado_em em qualquer tabela
CREATE OR REPLACE FUNCTION trigger_atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- TABELA 1: USUÁRIOS E AUTENTICAÇÃO
-- Armazena os usuários do sistema com controle de perfis (RBAC)
-- ====================================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    tipo_usuario VARCHAR(20) NOT NULL CHECK (
        tipo_usuario IN ('ADMIN', 'SINDICO', 'PORTARIA', 'MORADOR')
    ),
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    precisa_trocar_senha BOOLEAN DEFAULT FALSE NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Trigger de atualização de timestamp na tabela de usuários
DROP TRIGGER IF EXISTS trg_usuarios_atualizado_em ON usuarios;
CREATE TRIGGER trg_usuarios_atualizado_em
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

-- ====================================================================
-- TABELA 2: AUDITORIA DE ACESSOS E LOGIN
-- Registra tentativas de login para histórico e controle de tentativas
-- ====================================================================
CREATE TABLE IF NOT EXISTS logs_acesso (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    email_informado VARCHAR(150) NOT NULL,
    ip_origem VARCHAR(45),
    user_agent TEXT,
    sucesso BOOLEAN NOT NULL,
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índices para otimização de busca e consultas frequentes
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo_usuario);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_data ON logs_acesso(data_hora);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_usuario ON logs_acesso(usuario_id);

-- ====================================================================
-- PROCEDURE OBRIGATÓRIA (Requisito da Etapa 7)
-- Registrar log de tentativa de login de forma segura e transacional
-- ====================================================================
CREATE OR REPLACE PROCEDURE pr_registrar_log_acesso(
    p_usuario_id INT,
    p_email VARCHAR(150),
    p_ip VARCHAR(45),
    p_user_agent TEXT,
    p_sucesso BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO logs_acesso (usuario_id, email_informado, ip_origem, user_agent, sucesso)
    VALUES (p_usuario_id, p_email, p_ip, p_user_agent, p_sucesso);
END;
$$;

-- ====================================================================
-- TABELA 3: UNIDADES (APARTAMENTOS E BLOCOS)
-- Armazena os apartamentos do condomínio e moradores vinculados
-- ====================================================================
CREATE TABLE IF NOT EXISTS unidades (
    id SERIAL PRIMARY KEY,
    bloco VARCHAR(20) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    andar INT,
    morador_responsavel_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_bloco_numero UNIQUE (bloco, numero)
);

-- Trigger de atualização de timestamp na tabela de unidades
DROP TRIGGER IF EXISTS trg_unidades_atualizado_em ON unidades;
CREATE TRIGGER trg_unidades_atualizado_em
    BEFORE UPDATE ON unidades
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

-- Vincula a coluna unidade_id na tabela usuarios
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_unidades_bloco ON unidades(bloco);
CREATE INDEX IF NOT EXISTS idx_usuarios_unidade ON usuarios(unidade_id);

-- ====================================================================
-- TABELA 4: ENCOMENDAS (PORTARIA E MORADORES)
-- ====================================================================
CREATE TABLE IF NOT EXISTS encomendas (
    id SERIAL PRIMARY KEY,
    unidade_id INT NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
    descricao VARCHAR(255) NOT NULL,
    codigo_rastreio VARCHAR(100),
    porteiro_recebedor_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    status VARCHAR(30) DEFAULT 'AGUARDANDO_RETIRADA' NOT NULL CHECK (
        status IN ('AGUARDANDO_RETIRADA', 'ENTREGUE')
    ),
    data_chegada TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_retirada TIMESTAMP WITH TIME ZONE,
    retirado_por VARCHAR(150),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Trigger de atualização de timestamp na tabela de encomendas
DROP TRIGGER IF EXISTS trg_encomendas_atualizado_em ON encomendas;
CREATE TRIGGER trg_encomendas_atualizado_em
    BEFORE UPDATE ON encomendas
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

CREATE INDEX IF NOT EXISTS idx_encomendas_unidade ON encomendas(unidade_id);
CREATE INDEX IF NOT EXISTS idx_encomendas_status ON encomendas(status);

-- ====================================================================
-- TABELA 5: ÁREAS COMUNS DO CONDOMÍNIO
-- ====================================================================
CREATE TABLE IF NOT EXISTS areas_comuns (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    capacidade_pessoas INT NOT NULL,
    taxa_limpeza NUMERIC(10, 2) DEFAULT 0.00,
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ====================================================================
-- TABELA 6: RESERVAS DE ÁREAS COMUNS
-- ====================================================================
CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    area_comum_id INT NOT NULL REFERENCES areas_comuns(id) ON DELETE CASCADE,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL,
    data_reserva DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'CONFIRMADA' NOT NULL CHECK (
        status IN ('CONFIRMADA', 'CANCELADA', 'CONCLUIDA')
    ),
    observacoes TEXT,
    chave_entregue BOOLEAN DEFAULT FALSE NOT NULL,
    chave_entregue_por INT REFERENCES usuarios(id) ON DELETE SET NULL,
    chave_entregue_para VARCHAR(150),
    chave_entregue_em TIMESTAMP WITH TIME ZONE,
    chave_devolvida BOOLEAN DEFAULT FALSE NOT NULL,
    chave_devolvida_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Trigger de atualização de timestamp
DROP TRIGGER IF EXISTS trg_reservas_atualizado_em ON reservas;
CREATE TRIGGER trg_reservas_atualizado_em
    BEFORE UPDATE ON reservas
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

-- ====================================================================
-- TRIGGER OBRIGATÓRIA: VALIDAÇÃO DE CONFLITO DE RESERVAS (Requisito Etapa 7)
-- Impede agendamento duplo da mesma área na mesma data no nível do banco
-- ====================================================================
CREATE OR REPLACE FUNCTION fn_validar_conflito_reserva()
RETURNS TRIGGER AS $$
DECLARE
    v_conflito_id INT;
BEGIN
    IF NEW.status = 'CONFIRMADA' THEN
        SELECT id INTO v_conflito_id
        FROM reservas
        WHERE area_comum_id = NEW.area_comum_id
          AND data_reserva = NEW.data_reserva
          AND status = 'CONFIRMADA'
          AND (TG_OP = 'INSERT' OR id <> NEW.id)
        LIMIT 1;

        IF v_conflito_id IS NOT NULL THEN
            RAISE EXCEPTION 'CONFLITO_RESERVA: Esta area comum ja possui reserva confirmada para esta data.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_conflito_reserva ON reservas;
CREATE TRIGGER trg_validar_conflito_reserva
    BEFORE INSERT OR UPDATE ON reservas
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_conflito_reserva();

CREATE INDEX IF NOT EXISTS idx_reservas_data ON reservas(data_reserva);
CREATE INDEX IF NOT EXISTS idx_reservas_area ON reservas(area_comum_id);
CREATE INDEX IF NOT EXISTS idx_reservas_status ON reservas(status);

-- ====================================================================
-- TABELA 7: MURAL DE AVISOS E COMUNICADOS OFICIAIS
-- ====================================================================
CREATE TABLE IF NOT EXISTS avisos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    mensagem TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'GERAL' NOT NULL CHECK (
        categoria IN ('GERAL', 'MANUTENCAO', 'URGENTE', 'ASSEMBLEIA')
    ),
    autor_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Trigger de atualização de timestamp
DROP TRIGGER IF EXISTS trg_avisos_atualizado_em ON avisos;
CREATE TRIGGER trg_avisos_atualizado_em
    BEFORE UPDATE ON avisos
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

CREATE INDEX IF NOT EXISTS idx_avisos_criado_em ON avisos(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_avisos_categoria ON avisos(categoria);




