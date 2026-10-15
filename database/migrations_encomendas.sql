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

DROP TRIGGER IF EXISTS trg_encomendas_atualizado_em ON encomendas;
CREATE TRIGGER trg_encomendas_atualizado_em
    BEFORE UPDATE ON encomendas
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

CREATE INDEX IF NOT EXISTS idx_encomendas_unidade ON encomendas(unidade_id);
CREATE INDEX IF NOT EXISTS idx_encomendas_status ON encomendas(status);

-- Seed de teste para encomendas
INSERT INTO encomendas (unidade_id, descricao, codigo_rastreio, porteiro_recebedor_id, status)
VALUES 
(1, 'Pacote Mercado Livre (Caixa)', 'BR-MLB-9823412', 2, 'AGUARDANDO_RETIRADA'),
(2, 'Envelope Documentos / Cartao', 'BR-CORR-123456', 2, 'AGUARDANDO_RETIRADA');
