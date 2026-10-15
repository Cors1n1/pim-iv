-- ====================================================================
-- PROJETO INTEGRADO MULTIDISCIPLINAR - PIM IV
-- CURSO SUPERIOR DE TECNOLOGIA EM ANÁLISE E DESENVOLVIMENTO DE SISTEMAS
-- SISTEMA DE GESTÃO DE CONDOMÍNIO (SGC)
-- ETAPA 7 DO MANUAL: PROJETO DE BANCO DE DADOS COMPLETO
-- ARQUIVO: schema_completo_pim_iv.sql
-- MOTOR DO BANCO: PostgreSQL 15+ (Compatível com 14, 15 e 16)
-- PADRÃO: ANSI SQL / PL/pgSQL
-- ENCODING: UTF-8
-- ====================================================================
-- CONTEÚDO DESTE SCRIPT:
--   1. Configurações de Ambiente e Extensões
--   2. DDL Completo das 11 Tabelas com Chaves Primárias, Estrangeiras e Checks
--   3. Índices de Otimização e Performance (B-Tree)
--   4. Triggers Automáticas de Integridade e Regras de Negócio
--   5. Stored Procedures e Functions em PL/pgSQL
--   6. Views Analíticas e Operacionais Prontas
--   7. Carga de Dados Inicial (Seed de Demonstração e Testes Acadêmicos)
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. CONFIGURAÇÕES DE AMBIENTE E EXTENSÕES
-- --------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ====================================================================
-- 2. DDL COMPLETO (TABELAS E INTEGRIDADE REFERENCIAL)
-- ====================================================================

-- TABELA 1: UNIDADES (APARTAMENTOS / CASAS E BLOCOS)
-- Criada primeiro para permitir a referência nas tabelas de usuários e movimentações.
CREATE TABLE IF NOT EXISTS unidades (
    id SERIAL PRIMARY KEY,
    bloco VARCHAR(20) NOT NULL,
    numero VARCHAR(20) NOT NULL,
    andar INT,
    morador_responsavel_id INT, -- Referência cruzada com usuários adicionada via FK posteriormente
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_unidades_bloco_numero UNIQUE (bloco, numero)
);

COMMENT ON TABLE unidades IS 'Armazena as unidades habitacionais (apartamentos, blocos, andares) do condomínio.';

-- TABELA 2: USUÁRIOS E AUTENTICAÇÃO (RBAC)
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
    unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE usuarios IS 'Armazena as credenciais, perfis de acesso e dados cadastrais dos usuários do sistema.';

-- Adiciona a FK do morador responsável na tabela unidades (integridade circular segura)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_unidades_morador_responsavel'
    ) THEN
        ALTER TABLE unidades
            ADD CONSTRAINT fk_unidades_morador_responsavel
            FOREIGN KEY (morador_responsavel_id) REFERENCES usuarios(id) ON DELETE SET NULL;
    END IF;
END $$;

-- TABELA 3: AUDITORIA DE ACESSOS E LOGIN (Segurança / OWASP Top 10)
CREATE TABLE IF NOT EXISTS logs_acesso (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    email_informado VARCHAR(150) NOT NULL,
    ip_origem VARCHAR(45),
    user_agent TEXT,
    sucesso BOOLEAN NOT NULL,
    data_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE logs_acesso IS 'Trilha de auditoria para registros de tentativas de autenticação e mitigação de força bruta.';

-- TABELA 4: PARÂMETROS E CONFIGURAÇÕES GLOBAIS DO CONDOMÍNIO
CREATE TABLE IF NOT EXISTS configuracoes_condominio (
    id SERIAL PRIMARY KEY,
    nome_condominio VARCHAR(150) NOT NULL DEFAULT 'Condomínio Residencial',
    endereco VARCHAR(255) DEFAULT 'Rua das Flores, 123 - Centro',
    telefone_portaria VARCHAR(50) DEFAULT '(11) 98765-4321',
    email_contato VARCHAR(100) DEFAULT 'contato@condominio.com',
    prazo_retomada_horas INT NOT NULL DEFAULT 24,
    prazo_standby_horas INT NOT NULL DEFAULT 48,
    intervalo_padrao_dias INT NOT NULL DEFAULT 30,
    dias_penalidade_queima INT NOT NULL DEFAULT 30,
    queima_prioridade_cancelamento BOOLEAN NOT NULL DEFAULT TRUE,
    enviar_email_ativo BOOLEAN NOT NULL DEFAULT TRUE,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE configuracoes_condominio IS 'Parâmetros operacionais e regras de governança condominial.';

-- TABELA 5: ÁREAS COMUNS E ESPAÇOS DE LAZER
CREATE TABLE IF NOT EXISTS areas_comuns (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL UNIQUE,
    descricao TEXT,
    capacidade_pessoas INT NOT NULL CHECK (capacidade_pessoas > 0),
    taxa_limpeza NUMERIC(10, 2) DEFAULT 0.00 NOT NULL CHECK (taxa_limpeza >= 0),
    hora_inicio TIME DEFAULT '08:00:00' NOT NULL,
    hora_fim TIME DEFAULT '22:00:00' NOT NULL,
    duracao_maxima_horas INT DEFAULT 4 NOT NULL CHECK (duracao_maxima_horas > 0),
    intervalo_dias_prioridade INT DEFAULT 30 NOT NULL CHECK (intervalo_dias_prioridade >= 0),
    max_reservas_ativas INT DEFAULT 2 NOT NULL CHECK (max_reservas_ativas > 0),
    prazo_standby_horas INT DEFAULT 48 NOT NULL CHECK (prazo_standby_horas >= 0),
    ativo BOOLEAN DEFAULT TRUE NOT NULL,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE areas_comuns IS 'Espaços comunitários disponíveis para locação e uso pelos condôminos.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_areas_comuns_nome'
    ) THEN
        ALTER TABLE areas_comuns ADD CONSTRAINT uq_areas_comuns_nome UNIQUE (nome);
    END IF;
END $$;

-- TABELA 6: RESERVAS DE ÁREAS COMUNS
CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    area_comum_id INT NOT NULL REFERENCES areas_comuns(id) ON DELETE CASCADE,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL,
    data_reserva DATE NOT NULL,
    hora_inicio TIME DEFAULT '08:00:00' NOT NULL,
    hora_fim TIME DEFAULT '12:00:00' NOT NULL,
    status VARCHAR(20) DEFAULT 'CONFIRMADA' NOT NULL CHECK (
        status IN ('CONFIRMADA', 'CANCELADA', 'CONCLUIDA', 'STANDBY')
    ),
    prioridade VARCHAR(20) DEFAULT 'ALTA' NOT NULL CHECK (
        prioridade IN ('ALTA', 'MEDIA', 'BAIXA')
    ),
    prioridade_queimada BOOLEAN DEFAULT FALSE NOT NULL,
    oferta_retomada_ate TIMESTAMP WITH TIME ZONE,
    observacoes TEXT,
    chave_entregue BOOLEAN DEFAULT FALSE NOT NULL,
    chave_entregue_por INT REFERENCES usuarios(id) ON DELETE SET NULL,
    chave_entregue_para VARCHAR(150),
    chave_entregue_em TIMESTAMP WITH TIME ZONE,
    chave_devolvida BOOLEAN DEFAULT FALSE NOT NULL,
    chave_devolvida_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT chk_horarios_reserva CHECK (hora_fim > hora_inicio)
);

COMMENT ON TABLE reservas IS 'Agendamentos e reservas de espaços comuns com controle de chaves e status.';

-- TABELA 7: LISTA DE CONVIDADOS DA RESERVA
CREATE TABLE IF NOT EXISTS convidados_reserva (
    id SERIAL PRIMARY KEY,
    reserva_id INT NOT NULL REFERENCES reservas(id) ON DELETE CASCADE,
    nome_completo VARCHAR(150) NOT NULL,
    documento VARCHAR(50),
    email VARCHAR(150),
    convite_enviado BOOLEAN DEFAULT FALSE NOT NULL,
    entrada_registrada BOOLEAN DEFAULT FALSE NOT NULL,
    entrada_em TIMESTAMP WITH TIME ZONE,
    saida_registrada BOOLEAN DEFAULT FALSE NOT NULL,
    saida_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE convidados_reserva IS 'Controle de acesso para eventos e listas de convidados vinculadas a reservas.';

-- TABELA 8: ENCOMENDAS E CORRESPONDÊNCIAS
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

COMMENT ON TABLE encomendas IS 'Gestão e rastreabilidade de pacotes, correspondências e entregas na portaria.';

-- TABELA 9: MURAL DE AVISOS E COMUNICADOS OFICIAIS
CREATE TABLE IF NOT EXISTS avisos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    mensagem TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'GERAL' NOT NULL CHECK (
        categoria IN ('GERAL', 'MANUTENCAO', 'URGENTE', 'ASSEMBLEIA')
    ),
    link_anexo VARCHAR(500),
    autor_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE avisos IS 'Quadro de avisos digitais com comunicados da administração para os moradores.';

-- TABELA 10: LIVRO DE OCORRÊNCIAS E CHAMADOS DIGITAIS
CREATE TABLE IF NOT EXISTS ocorrencias (
    id SERIAL PRIMARY KEY,
    unidade_id INT REFERENCES unidades(id) ON DELETE SET NULL,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    categoria VARCHAR(50) DEFAULT 'GERAL' NOT NULL CHECK (
        categoria IN ('GERAL', 'BARULHO', 'MANUTENCAO', 'VAZAMENTO', 'SEGURANCA', 'OUTROS')
    ),
    status VARCHAR(30) DEFAULT 'ABERTO' NOT NULL CHECK (
        status IN ('ABERTO', 'EM_ANALISE', 'CONCLUIDO', 'CANCELADO')
    ),
    resposta_sindico TEXT,
    respondido_por INT REFERENCES usuarios(id) ON DELETE SET NULL,
    respondido_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE ocorrencias IS 'Chamados, reclamações e solicitações de manutenção abertas pelos condôminos.';

-- TABELA 11: CONTROLE DE VISITANTES E PRESTADORES DE SERVIÇO
CREATE TABLE IF NOT EXISTS visitantes (
    id SERIAL PRIMARY KEY,
    unidade_id INT NOT NULL REFERENCES unidades(id) ON DELETE CASCADE,
    autorizado_por_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    nome VARCHAR(150) NOT NULL,
    documento VARCHAR(30),
    tipo VARCHAR(30) DEFAULT 'VISITANTE' NOT NULL CHECK (
        tipo IN ('VISITANTE', 'PRESTADOR_SERVICO', 'DELIVERY')
    ),
    data_prevista DATE NOT NULL,
    status VARCHAR(30) DEFAULT 'AGUARDANDO' NOT NULL CHECK (
        status IN ('AGUARDANDO', 'NO_LOCAL', 'FINALIZADO', 'CANCELADO')
    ),
    hora_entrada TIMESTAMP WITH TIME ZONE,
    porteiro_entrada_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    hora_saida TIMESTAMP WITH TIME ZONE,
    porteiro_saida_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    observacoes TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE visitantes IS 'Controle de fluxo de portaria para entrada e saída de prestadores e convidados.';

-- ====================================================================
-- 3. ÍNDICES DE PERFORMANCE E OTIMIZAÇÃO (B-TREE)
-- ====================================================================

-- Usuários e Unidades
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo_usuario);
CREATE INDEX IF NOT EXISTS idx_usuarios_unidade ON usuarios(unidade_id);
CREATE INDEX IF NOT EXISTS idx_unidades_bloco ON unidades(bloco);

-- Logs e Auditoria
CREATE INDEX IF NOT EXISTS idx_logs_acesso_data ON logs_acesso(data_hora DESC);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_usuario ON logs_acesso(usuario_id);
CREATE INDEX IF NOT EXISTS idx_logs_acesso_email ON logs_acesso(email_informado);

-- Reservas e Convidados
CREATE INDEX IF NOT EXISTS idx_reservas_data ON reservas(data_reserva);
CREATE INDEX IF NOT EXISTS idx_reservas_area ON reservas(area_comum_id);
CREATE INDEX IF NOT EXISTS idx_reservas_usuario ON reservas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_reservas_status ON reservas(status);
CREATE INDEX IF NOT EXISTS idx_convidados_reserva ON convidados_reserva(reserva_id);

-- Encomendas
CREATE INDEX IF NOT EXISTS idx_encomendas_unidade ON encomendas(unidade_id);
CREATE INDEX IF NOT EXISTS idx_encomendas_status ON encomendas(status);
CREATE INDEX IF NOT EXISTS idx_encomendas_data_chegada ON encomendas(data_chegada DESC);

-- Avisos e Ocorrências
CREATE INDEX IF NOT EXISTS idx_avisos_criado_em ON avisos(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_avisos_categoria ON avisos(categoria);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_status ON ocorrencias(status);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_usuario ON ocorrencias(usuario_id);

-- Visitantes
CREATE INDEX IF NOT EXISTS idx_visitantes_data_prevista ON visitantes(data_prevista);
CREATE INDEX IF NOT EXISTS idx_visitantes_status ON visitantes(status);
CREATE INDEX IF NOT EXISTS idx_visitantes_unidade ON visitantes(unidade_id);

-- ====================================================================
-- 4. TRIGGERS AUTOMÁTICAS DE INTEGRIDADE E REGRAS DE NEGÓCIO
-- ====================================================================

-- --------------------------------------------------------------------
-- TRIGGER 1: ATUALIZAÇÃO AUTOMÁTICA DE TIMESTAMP (atualizado_em)
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicação da Trigger de timestamp em todas as tabelas com atualizado_em
DROP TRIGGER IF EXISTS trg_usuarios_atualizado_em ON usuarios;
CREATE TRIGGER trg_usuarios_atualizado_em
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_unidades_atualizado_em ON unidades;
CREATE TRIGGER trg_unidades_atualizado_em
    BEFORE UPDATE ON unidades
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_config_atualizado_em ON configuracoes_condominio;
CREATE TRIGGER trg_config_atualizado_em
    BEFORE UPDATE ON configuracoes_condominio
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_reservas_atualizado_em ON reservas;
CREATE TRIGGER trg_reservas_atualizado_em
    BEFORE UPDATE ON reservas
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_encomendas_atualizado_em ON encomendas;
CREATE TRIGGER trg_encomendas_atualizado_em
    BEFORE UPDATE ON encomendas
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_avisos_atualizado_em ON avisos;
CREATE TRIGGER trg_avisos_atualizado_em
    BEFORE UPDATE ON avisos
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_ocorrencias_atualizado_em ON ocorrencias;
CREATE TRIGGER trg_ocorrencias_atualizado_em
    BEFORE UPDATE ON ocorrencias
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

DROP TRIGGER IF EXISTS trg_visitantes_atualizado_em ON visitantes;
CREATE TRIGGER trg_visitantes_atualizado_em
    BEFORE UPDATE ON visitantes
    FOR EACH ROW EXECUTE FUNCTION trigger_atualizar_timestamp();

-- --------------------------------------------------------------------
-- TRIGGER 2: VALIDAÇÃO DE CONFLITO DE RESERVAS NO BANCO (Integridade Rígida)
-- Impede que duas reservas confirmadas ocupem o mesmo espaço na mesma data.
-- --------------------------------------------------------------------
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
            RAISE EXCEPTION 'CONFLITO_RESERVA: A area comum solicitada ja possui uma reserva confirmada para a data %.', NEW.data_reserva;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_conflito_reserva ON reservas;
CREATE TRIGGER trg_validar_conflito_reserva
    BEFORE INSERT OR UPDATE ON reservas
    FOR EACH ROW EXECUTE FUNCTION fn_validar_conflito_reserva();

-- --------------------------------------------------------------------
-- TRIGGER 3: IMPEDIR RESERVA RETROATIVA (Regra de Negócio)
-- Bloqueia a inserção de reservas para datas anteriores à data corrente.
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_impedir_reserva_retroativa()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.data_reserva < CURRENT_DATE THEN
        RAISE EXCEPTION 'DATA_INVALIDA: Nao e permitido realizar reservas para datas retroativas (data informada: %).', NEW.data_reserva;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_impedir_reserva_retroativa ON reservas;
CREATE TRIGGER trg_impedir_reserva_retroativa
    BEFORE INSERT ON reservas
    FOR EACH ROW EXECUTE FUNCTION fn_impedir_reserva_retroativa();

-- --------------------------------------------------------------------
-- TRIGGER 4: AUDITORIA E CONSISTÊNCIA DE BAIXA DE ENCOMENDAS
-- Ao mudar status para ENTREGUE, se data_retirada estiver vazia, preenche agora.
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_garantir_baixa_encomenda()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'ENTREGUE' AND OLD.status <> 'ENTREGUE' THEN
        IF NEW.data_retirada IS NULL THEN
            NEW.data_retirada = CURRENT_TIMESTAMP;
        END IF;
        IF NEW.retirado_por IS NULL OR TRIM(NEW.retirado_por) = '' THEN
            NEW.retirado_por = 'Morador / Retirada Balcão';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_garantir_baixa_encomenda ON encomendas;
CREATE TRIGGER trg_garantir_baixa_encomenda
    BEFORE UPDATE ON encomendas
    FOR EACH ROW EXECUTE FUNCTION fn_garantir_baixa_encomenda();

-- --------------------------------------------------------------------
-- TRIGGER 5: ATUALIZAÇÃO AUTOMÁTICA DE DATA DE RESPOSTA EM OCORRÊNCIAS
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_log_resposta_ocorrencia()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.resposta_sindico IS NOT NULL AND OLD.resposta_sindico IS NULL) 
       OR (NEW.status IN ('CONCLUIDO', 'EM_ANALISE') AND OLD.status = 'ABERTO') THEN
        IF NEW.respondido_em IS NULL THEN
            NEW.respondido_em = CURRENT_TIMESTAMP;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_log_resposta_ocorrencia ON ocorrencias;
CREATE TRIGGER trg_log_resposta_ocorrencia
    BEFORE UPDATE ON ocorrencias
    FOR EACH ROW EXECUTE FUNCTION fn_log_resposta_ocorrencia();

-- ====================================================================
-- 5. STORED PROCEDURES E FUNCTIONS NATIVAS (PL/pgSQL)
-- ====================================================================

-- --------------------------------------------------------------------
-- PROCEDURE 1: REGISTRAR LOG DE ACESSO (Segurança / Trilha de Auditoria)
-- --------------------------------------------------------------------
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
    INSERT INTO logs_acesso (usuario_id, email_informado, ip_origem, user_agent, sucesso, data_hora)
    VALUES (p_usuario_id, p_email, p_ip, p_user_agent, p_sucesso, CURRENT_TIMESTAMP);
END;
$$;

-- --------------------------------------------------------------------
-- PROCEDURE 2: DAR BAIXA EM ENCOMENDA COM VALIDAÇÃO TRANSAÇÃO
-- --------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_dar_baixa_encomenda(
    p_encomenda_id INT,
    p_retirado_por VARCHAR(150),
    p_porteiro_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_atual VARCHAR(30);
BEGIN
    SELECT status INTO v_status_atual 
    FROM encomendas 
    WHERE id = p_encomenda_id;

    IF v_status_atual IS NULL THEN
        RAISE EXCEPTION 'ENCOMENDA_NAO_ENCONTRADA: Nao existe encomenda com ID %.', p_encomenda_id;
    END IF;

    IF v_status_atual = 'ENTREGUE' THEN
        RAISE EXCEPTION 'ENCOMENDA_JA_ENTREGUE: A encomenda ID % ja foi retirada anteriormente.', p_encomenda_id;
    END IF;

    UPDATE encomendas
    SET status = 'ENTREGUE',
        data_retirada = CURRENT_TIMESTAMP,
        retirado_por = p_retirado_por,
        porteiro_recebedor_id = COALESCE(p_porteiro_id, porteiro_recebedor_id),
        atualizado_em = CURRENT_TIMESTAMP
    WHERE id = p_encomenda_id;
END;
$$;

-- --------------------------------------------------------------------
-- PROCEDURE 3: REGISTRAR ENTRADA DE VISITANTE NA PORTARIA
-- --------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_registrar_entrada_visitante(
    p_visitante_id INT,
    p_porteiro_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_atual VARCHAR(30);
BEGIN
    SELECT status INTO v_status_atual FROM visitantes WHERE id = p_visitante_id;

    IF v_status_atual IS NULL THEN
        RAISE EXCEPTION 'VISITANTE_NAO_ENCONTRADO: Registro de visitante % inexistente.', p_visitante_id;
    END IF;

    UPDATE visitantes
    SET status = 'NO_LOCAL',
        hora_entrada = CURRENT_TIMESTAMP,
        porteiro_entrada_id = p_porteiro_id,
        atualizado_em = CURRENT_TIMESTAMP
    WHERE id = p_visitante_id;
END;
$$;

-- --------------------------------------------------------------------
-- PROCEDURE 4: REGISTRAR SAÍDA DE VISITANTE NA PORTARIA
-- --------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_registrar_saida_visitante(
    p_visitante_id INT,
    p_porteiro_id INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_atual VARCHAR(30);
BEGIN
    SELECT status INTO v_status_atual FROM visitantes WHERE id = p_visitante_id;

    IF v_status_atual IS NULL THEN
        RAISE EXCEPTION 'VISITANTE_NAO_ENCONTRADO: Registro de visitante % inexistente.', p_visitante_id;
    END IF;

    UPDATE visitantes
    SET status = 'FINALIZADO',
        hora_saida = CURRENT_TIMESTAMP,
        porteiro_saida_id = p_porteiro_id,
        atualizado_em = CURRENT_TIMESTAMP
    WHERE id = p_visitante_id;
END;
$$;

-- --------------------------------------------------------------------
-- PROCEDURE 5: CONTROLE DE CHAVES DE ÁREA DE LAZER
-- --------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE pr_controle_chaves_reserva(
    p_reserva_id INT,
    p_porteiro_id INT,
    p_retirado_por VARCHAR(150),
    p_acao VARCHAR(20) -- 'ENTREGA' ou 'DEVOLUCAO'
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_acao = 'ENTREGA' THEN
        UPDATE reservas
        SET chave_entregue = TRUE,
            chave_entregue_por = p_porteiro_id,
            chave_entregue_para = p_retirado_por,
            chave_entregue_em = CURRENT_TIMESTAMP,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = p_reserva_id;
    ELSIF p_acao = 'DEVOLUCAO' THEN
        UPDATE reservas
        SET chave_devolvida = TRUE,
            chave_devolvida_em = CURRENT_TIMESTAMP,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = p_reserva_id;
    ELSE
        RAISE EXCEPTION 'ACAO_INVALIDA: A acao informada deve ser ENTREGA ou DEVOLUCAO.';
    END IF;
END;
$$;

-- --------------------------------------------------------------------
-- FUNCTION 1: DASHBOARD ANALÍTICO EM JSON
-- Retorna uma visão estruturada das principais métricas do condomínio
-- --------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_obter_resumo_dashboard()
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    v_resultado JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_moradores', (SELECT COUNT(*) FROM usuarios WHERE tipo_usuario = 'MORADOR' AND ativo = TRUE),
        'total_unidades', (SELECT COUNT(*) FROM unidades WHERE ativo = TRUE),
        'encomendas_aguardando', (SELECT COUNT(*) FROM encomendas WHERE status = 'AGUARDANDO_RETIRADA'),
        'reservas_hoje', (SELECT COUNT(*) FROM reservas WHERE data_reserva = CURRENT_DATE AND status = 'CONFIRMADA'),
        'visitantes_no_local', (SELECT COUNT(*) FROM visitantes WHERE status = 'NO_LOCAL'),
        'ocorrencias_abertas', (SELECT COUNT(*) FROM ocorrencias WHERE status IN ('ABERTO', 'EM_ANALISE'))
    ) INTO v_resultado;

    RETURN v_resultado;
END;
$$;

-- ====================================================================
-- 6. VIEWS ANALÍTICAS E OPERACIONAIS
-- ====================================================================

-- --------------------------------------------------------------------
-- VIEW 1: ENCOMENDAS PENDENTES DE RETIRADA
-- Exibe pacotes na portaria com dados da unidade e cálculo de permanência
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_encomendas_pendentes AS
SELECT 
    e.id AS encomenda_id,
    u.bloco,
    u.numero AS unidade_numero,
    COALESCE(morador.nome, 'Não vinculado') AS morador_nome,
    morador.telefone AS morador_telefone,
    e.descricao,
    e.codigo_rastreio,
    e.data_chegada,
    porteiro.nome AS recebido_por_porteiro,
    DATE_TRUNC('hour', CURRENT_TIMESTAMP - e.data_chegada) AS tempo_aguardando
FROM encomendas e
JOIN unidades u ON e.unidade_id = u.id
LEFT JOIN usuarios morador ON u.morador_responsavel_id = morador.id
LEFT JOIN usuarios porteiro ON e.porteiro_recebedor_id = porteiro.id
WHERE e.status = 'AGUARDANDO_RETIRADA'
ORDER BY e.data_chegada ASC;

COMMENT ON VIEW vw_encomendas_pendentes IS 'Lista todas as encomendas que ainda não foram retiradas na portaria.';

-- --------------------------------------------------------------------
-- VIEW 2: RESERVAS DETALHADAS COM CONVIDADOS
-- Consolida área, solicitante, data e total de convidados cadastrados
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_reservas_detalhadas AS
SELECT 
    r.id AS reserva_id,
    ac.nome AS area_comum,
    r.data_reserva,
    r.hora_inicio,
    r.hora_fim,
    u.nome AS morador_nome,
    u.email AS morador_email,
    un.bloco,
    un.numero AS unidade_numero,
    r.status,
    r.prioridade,
    r.chave_entregue,
    r.chave_devolvida,
    COUNT(c.id) AS total_convidados,
    SUM(CASE WHEN c.entrada_registrada THEN 1 ELSE 0 END) AS convidados_presentes
FROM reservas r
JOIN areas_comuns ac ON r.area_comum_id = ac.id
JOIN usuarios u ON r.usuario_id = u.id
LEFT JOIN unidades un ON r.unidade_id = un.id
LEFT JOIN convidados_reserva c ON r.id = c.reserva_id
GROUP BY r.id, ac.nome, u.nome, u.email, un.bloco, un.numero
ORDER BY r.data_reserva ASC, r.hora_inicio ASC;

COMMENT ON VIEW vw_reservas_detalhadas IS 'Visão unificada das reservas de áreas comuns e estatísticas da lista de convidados.';

-- --------------------------------------------------------------------
-- VIEW 3: OCORRÊNCIAS PENDENTES DE ANÁLISE PELO SÍNDICO
-- Chamados em aberto ordenados pelos mais antigos
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ocorrencias_pendentes AS
SELECT 
    o.id AS ocorrencia_id,
    o.titulo,
    o.descricao,
    o.categoria,
    o.status,
    u.nome AS solicitante_nome,
    un.bloco,
    un.numero AS unidade_numero,
    o.criado_em AS data_abertura,
    DATE_TRUNC('hour', CURRENT_TIMESTAMP - o.criado_em) AS tempo_em_aberto
FROM ocorrencias o
JOIN usuarios u ON o.usuario_id = u.id
LEFT JOIN unidades un ON o.unidade_id = un.id
WHERE o.status IN ('ABERTO', 'EM_ANALISE')
ORDER BY o.criado_em ASC;

COMMENT ON VIEW vw_ocorrencias_pendentes IS 'Painel de chamados pendentes para a gestão do condomínio.';

-- --------------------------------------------------------------------
-- VIEW 4: VISITANTES ATUALMENTE PRESENTES NO CONDOMÍNIO
-- Monitoramento de segurança com hora de entrada e tempo de permanência
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_visitantes_no_condominio AS
SELECT 
    v.id AS visitante_id,
    v.nome,
    v.documento,
    v.tipo,
    un.bloco,
    un.numero AS unidade_numero,
    morador.nome AS autorizado_por,
    p_in.nome AS liberado_por_porteiro,
    v.hora_entrada,
    DATE_TRUNC('minute', CURRENT_TIMESTAMP - v.hora_entrada) AS tempo_permanencia
FROM visitantes v
JOIN unidades un ON v.unidade_id = un.id
LEFT JOIN usuarios morador ON v.autorizado_por_id = morador.id
LEFT JOIN usuarios p_in ON v.porteiro_entrada_id = p_in.id
WHERE v.status = 'NO_LOCAL'
ORDER BY v.hora_entrada ASC;

COMMENT ON VIEW vw_visitantes_no_condominio IS 'Painel em tempo real de visitantes e prestadores dentro das dependências do condomínio.';

-- --------------------------------------------------------------------
-- VIEW 5: PAINEL DIÁRIO DA PORTARIA
-- Visão consolidada para o monitor da guarita para a data de hoje
-- --------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_painel_portaria_hoje AS
SELECT 
    'VISITANTE_PREVISTO' AS tipo_evento,
    v.id AS id_referencia,
    v.nome AS descricao_principal,
    CONCAT('Bloco ', un.bloco, ' - Apt ', un.numero) AS localizacao,
    v.status AS situacao,
    v.data_prevista::text AS data_hora_evento
FROM visitantes v
JOIN unidades un ON v.unidade_id = un.id
WHERE v.data_prevista = CURRENT_DATE AND v.status = 'AGUARDANDO'

UNION ALL

SELECT 
    'RESERVA_HOJE' AS tipo_evento,
    r.id AS id_referencia,
    CONCAT(ac.nome, ' (', u.nome, ')') AS descricao_principal,
    CONCAT(r.hora_inicio::text, ' às ', r.hora_fim::text) AS localizacao,
    r.status AS situacao,
    r.data_reserva::text AS data_hora_evento
FROM reservas r
JOIN areas_comuns ac ON r.area_comum_id = ac.id
JOIN usuarios u ON r.usuario_id = u.id
WHERE r.data_reserva = CURRENT_DATE AND r.status = 'CONFIRMADA';

COMMENT ON VIEW vw_painel_portaria_hoje IS 'Resumo operacional do dia corrente para consulta rápida da equipe de portaria.';

-- ====================================================================
-- 7. CARGA DE DADOS INICIAL (SEED ACADÊMICO DE TESTES)
-- ====================================================================

-- 7.1. Configurações Padrão
INSERT INTO configuracoes_condominio (
    nome_condominio, endereco, telefone_portaria, email_contato,
    prazo_retomada_horas, prazo_standby_horas, intervalo_padrao_dias, dias_penalidade_queima
) VALUES (
    'Residencial Parque das Acácias',
    'Av. Paulista, 1500 - Bela Vista, São Paulo - SP',
    '(11) 3254-8900',
    'portaria@acacias.condominio.com',
    24, 48, 30, 30
) ON CONFLICT DO NOTHING;

-- 7.2. Usuários Principais (Senhas bcrypt seguras)
-- Hash '$2b$12$bMTHBVJc8wJ2o2qTrvcgDekESfqCQp45qhL26RLTlpuoHNnl75LJ6' = senha123
-- Hash '$2b$12$AAtVaLmP2JVW0v6lar3tHuqCSEVUre7dm2zOyAa9J2u12XUX2yuyK' = portaria123
-- Hash '$2b$12$7dDQPNJgSQYvwQbD.hmOPObSSNteLeb6qf7cUIRMVZ7/MKYFnMZkW' = morador123
INSERT INTO usuarios (nome, email, senha_hash, telefone, tipo_usuario, ativo, precisa_trocar_senha)
VALUES 
    ('Carlos Silva (Síndico Geral)', 'admin@condominio.com', '$2b$12$bMTHBVJc8wJ2o2qTrvcgDekESfqCQp45qhL26RLTlpuoHNnl75LJ6', '(11) 98765-4321', 'ADMIN', true, false),
    ('Marcos Oliveira (Porteiro Diurno)', 'portaria@condominio.com', '$2b$12$AAtVaLmP2JVW0v6lar3tHuqCSEVUre7dm2zOyAa9J2u12XUX2yuyK', '(11) 97654-3210', 'PORTARIA', true, false),
    ('Ana Beatriz (Moradora Apto 101)', 'morador@condominio.com', '$2b$12$7dDQPNJgSQYvwQbD.hmOPObSSNteLeb6qf7cUIRMVZ7/MKYFnMZkW', '(11) 96543-2109', 'MORADOR', true, false)
ON CONFLICT (email) DO UPDATE 
SET nome = EXCLUDED.nome, tipo_usuario = EXCLUDED.tipo_usuario, precisa_trocar_senha = FALSE;

-- 7.3. Unidades Habitacionais
INSERT INTO unidades (bloco, numero, andar)
VALUES 
    ('A', '101', 1),
    ('A', '102', 1),
    ('A', '201', 2),
    ('B', '101', 1),
    ('B', '102', 1)
ON CONFLICT (bloco, numero) DO NOTHING;

-- Vincula a moradora Ana Beatriz à unidade do Bloco A - Apto 101
UPDATE usuarios 
SET unidade_id = (SELECT id FROM unidades WHERE bloco = 'A' AND numero = '101' LIMIT 1) 
WHERE email = 'morador@condominio.com';

UPDATE unidades 
SET morador_responsavel_id = (SELECT id FROM usuarios WHERE email = 'morador@condominio.com' LIMIT 1)
WHERE bloco = 'A' AND numero = '101';

-- 7.4. Áreas Comuns
INSERT INTO areas_comuns (nome, descricao, capacidade_pessoas, taxa_limpeza, hora_inicio, hora_fim, duracao_maxima_horas)
VALUES 
    ('Salão de Festas Principal', 'Espaço climatizado com cozinha completa, mesas e cadeiras para até 80 pessoas.', 80, 120.00, '08:00:00', '23:00:00', 6),
    ('Churrasqueira Gourmet', 'Área externa coberta com churrasqueira a carvão, freezer horizontal e bancadas.', 30, 60.00, '09:00:00', '22:00:00', 5),
    ('Quadra Poliesportiva', 'Quadra com iluminação de LED para futebol de salão, basquete e vôlei.', 20, 0.00, '07:00:00', '22:00:00', 2),
    ('Espaço Fitness / Academia', 'Equipamentos modernos para musculação e exercícios aeróbicos.', 15, 0.00, '06:00:00', '23:00:00', 2)
ON CONFLICT (nome) DO UPDATE 
SET capacidade_pessoas = EXCLUDED.capacidade_pessoas, taxa_limpeza = EXCLUDED.taxa_limpeza;

-- 7.5. Avisos Oficiais do Mural
INSERT INTO avisos (titulo, mensagem, categoria, link_anexo, autor_id)
SELECT 
    'Manutenção Preventiva dos Elevadores', 
    'Aviso aos condôminos: no dia 20 os elevadores do Bloco A passarão por manutenção entre 09:00 e 12:00.', 
    'MANUTENCAO', 
    NULL, 
    u.id
FROM usuarios u 
WHERE u.email = 'admin@condominio.com'
  AND NOT EXISTS (SELECT 1 FROM avisos WHERE titulo = 'Manutenção Preventiva dos Elevadores')
LIMIT 1;

INSERT INTO avisos (titulo, mensagem, categoria, link_anexo, autor_id)
SELECT 
    'Assembleia Geral Ordinária', 
    'Convocação oficial para a Assembleia Geral. Pauta: prestação de contas e eleição do conselho fiscal.', 
    'ASSEMBLEIA', 
    'https://meet.google.com/exemplo-pim-unip', 
    u.id
FROM usuarios u 
WHERE u.email = 'admin@condominio.com'
  AND NOT EXISTS (SELECT 1 FROM avisos WHERE titulo = 'Assembleia Geral Ordinária')
LIMIT 1;

-- 7.6. Encomendas de Teste
INSERT INTO encomendas (unidade_id, descricao, codigo_rastreio, porteiro_recebedor_id, status, data_chegada)
SELECT 
    u.id, 
    'Caixa Amazon Prime (Livros e Eletrônicos)', 
    'BR987654321AMZ', 
    (SELECT id FROM usuarios WHERE email = 'portaria@condominio.com' LIMIT 1), 
    'AGUARDANDO_RETIRADA', 
    CURRENT_TIMESTAMP - INTERVAL '3 hours'
FROM unidades u 
WHERE u.bloco = 'A' AND u.numero = '101'
  AND NOT EXISTS (SELECT 1 FROM encomendas WHERE codigo_rastreio = 'BR987654321AMZ')
LIMIT 1;

INSERT INTO encomendas (unidade_id, descricao, codigo_rastreio, porteiro_recebedor_id, status, data_chegada)
SELECT 
    u.id, 
    'Envelope Sedex Documentos', 
    'QB123456789BR', 
    (SELECT id FROM usuarios WHERE email = 'portaria@condominio.com' LIMIT 1), 
    'AGUARDANDO_RETIRADA', 
    CURRENT_TIMESTAMP - INTERVAL '1 day'
FROM unidades u 
WHERE u.bloco = 'A' AND u.numero = '101'
  AND NOT EXISTS (SELECT 1 FROM encomendas WHERE codigo_rastreio = 'QB123456789BR')
LIMIT 1;

-- 7.7. Ocorrências / Chamados
INSERT INTO ocorrencias (unidade_id, usuario_id, titulo, descricao, categoria, status, criado_em)
SELECT 
    usr.unidade_id,
    usr.id,
    'Infiltração no teto do corredor',
    'Notamos umidade e pequena goteira no hall do 1º andar próximo ao apto 101.',
    'MANUTENCAO',
    'EM_ANALISE',
    CURRENT_TIMESTAMP - INTERVAL '2 days'
FROM usuarios usr 
WHERE usr.email = 'morador@condominio.com'
  AND NOT EXISTS (SELECT 1 FROM ocorrencias WHERE titulo = 'Infiltração no teto do corredor')
LIMIT 1;

-- 7.8. Visitantes e Prestadores
INSERT INTO visitantes (unidade_id, autorizado_por_id, nome, documento, tipo, data_prevista, status, hora_entrada, porteiro_entrada_id)
SELECT 
    usr.unidade_id,
    usr.id,
    'Roberto Santos (Técnico Internet)',
    '45.890.123-4',
    'PRESTADOR_SERVICO',
    CURRENT_DATE,
    'NO_LOCAL',
    CURRENT_TIMESTAMP - INTERVAL '45 minutes',
    (SELECT id FROM usuarios WHERE email = 'portaria@condominio.com' LIMIT 1)
FROM usuarios usr 
WHERE usr.email = 'morador@condominio.com'
  AND NOT EXISTS (SELECT 1 FROM visitantes WHERE documento = '45.890.123-4' AND data_prevista = CURRENT_DATE)
LIMIT 1;

INSERT INTO visitantes (unidade_id, autorizado_por_id, nome, documento, tipo, data_prevista, status)
SELECT 
    usr.unidade_id,
    usr.id,
    'Juliana Mendes',
    '32.123.456-7',
    'VISITANTE',
    CURRENT_DATE,
    'AGUARDANDO'
FROM usuarios usr 
WHERE usr.email = 'morador@condominio.com'
  AND NOT EXISTS (SELECT 1 FROM visitantes WHERE documento = '32.123.456-7' AND data_prevista = CURRENT_DATE)
LIMIT 1;

-- 7.9. Reserva de Demonstração (Salão de Festas para o próximo sábado)
INSERT INTO reservas (area_comum_id, usuario_id, unidade_id, data_reserva, hora_inicio, hora_fim, status, observacoes)
SELECT 
    ac.id,
    usr.id,
    usr.unidade_id,
    CURRENT_DATE + INTERVAL '5 days',
    '12:00:00',
    '18:00:00',
    'CONFIRMADA',
    'Almoço em família e comemoração de aniversário.'
FROM areas_comuns ac, usuarios usr
WHERE ac.nome = 'Salão de Festas Principal' 
  AND usr.email = 'morador@condominio.com'
  AND NOT EXISTS (
      SELECT 1 FROM reservas r 
      WHERE r.area_comum_id = ac.id 
        AND r.data_reserva = CURRENT_DATE + INTERVAL '5 days'
        AND r.status = 'CONFIRMADA'
  )
LIMIT 1;

-- ====================================================================
-- FIM DO SCRIPT: schema_completo_pim_iv.sql
-- ====================================================================
