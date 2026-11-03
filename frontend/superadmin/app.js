/**
 * CONDOHUB MASTER — CLIENT-SIDE APP DO SUPERADMIN SAAS
 */

const API_BASE = '/api/superadmin';
let currentToken = localStorage.getItem('superadmin_token');

// Elementos DOM
const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const formSuperLogin = document.getElementById('formSuperLogin');
const loginError = document.getElementById('loginError');
const btnLogout = document.getElementById('btnLogout');
const btnRefresh = document.getElementById('btnRefresh');

const metricCondosAtivos = document.getElementById('metricCondosAtivos');
const metricCondosTotal = document.getElementById('metricCondosTotal');
const metricTotalUnidades = document.getElementById('metricTotalUnidades');
const metricTotalMoradores = document.getElementById('metricTotalMoradores');
const metricMrr = document.getElementById('metricMrr');
const metricEventos = document.getElementById('metricEventos');
const condosTableBody = document.getElementById('condosTableBody');

const modalNewCondo = document.getElementById('modalNewCondo');
const btnOpenNewCondo = document.getElementById('btnOpenNewCondo');
const btnCloseModalNewCondo = document.getElementById('btnCloseModalNewCondo');
const btnCancelNewCondo = document.getElementById('btnCancelNewCondo');
const formCreateCondo = document.getElementById('formCreateCondo');

const newCondoCorPrimaria = document.getElementById('newCondoCorPrimaria');
const labelCorPrimaria = document.getElementById('labelCorPrimaria');
const newCondoCorSecundaria = document.getElementById('newCondoCorSecundaria');
const labelCorSecundaria = document.getElementById('labelCorSecundaria');

// Sincronização dos pickers de cores
if (newCondoCorPrimaria && labelCorPrimaria) {
  newCondoCorPrimaria.addEventListener('input', (e) => {
    labelCorPrimaria.textContent = e.target.value;
  });
}
if (newCondoCorSecundaria && labelCorSecundaria) {
  newCondoCorSecundaria.addEventListener('input', (e) => {
    labelCorSecundaria.textContent = e.target.value;
  });
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
  if (currentToken) {
    showDashboard();
  } else {
    showLogin();
  }
});

// Toast notification
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Controle de Telas
function showLogin() {
  loginView.classList.remove('hidden');
  dashboardView.classList.add('hidden');
}

function showDashboard() {
  loginView.classList.add('hidden');
  dashboardView.classList.remove('hidden');
  loadMetrics();
  loadCondominios();
}

// Submissão do Login SuperAdmin
formSuperLogin.addEventListener('submit', async (e) => {
  e.preventDefault();
  loginError.classList.add('hidden');
  loginError.textContent = '';

  const email = document.getElementById('superEmail').value.trim();
  const senha = document.getElementById('superPassword').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Falha na autenticação do SuperAdmin.');
    }

    const data = await res.json();
    currentToken = data.access_token;
    localStorage.setItem('superadmin_token', currentToken);
    showToast('Acesso concedido com sucesso.', 'success');
    showDashboard();
  } catch (err) {
    loginError.textContent = err.message;
    loginError.classList.remove('hidden');
  }
});

// Logout
btnLogout.addEventListener('click', () => {
  localStorage.removeItem('superadmin_token');
  currentToken = null;
  showLogin();
  showToast('Sessão encerrada com segurança.');
});

// Atualizar
btnRefresh.addEventListener('click', () => {
  loadMetrics();
  loadCondominios();
  showToast('Dados atualizados.', 'info');
});

// Requisição com Bearer Token
async function fetchAdmin(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${currentToken}`,
    ...(options.headers || {})
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (res.status === 401 || res.status === 403) {
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      localStorage.removeItem('superadmin_token');
      currentToken = null;
      showLogin();
      showToast('Sessão expirada. Faça login novamente.', 'error');
    }
    throw new Error(data.detail || 'Não autorizado.');
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Erro na requisição (${res.status})`);
  }

  return res.json();
}

// Carregar Métricas Executivas
async function loadMetrics() {
  try {
    const m = await fetchAdmin('/metrics');
    metricCondosAtivos.textContent = m.condominios_ativos || 0;
    metricCondosTotal.textContent = `${m.total_condominios || 0} cadastrados no total (${m.condominios_bloqueados || 0} bloqueados)`;
    metricTotalUnidades.textContent = m.total_unidades || 0;
    metricTotalMoradores.textContent = `${m.total_usuarios || 0} usuários na base`;
    
    // Formata faturamento
    const mrr = Number(m.faturamento_mensal_estimado || 0);
    metricMrr.textContent = mrr.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    metricEventos.textContent = (m.total_reservas || 0) + (m.total_ocorrencias || 0);
  } catch (err) {
    console.error('Erro ao carregar métricas:', err);
  }
}

// Carregar Tabela de Condomínios
async function loadCondominios() {
  condosTableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4">Carregando lista de condomínios...</td></tr>`;
  try {
    const condos = await fetchAdmin('/condominios');
    if (!condos || condos.length === 0) {
      condosTableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4">Nenhum condomínio cadastrado ainda.</td></tr>`;
      return;
    }

    condosTableBody.innerHTML = condos.map(c => {
      const isAtivo = c.status === 'ATIVO';
      const statusBadge = isAtivo
        ? `<span class="badge-status ativo">● Ativo</span>`
        : `<span class="badge-status bloqueado">● Bloqueado</span>`;

      const planClass = c.plano.toLowerCase();
      const planBadge = `<span class="badge-plan ${planClass}">${c.plano}</span>`;

      const colorIndicator = `
        <div class="color-swatch-duo" title="Primária: ${c.cor_primaria} | Secundária: ${c.cor_secundaria}">
          <span class="color-dot" style="background-color: ${c.cor_primaria};"></span>
          <span class="color-dot" style="background-color: ${c.cor_secundaria};"></span>
        </div>
      `;

      const toggleActionBtn = isAtivo
        ? `<button type="button" class="btn-action block" onclick="toggleStatus(${c.id}, 'BLOQUEADO', '${c.nome}')" title="Suspender temporariamente o acesso do condomínio">
             <svg class="ico"><use href="#i-lock"/></svg> Suspender
           </button>`
        : `<button type="button" class="btn-action unblock" onclick="toggleStatus(${c.id}, 'ATIVO', '${c.nome}')" title="Reativar acesso do condomínio">
             <svg class="ico"><use href="#i-unlock"/></svg> Liberar
           </button>`;

      return `
        <tr>
          <td><strong>#${c.id}</strong></td>
          <td>
            <strong>${c.nome}</strong><br />
            <small class="muted-sm">${c.email_contato || 'Sem e-mail cadastrado'}</small>
          </td>
          <td>
            <span>${c.cnpj || 'CNPJ não informado'}</span><br />
            <small class="muted-sm">${c.endereco || ''}</small>
          </td>
          <td>${planBadge}</td>
          <td>
            <strong>${c.total_unidades}</strong> / ${c.limite_unidades} un.<br />
            <small class="muted-sm">${c.total_moradores} moradores</small>
          </td>
          <td>${colorIndicator}</td>
          <td>${statusBadge}</td>
          <td class="text-right">
            <div class="table-actions">
              <button type="button" class="btn-action impersonate" onclick="impersonateCondo(${c.id}, '${c.nome}')" title="Acessar painel do condomínio em modo auditoria">
                <svg class="ico"><use href="#i-external"/></svg> Abrir Painel
              </button>
              ${toggleActionBtn}
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    condosTableBody.innerHTML = `<tr><td colspan="8" class="text-center py-4" style="color: var(--rose);">Erro ao carregar condomínios: ${err.message}</td></tr>`;
  }
}

// Suspender ou Liberar Acesso do Condomínio
window.toggleStatus = async function(condoId, newStatus, condoNome) {
  const isBlocking = newStatus === 'BLOQUEADO';
  const confirmMsg = isBlocking
    ? `Deseja realmente SUSPENDER o acesso do condomínio "${condoNome}"? O login de todos os moradores e funcionários será temporariamente pausado.`
    : `Deseja LIBERAR o acesso do condomínio "${condoNome}"?`;

  if (!confirm(confirmMsg)) return;

  try {
    await fetchAdmin(`/condominios/${condoId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus })
    });
    showToast(`Situação do condomínio atualizada para ${newStatus === 'ATIVO' ? 'Liberado' : 'Suspenso'}.`, 'success');
    loadMetrics();
    loadCondominios();
  } catch (err) {
    showToast(`Erro ao atualizar situação: ${err.message}`, 'error');
  }
};

// Impersonation: Entrar como Suporte Técnico no Condomínio
window.impersonateCondo = async function(condoId, condoNome, condoSlug) {
  const newTab = window.open('about:blank', '_blank');
  try {
    const data = await fetchAdmin(`/condominios/${condoId}/impersonate`, {
      method: 'POST'
    });

    // Salva o token oficial de sessão lido pelo frontend principal (app.js)
    localStorage.setItem('sgc_token', data.access_token);
    localStorage.setItem('sgc_user', JSON.stringify(data.user));
    if (condoSlug) {
      localStorage.setItem('sgc_condo_slug', condoSlug);
    }
    showToast(`Iniciando sessão de suporte em "${condoNome}"...`, 'success');
    
    const targetUrl = `${condoSlug ? `/c/${condoSlug}/` : `/?condo=${condoId}`}?impersonate_token=${encodeURIComponent(data.access_token)}`;
    if (newTab && !newTab.closed) {
      newTab.location.href = targetUrl;
    } else {
      window.location.href = targetUrl;
    }
  } catch (err) {
    if (newTab && !newTab.closed) {
      newTab.close();
    }
    showToast(`Erro ao entrar como suporte: ${err.message}`, 'error');
  }
};

// Modais
btnOpenNewCondo.addEventListener('click', () => {
  formCreateCondo.reset();
  modalNewCondo.classList.remove('hidden');
});

btnCloseModalNewCondo.addEventListener('click', () => {
  modalNewCondo.classList.add('hidden');
});

btnCancelNewCondo.addEventListener('click', () => {
  modalNewCondo.classList.add('hidden');
});

// Cadastrar Novo Condomínio
formCreateCondo.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    nome: document.getElementById('newCondoNome').value.trim(),
    cnpj: document.getElementById('newCondoCnpj').value.trim() || null,
    endereco: document.getElementById('newCondoEndereco').value.trim() || null,
    telefone: document.getElementById('newCondoTelefone').value.trim() || null,
    plano: document.getElementById('newCondoPlano').value,
    limite_unidades: parseInt(document.getElementById('newCondoLimite').value, 10),
    cor_primaria: document.getElementById('newCondoCorPrimaria').value,
    cor_secundaria: document.getElementById('newCondoCorSecundaria').value,
    sindico_nome: document.getElementById('newSindicoNome').value.trim() || null,
    sindico_email: document.getElementById('newSindicoEmail').value.trim() || null,
    sindico_senha: document.getElementById('newSindicoSenha').value || null
  };

  try {
    await fetchAdmin('/condominios', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    modalNewCondo.classList.add('hidden');
    showToast(`Condomínio "${payload.nome}" cadastrado com sucesso!`, 'success');
    loadMetrics();
    loadCondominios();
  } catch (err) {
    alert(`Erro ao cadastrar condomínio: ${err.message}`);
  }
});
