-- ====================================================================
-- PIM IV - SISTEMA DE GESTÃO DE CONDOMÍNIO (SGC)
-- ARQUIVO: seed.sql - Carga de Usuários Iniciais para Teste
-- ====================================================================

-- Inserção de usuários iniciais (com senhas criptografadas em bcrypt padrão seguro)
INSERT INTO usuarios (nome, email, senha_hash, telefone, tipo_usuario, ativo)
VALUES 
    (
        'Carlos Silva (Síndico Geral)',
        'admin@condominio.com',
        '$2b$12$bMTHBVJc8wJ2o2qTrvcgDekESfqCQp45qhL26RLTlpuoHNnl75LJ6',
        '(11) 98765-4321',
        'ADMIN',
        true
    ),
    (
        'Marcos Oliveira (Porteiro Diurno)',
        'portaria@condominio.com',
        '$2b$12$AAtVaLmP2JVW0v6lar3tHuqCSEVUre7dm2zOyAa9J2u12XUX2yuyK',
        '(11) 97654-3210',
        'PORTARIA',
        true
    ),
    (
        'Ana Beatriz (Moradora Apto 101)',
        'morador@condominio.com',
        '$2b$12$7dDQPNJgSQYvwQbD.hmOPObSSNteLeb6qf7cUIRMVZ7/MKYFnMZkW',
        '(11) 96543-2109',
        'MORADOR',
        true
    )
ON CONFLICT (email) DO NOTHING;
