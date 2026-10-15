-- ====================================================================
-- SISTEMA DE GESTÃO DE CONDOMÍNIO (SGC) - PIM IV UNIP
-- MIGRATION: Módulo de Livro de Ocorrências e Controle de Portaria/Visitantes
-- MOTOR: PostgreSQL 15+
-- ====================================================================

-- 1. Desativa necessidade de troca de senha no usuário demo de testes
UPDATE usuarios 
SET precisa_trocar_senha = FALSE 
WHERE email = 'morador@condominio.com';

-- 2. Tabela de Ocorrências e Chamados Digitais
CREATE TABLE IF NOT EXISTS ocorrencias (
    id SERIAL PRIMARY KEY,
    unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL,
    usuario_id INT REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    categoria VARCHAR(50) NOT NULL DEFAULT 'GERAL', -- BARULHO, MANUTENCAO, VAZAMENTO, SEGURANCA, OUTROS
    status VARCHAR(30) NOT NULL DEFAULT 'ABERTO',   -- ABERTO, EM_ANALISE, CONCLUIDO, CANCELADO
    resposta_sindico TEXT NULL,
    respondido_por INT REFERENCES usuarios(id) ON DELETE SET NULL,
    respondido_em TIMESTAMP WITH TIME ZONE NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TRIGGER IF EXISTS trg_ocorrencias_atualizado_em ON ocorrencias;
CREATE TRIGGER trg_ocorrencias_atualizado_em
    BEFORE UPDATE ON ocorrencias
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

-- 3. Tabela de Visitantes e Prestadores de Serviço
CREATE TABLE IF NOT EXISTS visitantes (
    id SERIAL PRIMARY KEY,
    unidade_id INT REFERENCES unidades(id) ON DELETE CASCADE,
    autorizado_por_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    nome VARCHAR(150) NOT NULL,
    documento VARCHAR(30) NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'VISITANTE',   -- VISITANTE, PRESTADOR_SERVICO, DELIVERY
    data_prevista DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'AGUARDANDO', -- AGUARDANDO, NO_LOCAL, FINALIZADO, CANCELADO
    hora_entrada TIMESTAMP WITH TIME ZONE NULL,
    porteiro_entrada_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    hora_saida TIMESTAMP WITH TIME ZONE NULL,
    porteiro_saida_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    observacoes TEXT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

DROP TRIGGER IF EXISTS trg_visitantes_atualizado_em ON visitantes;
CREATE TRIGGER trg_visitantes_atualizado_em
    BEFORE UPDATE ON visitantes
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();
