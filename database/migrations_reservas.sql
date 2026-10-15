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

-- Inserção das áreas comuns padrão do condomínio
INSERT INTO areas_comuns (nome, descricao, capacidade_pessoas, taxa_limpeza) VALUES
('Salão de Festas Principal', 'Espaço climatizado com cozinha completa, mesas e cadeiras para eventos.', 80, 120.00),
('Churrasqueira Gourmet', 'Área externa coberta com churrasqueira a carvão, freezer e bancadas.', 30, 60.00),
('Quadra Poliesportiva', 'Quadra para prática de futebol, vôlei e basquete.', 20, 0.00)
ON CONFLICT DO NOTHING;

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
    -- Verifica se já existe reserva confirmada para a mesma área e data
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

-- Seed de teste: Reserva no Salão de Festas para o próximo sábado da moradora Ana Beatriz
INSERT INTO reservas (area_comum_id, usuario_id, unidade_id, data_reserva, status, observacoes)
VALUES 
(1, 3, 1, CURRENT_DATE + INTERVAL '5 days', 'CONFIRMADA', 'Aniversário familiar')
ON CONFLICT DO NOTHING;
