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

DROP TRIGGER IF EXISTS trg_avisos_atualizado_em ON avisos;
CREATE TRIGGER trg_avisos_atualizado_em
    BEFORE UPDATE ON avisos
    FOR EACH ROW
    EXECUTE FUNCTION trigger_atualizar_timestamp();

CREATE INDEX IF NOT EXISTS idx_avisos_criado_em ON avisos(criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_avisos_categoria ON avisos(categoria);

-- Seed inicial de comunicados
INSERT INTO avisos (titulo, mensagem, categoria, autor_id) VALUES
(
    'Manutencao Preventiva dos Elevadores - Bloco A e B',
    'Informamos a todos os moradores que na proxima quarta-feira, das 09h as 12h, sera realizada a revisao periodica dos elevadores sociais e de servico.',
    'MANUTENCAO',
    1
),
(
    'Convocacao para Assembleia Geral Ordinaria',
    'Prezados condominos, convocamos todos para a assembleia que ocorrera dia 25 as 19h30 no Salao de Festas. Pauta: prestacao de contas e melhorias na seguranca.',
    'ASSEMBLEIA',
    1
)
ON CONFLICT DO NOTHING;
