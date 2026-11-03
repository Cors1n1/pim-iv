-- ====================================================================
-- CONDOHUB - CARGA DE DADOS COMPLETA (SEED DE HOMOLOGAÇÃO / PRODUÇÃO)
-- Banco de Dados: condominio_db
-- ====================================================================

BEGIN;

-- 1. CONDOMÍNIO PRINCIPAL
INSERT INTO condominios (
    id, nome, slug, cnpj, endereco, telefone, email_contato,
    plano, limite_unidades, status, cor_primaria, cor_secundaria,
    cor_sidebar, cor_fundo, tipo_gestao, administradora_nome, administradora_email
) VALUES (
    1,
    'Residencial Jardins do Sol',
    'jardins-do-sol',
    '12.345.678/0001-90',
    'Av. Paulista, 1500 - Bela Vista, São Paulo - SP',
    '(11) 3254-9000',
    'contato@jardinsdosol.com.br',
    'PRO',
    120,
    'ATIVO',
    '#2563eb',
    '#1d4ed8',
    '#09090b',
    'AUTO',
    'AUTOGESTAO',
    'CondoHub Soluções Imobiliárias',
    'adm@condohub.com.br'
) ON CONFLICT (id) DO UPDATE SET
    nome = EXCLUDED.nome,
    slug = EXCLUDED.slug,
    cnpj = EXCLUDED.cnpj,
    endereco = EXCLUDED.endereco,
    status = 'ATIVO';

-- 2. CONFIGURAÇÕES DO CONDOMÍNIO
INSERT INTO configuracoes_condominio (
    id, condominio_id, nome_condominio, endereco, telefone_portaria,
    email_contato, prazo_retomada_horas, prazo_standby_horas,
    intervalo_padrao_dias, dias_penalidade_queima,
    queima_prioridade_cancelamento, enviar_email_ativo
) VALUES (
    1,
    1,
    'Residencial Jardins do Sol',
    'Av. Paulista, 1500 - Bela Vista, São Paulo - SP',
    '(11) 3254-9001',
    'portaria@jardinsdosol.com.br',
    24,
    48,
    30,
    30,
    true,
    true
) ON CONFLICT (id) DO UPDATE SET
    nome_condominio = EXCLUDED.nome_condominio,
    condominio_id = 1;

-- 3. CONFIGURAÇÕES GERAIS DA PLATAFORMA CONDOHUB
INSERT INTO configuracoes_plataforma (
    id, suporte_email, suporte_telefone, suporte_horario,
    titulo_regularizacao, mensagem_regularizacao,
    titulo_suspensao, subtitulo_suspensao
) VALUES (
    1,
    'suporte@condohub.com.br',
    '(11) 98765-4321',
    'Segunda a Sexta, das 08h às 18h',
    'O que fazer para regularizar?',
    'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.',
    'Acesso ao Condomínio Suspenso',
    'O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.'
) ON CONFLICT (id) DO UPDATE SET
    suporte_email = EXCLUDED.suporte_email;

-- 4. UNIDADES RESIDENCIAIS (CRIADAS INICIALMENTE SEM MORADOR VINCULADO)
INSERT INTO unidades (id, condominio_id, bloco, numero, andar, ativo) VALUES
    (1, 1, 'Bloco A', '101', 1, true),
    (2, 1, 'Bloco A', '102', 1, true),
    (3, 1, 'Bloco A', '201', 2, true),
    (4, 1, 'Bloco A', '202', 2, true),
    (5, 1, 'Bloco B', '101', 1, true),
    (6, 1, 'Bloco B', '102', 1, true),
    (7, 1, 'Bloco B', '201', 2, true),
    (8, 1, 'Bloco B', '202', 2, true)
ON CONFLICT (id) DO UPDATE SET
    bloco = EXCLUDED.bloco,
    numero = EXCLUDED.numero;

-- 5. USUÁRIOS E PERFIS DE ACESSO
-- Senhas criptografadas em BCrypt com salt de 12 rounds:
-- Síndico / Subsíndica: Sindico@2026 ($2b$12$avDJF3E4gkqc64CO1BUTc.ToXZzGOqRVYXN7J5mjwng6L5S4CrBVu)
-- Portaria:             Portaria@2026 ($2b$12$0qkIkqXifBeRDegzD7kYrOz5DBR0b7cRUqzRmHR/gerq9RsWjeOqu)
-- Moradores:            Morador@2026 ($2b$12$WGxDVwPthatTYLWbcK06WuFZU.Tw/kAKJzUNNyd5IudDWD.OIVvTC)

-- Atualiza ou vincula o Superadmin existente ao condomínio 1
UPDATE usuarios 
SET condominio_id = 1 
WHERE email = 'admin@condohub.com.br';

-- Inserção dos usuários administrativos e moradores
INSERT INTO usuarios (
    id, condominio_id, nome, email, senha_hash, telefone,
    tipo_usuario, ativo, precisa_trocar_senha, status_cadastro,
    token_version, cpf, unidade_id
) VALUES 
    (
        2,
        1,
        'Roberto Mendes (Síndico Geral)',
        'sindico@condohub.com.br',
        '$2b$12$avDJF3E4gkqc64CO1BUTc.ToXZzGOqRVYXN7J5mjwng6L5S4CrBVu',
        '(11) 98111-2233',
        'SINDICO',
        true,
        false,
        'ATIVO',
        1,
        '111.222.333-44',
        3 -- Bloco A, Apto 201
    ),
    (
        3,
        1,
        'Mariana Alencar (Subsíndica)',
        'subsindico@condohub.com.br',
        '$2b$12$avDJF3E4gkqc64CO1BUTc.ToXZzGOqRVYXN7J5mjwng6L5S4CrBVu',
        '(11) 98222-3344',
        'SUBSINDICO',
        true,
        false,
        'ATIVO',
        1,
        '222.333.444-55',
        4 -- Bloco A, Apto 202
    ),
    (
        4,
        1,
        'José Carlos (Portaria Principal)',
        'portaria@condohub.com.br',
        '$2b$12$0qkIkqXifBeRDegzD7kYrOz5DBR0b7cRUqzRmHR/gerq9RsWjeOqu',
        '(11) 98333-4455',
        'PORTARIA',
        true,
        false,
        'ATIVO',
        1,
        '333.444.555-66',
        NULL -- Portaria não possui unidade própria
    ),
    (
        5,
        1,
        'Ana Beatriz Santos',
        'morador1@condohub.com.br',
        '$2b$12$WGxDVwPthatTYLWbcK06WuFZU.Tw/kAKJzUNNyd5IudDWD.OIVvTC',
        '(11) 98444-5566',
        'MORADOR',
        true,
        false,
        'ATIVO',
        1,
        '444.555.666-77',
        1 -- Bloco A, Apto 101
    ),
    (
        6,
        1,
        'Carlos Eduardo Lima',
        'morador2@condohub.com.br',
        '$2b$12$WGxDVwPthatTYLWbcK06WuFZU.Tw/kAKJzUNNyd5IudDWD.OIVvTC',
        '(11) 98555-6677',
        'MORADOR',
        true,
        false,
        'ATIVO',
        1,
        '555.666.777-88',
        2 -- Bloco A, Apto 102
    ),
    (
        7,
        1,
        'Fernanda Oliveira Silva',
        'morador3@condohub.com.br',
        '$2b$12$WGxDVwPthatTYLWbcK06WuFZU.Tw/kAKJzUNNyd5IudDWD.OIVvTC',
        '(11) 98666-7788',
        'MORADOR',
        true,
        false,
        'ATIVO',
        1,
        '666.777.888-99',
        5 -- Bloco B, Apto 101
    ),
    (
        8,
        1,
        'Lucas Pinheiro Rocha',
        'morador4@condohub.com.br',
        '$2b$12$WGxDVwPthatTYLWbcK06WuFZU.Tw/kAKJzUNNyd5IudDWD.OIVvTC',
        '(11) 98777-8899',
        'MORADOR',
        true,
        false,
        'ATIVO',
        1,
        '777.888.999-00',
        6 -- Bloco B, Apto 102
    )
ON CONFLICT (email) DO UPDATE SET
    condominio_id = EXCLUDED.condominio_id,
    nome = EXCLUDED.nome,
    senha_hash = EXCLUDED.senha_hash,
    telefone = EXCLUDED.telefone,
    tipo_usuario = EXCLUDED.tipo_usuario,
    ativo = true,
    unidade_id = EXCLUDED.unidade_id;

-- 6. VINCULAÇÃO DOS MORADORES RESPONSÁVEIS ÀS UNIDADES
UPDATE unidades SET morador_responsavel_id = 5 WHERE id = 1; -- Ana Beatriz -> Apto 101 (Bloco A)
UPDATE unidades SET morador_responsavel_id = 6 WHERE id = 2; -- Carlos Eduardo -> Apto 102 (Bloco A)
UPDATE unidades SET morador_responsavel_id = 2 WHERE id = 3; -- Roberto (Síndico) -> Apto 201 (Bloco A)
UPDATE unidades SET morador_responsavel_id = 3 WHERE id = 4; -- Mariana (Subsíndica) -> Apto 202 (Bloco A)
UPDATE unidades SET morador_responsavel_id = 7 WHERE id = 5; -- Fernanda -> Apto 101 (Bloco B)
UPDATE unidades SET morador_responsavel_id = 8 WHERE id = 6; -- Lucas -> Apto 102 (Bloco B)

-- 7. ÁREAS COMUNS DO CONDOMÍNIO
INSERT INTO areas_comuns (
    id, condominio_id, nome, descricao, capacidade_pessoas, taxa_limpeza,
    hora_inicio, hora_fim, duracao_maxima_horas, intervalo_dias_prioridade,
    max_reservas_ativas, prazo_standby_horas, ativo
) VALUES
    (
        1, 1, 'Salão de Festas Nobre',
        'Espaço climatizado completo com cozinha de apoio, churrasqueira integrada, mesas, cadeiras e sistema de som.',
        80, 150.00, '09:00:00', '23:00:00', 8, 30, 2, 48, true
    ),
    (
        2, 1, 'Espaço Gourmet & Churrasqueira',
        'Área ao ar livre com pergolado, churrasqueira a carvão, chopeira e bancada em granito.',
        30, 80.00, '10:00:00', '22:00:00', 6, 20, 2, 48, true
    ),
    (
        3, 1, 'Quadra Poliesportiva',
        'Quadra para prática de futebol society, basquete e vôlei com iluminação em LED.',
        20, 0.00, '08:00:00', '22:00:00', 2, 7, 3, 24, true
    ),
    (
        4, 1, 'Academia & Espaço Fitness',
        'Equipamentos modernos para musculação, esteiras ergométricas e área de alongamento.',
        15, 0.00, '06:00:00', '23:00:00', 2, 7, 3, 24, true
    ),
    (
        5, 1, 'Sala de Coworking & Reuniões',
        'Ambiente silencioso com internet de alta velocidade, mesas individuais e sala de reunião.',
        12, 0.00, '08:00:00', '20:00:00', 4, 15, 2, 24, true
    )
ON CONFLICT (id) DO UPDATE SET
    nome = EXCLUDED.nome,
    capacidade_pessoas = EXCLUDED.capacidade_pessoas,
    taxa_limpeza = EXCLUDED.taxa_limpeza;

-- 8. RESERVAS CONFIRMADAS COM CONVIDADOS
INSERT INTO reservas (
    id, area_comum_id, usuario_id, unidade_id, data_reserva, hora_inicio, hora_fim,
    status, prioridade, prioridade_queimada, observacoes, chave_entregue, chave_devolvida
) VALUES
    (
        1,
        1, -- Salão de Festas Nobre
        5, -- Ana Beatriz (Apto 101)
        1,
        CURRENT_DATE + INTERVAL '5 days',
        '14:00:00',
        '22:00:00',
        'CONFIRMADA',
        'ALTA',
        false,
        'Comemoração de Aniversário Infantil em Família',
        false,
        false
    ),
    (
        2,
        2, -- Espaço Gourmet
        7, -- Fernanda Oliveira (Apto 101 - Bloco B)
        5,
        CURRENT_DATE + INTERVAL '8 days',
        '11:00:00',
        '17:00:00',
        'CONFIRMADA',
        'NORMAL',
        false,
        'Almoço de domingo com familiares',
        false,
        false
    )
ON CONFLICT (id) DO NOTHING;

-- Lista de Convidados da Reserva do Salão de Festas
INSERT INTO convidados_reserva (id, reserva_id, nome_completo, documento, email, convite_enviado, entrada_registrada, saida_registrada) VALUES
    (1, 1, 'Marcos Vinicius Santos', 'MG-18.452.123', 'marcos.santos@email.com', true, false, false),
    (2, 1, 'Camila Rodrigues Alves', 'SP-42.312.987', 'camila.alves@email.com', true, false, false),
    (3, 1, 'Juliana Martins Castro', 'RJ-21.789.654', 'juliana.castro@email.com', true, false, false),
    (4, 1, 'Renato Silva Ferreira', 'SP-33.123.456', 'renato.ferreira@email.com', true, false, false)
ON CONFLICT (id) DO NOTHING;

-- 9. ENCOMENDAS NA PORTARIA
INSERT INTO encomendas (
    id, condominio_id, unidade_id, descricao, codigo_rastreio,
    porteiro_recebedor_id, status, data_chegada, data_retirada, retirado_por
) VALUES
    (
        1,
        1,
        1, -- Apto 101 (Bloco A)
        'Amazon - Pacote Caixa Média (Livros e Eletrônicos)',
        'BR-AMZ-9841238',
        4, -- Porteiro José Carlos
        'AGUARDANDO_RETIRADA',
        NOW() - INTERVAL '3 hours',
        NULL,
        NULL
    ),
    (
        2,
        1,
        2, -- Apto 102 (Bloco A)
        'Mercado Livre - Pacote Pequeno (Cabos e Acessórios)',
        'ML-784125896BR',
        4, -- Porteiro José Carlos
        'AGUARDANDO_RETIRADA',
        NOW() - INTERVAL '1 day',
        NULL,
        NULL
    ),
    (
        3,
        1,
        3, -- Apto 201 (Bloco A - Síndico Roberto)
        'Shopee - Envelope de Documentos',
        'NL-124987123BR',
        4,
        'ENTREGUE',
        NOW() - INTERVAL '2 days',
        NOW() - INTERVAL '1 day',
        'Roberto Mendes'
    )
ON CONFLICT (id) DO NOTHING;

-- 10. AVISOS NO MURAL DO CONDOMÍNIO
INSERT INTO avisos (
    id, condominio_id, titulo, mensagem, categoria, link_anexo, autor_id, ativo
) VALUES
    (
        1,
        1,
        'Manutenção Preventiva dos Elevadores (Blocos A e B)',
        'Informamos que na próxima terça-feira, das 09h às 12h, a empresa Otis realizará manutenção preventiva programada nos elevadores sociais. Os elevadores de serviço funcionarão normalmente.',
        'MANUTENCAO',
        NULL,
        2, -- Síndico Roberto Mendes
        true
    ),
    (
        2,
        1,
        'Convocação de Assembleia Geral Ordinária (AGO)',
        'Ficam convocados todos os senhores condôminos para a AGO anual que debaterá a prestação de contas do exercício anterior e a previsão orçamentária do próximo ano.',
        'ASSEMBLEIA',
        'https://meet.google.com/xyz-condo-hub',
        2,
        true
    ),
    (
        3,
        1,
        'Bem-vindos ao Novo Portal CondoHub!',
        'É com satisfação que inauguramos o CondoHub em nosso condomínio. Por aqui você pode agendar áreas comuns, acompanhar encomendas na portaria, registrar ocorrências e muito mais!',
        'GERAL',
        NULL,
        2,
        true
    ),
    (
        4,
        1,
        'Reforço: Horário de Silêncio após as 22h',
        'Solicitamos a colaboração de todos quanto ao respeito ao horário de silêncio (das 22h às 08h), conforme previsto no Regimento Interno do condomínio.',
        'URGENTE',
        NULL,
        2,
        true
    )
ON CONFLICT (id) DO NOTHING;

-- 11. OCORRÊNCIAS / CHAMADOS DOS MORADORES
INSERT INTO ocorrencias (
    id, condominio_id, unidade_id, usuario_id, titulo, descricao,
    categoria, status, resposta_sindico, respondido_por, respondido_em
) VALUES
    (
        1,
        1,
        1, -- Apto 101
        5, -- Ana Beatriz
        'Lâmpada queimada no corredor do 1º andar',
        'A lâmpada em frente ao apartamento 102 está piscando e falhando há dois dias.',
        'MANUTENCAO',
        'CONCLUIDO',
        'Manutenção realizada e lâmpada tubular substituída pela equipe predial.',
        2, -- Síndico Roberto
        NOW() - INTERVAL '1 day'
    ),
    (
        2,
        1,
        2, -- Apto 102
        6, -- Carlos Eduardo
        'Vazamento leve na torneira do jardim lateral',
        'Notei gotejamento constante na torneira próxima à rampa de acesso dos carros.',
        'VAZAMENTO',
        'EM_ANALISE',
        'Encaminhado para vistoria do zelador no primeiro turno.',
        2,
        NOW() - INTERVAL '4 hours'
    ),
    (
        3,
        1,
        5, -- Apto 101 Bloco B
        7, -- Fernanda Oliveira
        'Sugestão: Instalação de lixeiras de coleta seletiva na garagem',
        'Gostaria de sugerir a disponibilização de lixeiras identificadas para recicláveis no piso G1.',
        'GERAL',
        'ABERTO',
        NULL,
        NULL,
        NULL
    )
ON CONFLICT (id) DO NOTHING;

-- 12. VISITANTES E PRESTADORES DE SERVIÇO
INSERT INTO visitantes (
    id, condominio_id, unidade_id, autorizado_por_id, nome, documento,
    tipo, data_prevista, status, hora_entrada, porteiro_entrada_id, observacoes
) VALUES
    (
        1,
        1,
        1, -- Apto 101
        5, -- Ana Beatriz
        'Carlos Alberto Moreira',
        'MG-12.984.712',
        'VISITANTE',
        CURRENT_DATE,
        'NO_LOCAL',
        NOW() - INTERVAL '45 minutes',
        4, -- Porteiro José Carlos
        'Visita familiar - Acesso liberado à vaga de visitante 02'
    ),
    (
        2,
        1,
        2, -- Apto 102
        6, -- Carlos Eduardo
        'Lucas Rocha (Técnico Vivo Fibra)',
        'SP-38.412.590',
        'PRESTADOR_SERVICO',
        CURRENT_DATE,
        'FINALIZADO',
        NOW() - INTERVAL '3 hours',
        4,
        'Instalação de ponto adicional de internet cabeada'
    ),
    (
        3,
        1,
        3, -- Apto 201
        2, -- Síndico Roberto
        'Mariana Souza',
        'SP-44.123.889',
        'VISITANTE',
        CURRENT_DATE,
        'AGUARDANDO',
        NULL,
        NULL,
        'Aguardando chegada para almoço'
    )
ON CONFLICT (id) DO NOTHING;

-- 13. AJUSTE DE SEQUÊNCIAS DO POSTGRESQL (PREVINE ERRO DE DUPLICATE KEY EM NOVOS CADASTROS)
SELECT setval(pg_get_serial_sequence('condominios', 'id'), COALESCE(MAX(id), 1)) FROM condominios;
SELECT setval(pg_get_serial_sequence('configuracoes_condominio', 'id'), COALESCE(MAX(id), 1)) FROM configuracoes_condominio;
SELECT setval(pg_get_serial_sequence('configuracoes_plataforma', 'id'), COALESCE(MAX(id), 1)) FROM configuracoes_plataforma;
SELECT setval(pg_get_serial_sequence('unidades', 'id'), COALESCE(MAX(id), 1)) FROM unidades;
SELECT setval(pg_get_serial_sequence('usuarios', 'id'), COALESCE(MAX(id), 1)) FROM usuarios;
SELECT setval(pg_get_serial_sequence('areas_comuns', 'id'), COALESCE(MAX(id), 1)) FROM areas_comuns;
SELECT setval(pg_get_serial_sequence('reservas', 'id'), COALESCE(MAX(id), 1)) FROM reservas;
SELECT setval(pg_get_serial_sequence('convidados_reserva', 'id'), COALESCE(MAX(id), 1)) FROM convidados_reserva;
SELECT setval(pg_get_serial_sequence('encomendas', 'id'), COALESCE(MAX(id), 1)) FROM encomendas;
SELECT setval(pg_get_serial_sequence('avisos', 'id'), COALESCE(MAX(id), 1)) FROM avisos;
SELECT setval(pg_get_serial_sequence('ocorrencias', 'id'), COALESCE(MAX(id), 1)) FROM ocorrencias;
SELECT setval(pg_get_serial_sequence('visitantes', 'id'), COALESCE(MAX(id), 1)) FROM visitantes;

COMMIT;
