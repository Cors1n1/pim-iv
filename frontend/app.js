/* ====================================================================
   SISTEMA DE GESTÃO DE CONDOMÍNIO (SGC) - RESIDENCIAL BELA VISTA
   Lógica do frontend: autenticação, controle de acesso por perfil (RBAC),
   privacidade (LGPD) e módulos operacionais corporativos.
   ==================================================================== */

const API_BASE_URL = window.location.origin.startsWith("http") ? "" : "http://localhost:8000";

// ==========================================
// 0. UTILITÁRIOS
// ==========================================
const $ = (id) => document.getElementById(id);

const icon = (name, cls = "ico ico-sm") =>
  `<svg class="${cls}" aria-hidden="true"><use href="#i-${name}"/></svg>`;

/** Escapa dados vindos do servidor antes de injetar no DOM (prevenção de XSS). */
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function getStoredUser() {
  try {
    const raw = localStorage.getItem("sgc_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const isAdminRole = (user) => !!user && (user.tipo_usuario === "ADMIN" || user.tipo_usuario === "SINDICO");

/** Notificação não bloqueante (substitui alert) - com animações suaves e ícones SVG. */
function showToast(message, type = "info") {
  const region = $("toastRegion");
  if (!region) return;
  const iconName = type === "error" ? "close" : (type === "success" ? "check" : "shield");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.setAttribute("role", type === "error" ? "alert" : "status");
  toast.innerHTML = `${icon(iconName, "ico")}<span>${escapeHtml(message)}</span>`;
  region.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("leaving");
    setTimeout(() => toast.remove(), 260);
  }, 4200);
}

/**
 * Diálogo modal assíncrono para confirmação (substitui confirm do navegador).
 * @param {Object} options
 * @param {string} options.title - Título do diálogo
 * @param {string} options.message - Texto explicativo
 * @param {string} [options.confirmText="Confirmar"] - Rótulo do botão principal
 * @param {string} [options.cancelText="Cancelar"] - Rótulo do botão secundário
 * @param {boolean} [options.isDanger=false] - Estilo de perigo (vermelho)
 * @param {string} [options.iconName="shield"] - Nome do ícone SVG
 * @returns {Promise<boolean>}
 */
function showCustomConfirm({
  title = "Confirmação",
  message = "",
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  isDanger = false,
  iconName = isDanger ? "trash" : "shield"
} = {}) {
  return new Promise((resolve) => {
    const overlay = $("customDialogOverlay");
    const iconEl = $("dialogIcon");
    const titleEl = $("dialogTitle");
    const messageEl = $("dialogMessage");
    const inputWrapper = $("dialogInputWrapper");
    const btnConfirm = $("btnDialogConfirm");
    const btnCancel = $("btnDialogCancel");
    const btnCloseX = $("btnDialogCloseX");

    if (!overlay) {
      resolve(confirm(message));
      return;
    }

    titleEl.textContent = title;
    messageEl.textContent = message;
    inputWrapper.classList.add("hidden");

    iconEl.className = `custom-dialog-icon ${isDanger ? "danger" : ""}`;
    iconEl.innerHTML = icon(iconName, "ico");

    btnConfirm.textContent = confirmText;
    btnConfirm.className = `btn-dialog-primary ${isDanger ? "danger" : ""}`;
    btnCancel.textContent = cancelText;

    overlay.classList.remove("hidden");
    document.body.classList.add("modal-open");
    btnConfirm.focus();

    function cleanup(result) {
      window.removeEventListener("keydown", onKeyDown);
      overlay.removeEventListener("click", onBackdropClick);
      btnConfirm.removeEventListener("click", onConfirm);
      btnCancel.removeEventListener("click", onCancel);
      btnCloseX.removeEventListener("click", onCancel);
      overlay.classList.add("hidden");
      document.body.classList.remove("modal-open");
      resolve(result);
    }

    function onConfirm() { cleanup(true); }
    function onCancel() { cleanup(false); }
    function onBackdropClick(e) {
      if (e.target === overlay) cleanup(false);
    }
    function onKeyDown(e) {
      if (e.key === "Escape") cleanup(false);
      else if (e.key === "Enter") {
        e.preventDefault();
        cleanup(true);
      }
    }

    btnConfirm.addEventListener("click", onConfirm);
    btnCancel.addEventListener("click", onCancel);
    btnCloseX.addEventListener("click", onCancel);
    overlay.addEventListener("click", onBackdropClick);
    window.addEventListener("keydown", onKeyDown);
  });
}

/**
 * Diálogo modal assíncrono para entrada de texto (substitui prompt do navegador).
 * @param {Object} options
 * @param {string} options.title - Título do diálogo
 * @param {string} options.message - Texto explicativo
 * @param {string} [options.label="Informe o dado:"] - Rótulo do campo
 * @param {string} [options.placeholder=""] - Placeholder
 * @param {string} [options.defaultValue=""] - Valor inicial
 * @param {string} [options.confirmText="Confirmar"] - Rótulo do botão principal
 * @param {string} [options.cancelText="Cancelar"] - Rótulo do botão secundário
 * @param {string} [options.iconName="clipboard"] - Nome do ícone SVG
 * @returns {Promise<string|null>}
 */
function showCustomPrompt({
  title = "Solicitação de Informação",
  message = "",
  label = "Informe o dado:",
  placeholder = "Digite aqui...",
  defaultValue = "",
  confirmText = "Confirmar",
  cancelText = "Cancelar",
  iconName = "clipboard"
} = {}) {
  return new Promise((resolve) => {
    const overlay = $("customDialogOverlay");
    const iconEl = $("dialogIcon");
    const titleEl = $("dialogTitle");
    const messageEl = $("dialogMessage");
    const inputWrapper = $("dialogInputWrapper");
    const inputLabel = $("dialogInputLabel");
    const inputEl = $("dialogInput");
    const btnConfirm = $("btnDialogConfirm");
    const btnCancel = $("btnDialogCancel");
    const btnCloseX = $("btnDialogCloseX");

    if (!overlay) {
      resolve(prompt(message, defaultValue));
      return;
    }

    titleEl.textContent = title;
    messageEl.textContent = message;
    inputLabel.textContent = label;
    inputEl.placeholder = placeholder;
    inputEl.value = defaultValue;
    inputWrapper.classList.remove("hidden");

    iconEl.className = "custom-dialog-icon";
    iconEl.innerHTML = icon(iconName, "ico");

    btnConfirm.textContent = confirmText;
    btnConfirm.className = "btn-dialog-primary";
    btnCancel.textContent = cancelText;

    overlay.classList.remove("hidden");
    document.body.classList.add("modal-open");
    setTimeout(() => {
      inputEl.focus();
      inputEl.select();
    }, 50);

    function cleanup(result) {
      window.removeEventListener("keydown", onKeyDown);
      overlay.removeEventListener("click", onBackdropClick);
      btnConfirm.removeEventListener("click", onConfirm);
      btnCancel.removeEventListener("click", onCancel);
      btnCloseX.removeEventListener("click", onCancel);
      overlay.classList.add("hidden");
      document.body.classList.remove("modal-open");
      resolve(result);
    }

    function onConfirm() { cleanup(inputEl.value); }
    function onCancel() { cleanup(null); }
    function onBackdropClick(e) {
      if (e.target === overlay) cleanup(null);
    }
    function onKeyDown(e) {
      if (e.key === "Escape") cleanup(null);
      else if (e.key === "Enter") {
        e.preventDefault();
        cleanup(inputEl.value);
      }
    }

    btnConfirm.addEventListener("click", onConfirm);
    btnCancel.addEventListener("click", onCancel);
    btnCloseX.addEventListener("click", onCancel);
    overlay.addEventListener("click", onBackdropClick);
    window.addEventListener("keydown", onKeyDown);
  });
}

/** Converte o campo "detail" da API (string ou lista de validação) em texto legível. */
function formatApiDetail(detail) {
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || "Dado inválido").join("; ");
  }
  return typeof detail === "string" ? detail : "Erro ao processar a requisição.";
}

/** Cliente HTTP autenticado. Encerra a sessão automaticamente em caso de 401. */
async function api(path, { method = "GET", body } = {}) {
  const token = localStorage.getItem("sgc_token");
  const headers = { Authorization: `Bearer ${token}` };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (response.status === 401) {
    logout("Sua sessão expirou. Entre novamente.");
    throw new Error("Sessão expirada.");
  }
  if (!response.ok) {
    throw new Error(formatApiDetail(data && data.detail));
  }
  return data;
}

// ==========================================
// 1. ELEMENTOS PRINCIPAIS
// ==========================================
const loginSection = $("loginSection");
const dashboardSection = $("dashboardSection");
const loginForm = $("loginForm");
const inputEmail = $("inputEmail");
const inputPassword = $("inputPassword");
const togglePassword = $("togglePassword");
const btnLogin = $("btnLogin");
const alertBox = $("alertBox");
const btnLogout = $("btnLogout");
const userNameEl = $("userName");
const userRoleBadgeEl = $("userRoleBadge");
const userAvatarEl = $("userAvatar");
const btnContrast = $("btnContrast");
const btnTextSize = $("btnTextSize");

// ==========================================
// 2. INICIALIZAÇÃO E SESSÃO
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  loadCondoSettings();
  checkExistingSession();
  setupEventListeners();
  setupMobileDrawer();
  enableTableSorting();
});

function checkExistingSession() {
  const token = localStorage.getItem("sgc_token");
  const user = getStoredUser();
  if (token && user) {
    showDashboard(user);
  } else {
    document.body.classList.remove("is-logged-in");
    localStorage.removeItem("sgc_token");
    localStorage.removeItem("sgc_user");
  }
}

function logout(message) {
  localStorage.removeItem("sgc_token");
  localStorage.removeItem("sgc_user");
  dashboardSection.classList.add("hidden");
  loginSection.classList.remove("hidden");
  document.body.classList.remove("is-logged-in");
  const mobileNav = $("mobileBottomNav");
  if (mobileNav) mobileNav.classList.add("hidden");
  closeMobileDrawer();
  inputPassword.value = "";
  if (message) showAlert(message, "success");
}

const FONT_LEVEL_NAMES = ["Normal", "Grande", "Maior", "Máxima"];

/** Tema escuro, alto contraste e tamanho da letra (4 níveis), com memória entre visitas. */
function setupAccessibilityPrefs() {
  let prefs = { dark: false, contrast: false, font: 0 };
  try {
    prefs = { ...prefs, ...JSON.parse(localStorage.getItem("sgc_prefs") || "{}") };
  } catch { /* preferências corrompidas: usa o padrão */ }
  prefs.font = Math.min(Math.max(Number(prefs.font) || 0, 0), FONT_LEVEL_NAMES.length - 1);

  const btnDark = $("btnDarkMode");
  const btnFontDown = $("btnFontDown");

  const apply = () => {
    document.body.classList.toggle("dark-mode", prefs.dark);
    document.body.classList.toggle("high-contrast", prefs.contrast);
    FONT_LEVEL_NAMES.forEach((_, i) => document.documentElement.classList.toggle(`fs-${i}`, i === prefs.font && i > 0));
    btnDark.setAttribute("aria-pressed", String(prefs.dark));
    btnContrast.setAttribute("aria-pressed", String(prefs.contrast));
    $("darkModeLabel").textContent = prefs.dark ? "Tema escuro: ligado" : "Tema escuro";
    $("contrastLabel").textContent = prefs.contrast ? "Alto contraste: ligado" : "Alto contraste";
    $("fontLevelLabel").textContent = FONT_LEVEL_NAMES[prefs.font];
    btnFontDown.disabled = prefs.font === 0;
    btnTextSize.disabled = prefs.font === FONT_LEVEL_NAMES.length - 1;
    localStorage.setItem("sgc_prefs", JSON.stringify(prefs));
  };

  btnDark.addEventListener("click", () => { prefs.dark = !prefs.dark; apply(); });
  btnContrast.addEventListener("click", () => { prefs.contrast = !prefs.contrast; apply(); });
  btnTextSize.addEventListener("click", () => { prefs.font = Math.min(prefs.font + 1, FONT_LEVEL_NAMES.length - 1); apply(); });
  btnFontDown.addEventListener("click", () => { prefs.font = Math.max(prefs.font - 1, 0); apply(); });
  apply();
}

function setupEventListeners() {
  loginForm.addEventListener("submit", handleLoginSubmit);

  togglePassword.addEventListener("click", () => {
    const reveal = inputPassword.type === "password";
    inputPassword.type = reveal ? "text" : "password";
    togglePassword.innerHTML = icon(reveal ? "eye-off" : "eye", "ico");
  });

  const capsLockWarning = $("capsLockWarning");
  if (capsLockWarning && inputPassword) {
    const handleCaps = (e) => {
      if (e.getModifierState) {
        const isCaps = e.getModifierState("CapsLock");
        capsLockWarning.classList.toggle("hidden", !isCaps);
      }
    };
    inputPassword.addEventListener("keydown", handleCaps);
    inputPassword.addEventListener("keyup", handleCaps);
    inputPassword.addEventListener("blur", () => {
      capsLockWarning.classList.add("hidden");
    });
  }

  document.querySelectorAll(".btn-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".btn-chip").forEach((b) => b.classList.remove("active-profile"));
      btn.classList.add("active-profile");
      inputEmail.value = btn.dataset.email;
      inputPassword.value = btn.dataset.pass;
      hideAlert();
    });
  });

  btnLogout.addEventListener("click", () => logout("Sessão finalizada com sucesso."));

  setupAccessibilityPrefs();

  // Navegação entre janelas (menu lateral e cards)
  document.querySelectorAll("[data-window]").forEach((el) => {
    el.addEventListener("click", () => {
      const win = el.dataset.window;
      if (win) navigateToWindow(win);
    });
  });

  // Botões de voltar à Visão geral nas janelas
  document.querySelectorAll("[data-window-back]").forEach((btn) => {
    btn.addEventListener("click", () => navigateToWindow("windowOverview"));
  });

  // Tecla Escape para voltar ao painel inicial caso esteja em outra janela
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && currentActiveWindow !== "windowOverview") {
      const user = getStoredUser();
      if (!user || !user.precisa_trocar_senha) {
        navigateToWindow("windowOverview");
      }
    }
  });

  // Listener para troca obrigatória de senha no primeiro login
  const formForcePw = $("formForceChangePassword");
  if (formForcePw) {
    formForcePw.addEventListener("submit", handleForceChangePasswordSubmit);
  }
  const btnForceLogout = $("btnForcePwLogout");
  if (btnForceLogout) {
    btnForceLogout.addEventListener("click", () => {
      closeForceChangePasswordModal();
      logout("Sessão finalizada. Entre com sua senha temporária para redefini-la.");
    });
  }

  // Formulário de Configurações do Condomínio (Síndico)
  const formSettings = $("formCondoSettings");
  if (formSettings) {
    formSettings.addEventListener("submit", handleSaveCondoSettings);
  }
  const btnCancelSettings = $("btnCancelCondoSettings");
  if (btnCancelSettings) {
    btnCancelSettings.addEventListener("click", () => {
      loadCondoSettingsForm();
      showToast("Configurações restauradas para os valores salvos no servidor.", "info");
    });
  }

  // Modal de Convidados da Reserva
  const btnCloseGuestsX = $("btnGuestsCloseX");
  const btnCloseGuests = $("btnCloseGuestsModal");
  const modalGuests = $("modalGuestsList");
  const closeGuests = () => {
    if (modalGuests) modalGuests.classList.add("hidden");
    document.body.classList.remove("modal-open");
  };
  if (btnCloseGuestsX) btnCloseGuestsX.addEventListener("click", closeGuests);
  if (btnCloseGuests) btnCloseGuests.addEventListener("click", closeGuests);
  if (modalGuests) {
    modalGuests.addEventListener("click", (e) => {
      if (e.target === modalGuests) closeGuests();
    });
  }

  const formAddGuest = $("formAddGuest");
  if (formAddGuest) {
    formAddGuest.addEventListener("submit", handleAddGuestSubmit);
  }

  const btnRefreshTodayGuests = $("btnRefreshTodayGuests");
  if (btnRefreshTodayGuests) {
    btnRefreshTodayGuests.addEventListener("click", loadTodayGuests);
  }
}

// ==========================================
// 3. JANELAS E NAVEGAÇÃO DO WORKSPACE
// ==========================================
const ALL_WINDOWS = [
  "windowOverview",
  "windowUnits",
  "windowDeliveries",
  "windowReservations",
  "windowNotices",
  "windowTickets",
  "windowVisitors",
  "windowAudit",
  "windowSettings",
];

let currentActiveWindow = "windowOverview";

function navigateToWindow(targetWindowId) {
  const user = getStoredUser();

  // Bloqueio mandatário se o usuário precisar trocar de senha no primeiro login
  if (user && user.precisa_trocar_senha) {
    openForceChangePasswordModal();
    return;
  }

  // Proteção de rotas do lado do cliente (RBAC + LGPD)
  if (targetWindowId === "windowUnits" && (!user || !isAdminRole(user))) {
    showToast("Acesso restrito: o cadastro de apartamentos e moradores é exclusivo do síndico (LGPD).", "error");
    return;
  }
  if (targetWindowId === "windowAudit" && (!user || !isAdminRole(user))) {
    showToast("Acesso restrito: a auditoria de segurança é exclusiva do síndico.", "error");
    return;
  }
  if (targetWindowId === "windowSettings" && (!user || !isAdminRole(user))) {
    showToast("Acesso restrito: as configurações do condomínio são exclusivas do síndico.", "error");
    return;
  }

  // Alterna a exibição das janelas reais
  ALL_WINDOWS.forEach((winId) => {
    const el = $(winId);
    if (el) el.classList.toggle("hidden", winId !== targetWindowId);
  });
  currentActiveWindow = targetWindowId;

  // Atualiza destaque na barra lateral
  document.querySelectorAll(".nav-item").forEach((item) => {
    const isTarget = item.dataset.window === targetWindowId || (targetWindowId === "windowOverview" && item.id === "navHome");
    item.classList.toggle("active", isTarget);
  });

  // Atualiza destaque na barra de navegação móvel
  document.querySelectorAll(".m-nav-btn").forEach((item) => {
    const isTarget = item.dataset.window === targetWindowId;
    item.classList.toggle("active", isTarget);
  });

  closeMobileDrawer();

  // Carrega os dados sob demanda para a janela aberta
  switch (targetWindowId) {
    case "windowUnits":
      loadUnits();
      break;
    case "windowDeliveries":
      loadDeliveries();
      break;
    case "windowReservations":
      loadReservations();
      break;
    case "windowNotices":
      loadNotices();
      break;
    case "windowTickets":
      loadTickets();
      break;
    case "windowVisitors":
      loadVisitors();
      loadTodayGuests();
      break;
    case "windowAudit":
      loadAuditLogs();
      break;
    case "windowSettings":
      loadCondoSettingsForm();
      loadAreasManagementList();
      break;
    case "windowOverview":
    default:
      if (user) loadQuickStatsForRole(user);
      break;
  }

  setTimeout(enableTableSorting, 350);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ==========================================
// 4. LOGIN
// ==========================================
async function handleLoginSubmit(e) {
  e.preventDefault();
  hideAlert();

  const email = inputEmail.value.trim();
  const senha = inputPassword.value;

  if (!email || !senha) {
    showAlert("Por favor, preencha todos os campos.", "error");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, senha }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(formatApiDetail(data.detail) || "Erro ao conectar com o servidor.");
    }

    localStorage.setItem("sgc_token", data.access_token);
    localStorage.setItem("sgc_user", JSON.stringify(data.user));

    showAlert("Login realizado com sucesso. Redirecionando...", "success");
    setTimeout(() => showDashboard(data.user), 500);
  } catch (err) {
    showAlert(err.message, "error");
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  const btnText = btnLogin.querySelector(".btn-text");
  const spinner = btnLogin.querySelector(".spinner");
  btnLogin.disabled = isLoading;
  btnText.textContent = isLoading ? "Validando credenciais..." : "Entrar no portal";
  spinner.classList.toggle("hidden", !isLoading);
}

function showAlert(message, type) {
  alertBox.textContent = message;
  alertBox.className = `alert-box ${type}`;
}

function hideAlert() {
  alertBox.classList.add("hidden");
}

// ==========================================
// 4.1 TROCA OBRIGATÓRIA DE SENHA (PRIMEIRO ACESSO)
// ==========================================
function openForceChangePasswordModal() {
  const modal = $("modalForceChangePassword");
  if (!modal) return;
  modal.classList.remove("hidden");
  document.body.classList.add("modal-open");
  $("inputForcePwCurrent").value = "";
  $("inputForcePwNew").value = "";
  $("inputForcePwConfirm").value = "";
  const errBox = $("forcePwError");
  if (errBox) {
    errBox.classList.add("hidden");
    errBox.textContent = "";
  }
  setTimeout(() => $("inputForcePwCurrent").focus(), 120);
}

function closeForceChangePasswordModal() {
  const modal = $("modalForceChangePassword");
  if (modal) modal.classList.add("hidden");
  document.body.classList.remove("modal-open");
}

async function handleForceChangePasswordSubmit(e) {
  e.preventDefault();
  const senhaAtual = $("inputForcePwCurrent").value;
  const novaSenha = $("inputForcePwNew").value;
  const confirmacao = $("inputForcePwConfirm").value;
  const errBox = $("forcePwError");
  const btnSubmit = $("btnForcePwSubmit");

  if (!senhaAtual || !novaSenha || !confirmacao) {
    errBox.textContent = "Preencha todos os campos obrigatórios.";
    errBox.classList.remove("hidden");
    return;
  }

  if (novaSenha !== confirmacao) {
    errBox.textContent = "A nova senha e a confirmação de senha não coincidem.";
    errBox.classList.remove("hidden");
    return;
  }

  if (novaSenha.length < 6) {
    errBox.textContent = "A nova senha deve ter no mínimo 6 caracteres.";
    errBox.classList.remove("hidden");
    return;
  }

  btnSubmit.disabled = true;
  btnSubmit.textContent = "Gravando nova senha...";
  try {
    const updatedUser = await api("/api/auth/change-password", {
      method: "POST",
      body: {
        senha_atual: senhaAtual,
        nova_senha: novaSenha,
        confirmacao_senha: confirmacao,
      },
    });

    localStorage.setItem("sgc_user", JSON.stringify(updatedUser));
    closeForceChangePasswordModal();
    showToast("Senha alterada com sucesso! Seu acesso ao sistema foi liberado.", "success");
    showDashboard(updatedUser);
  } catch (err) {
    errBox.textContent = err.message;
    errBox.classList.remove("hidden");
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.textContent = "Gravar Nova Senha";
  }
}

// ==========================================
// 5. DASHBOARD E CONTROLE DE ACESSO (RBAC + LGPD)
// ==========================================
function showDashboard(user) {
  userNameEl.textContent = user.nome;
  userRoleBadgeEl.textContent = user.tipo_usuario;
  userAvatarEl.textContent = user.nome.charAt(0).toUpperCase();

  const pageDate = $("pageDate");
  if (pageDate) {
    pageDate.textContent = new Date().toLocaleDateString("pt-BR", {
      weekday: "long", day: "numeric", month: "long", year: "numeric",
    });
  }

  applyRoleBasedAccess(user);
  hideAlert();
  loginSection.classList.add("hidden");
  dashboardSection.classList.remove("hidden");
  document.body.classList.add("is-logged-in");
  const mobileNav = $("mobileBottomNav");
  if (mobileNav) mobileNav.classList.remove("hidden");
  navigateToWindow("windowOverview");

  // Bloqueio compulsório de primeiro login
  if (user && user.precisa_trocar_senha) {
    openForceChangePasswordModal();
  } else {
    closeForceChangePasswordModal();
  }
}

/** Configuração declarativa de cada perfil: o que aparece e como é descrito. */
const ROLE_CONFIG = {
ADMIN: {
bannerClass: "",
bannerIcon: "key",
title: "Painel da administração (síndico)",
desc: "Acesso completo: cadastro de moradores, portaria, reservas, comunicados, livro de ocorrências, visitantes e segurança operacional.",
modules: ["Units", "Deliveries", "Reservations", "Notices", "Tickets", "Visitors", "Audit"],
stats: ["Moradores", "Acessos", "Reservas", "Avisos"],
deliveriesTitle: "Portaria e encomendas",
deliveriesDesc: "Registro de chegada de entregas, aviso ao morador e baixa de retirada.",
reservationsDesc: "Agendamento de áreas comuns com identificação completa dos solicitantes.",
reservasLabel: "Reservas ativas",
navDeliveries: "Encomendas",
},
PORTARIA: {
bannerClass: "portaria",
bannerIcon: "shield",
title: "Painel da portaria (controle operacional)",
desc: "Controle de encomendas, registro de entrada/saída de visitantes e acompanhamento do cronograma de reservas para entrega de chaves.",
modules: ["Deliveries", "Reservations", "Visitors", "Notices"],
stats: ["Acessos", "Reservas", "Avisos"],
deliveriesTitle: "Recepção de encomendas",
deliveriesDesc: "Registrar a chegada de encomendas e dar baixa na entrega aos condôminos.",
reservationsDesc: "Consultar o cronograma de eventos para liberar chaves e acessos.",
reservasLabel: "Reservas agendadas",
navDeliveries: "Recepção de encomendas",
},
MORADOR: {
bannerClass: "morador",
bannerIcon: "user",
title: "Painel do condômino (protegido pela LGPD)",
desc: "Acompanhe suas encomendas, agende áreas comuns, pré-autorize visitantes e registre ocorrências com resposta oficial do síndico.",
modules: ["Deliveries", "Reservations", "Notices", "Tickets", "Visitors"],
stats: ["Encomendas", "Reservas", "Avisos"],
deliveriesTitle: "Minhas encomendas",
deliveriesDesc: "Consulte os pacotes recebidos na portaria para o seu apartamento.",
reservationsDesc: "Agende churrasqueira e salão. As reservas de vizinhos aparecem de forma anônima (LGPD).",
reservasLabel: "Espaços ocupados",
navDeliveries: "Minhas encomendas",
},
};
ROLE_CONFIG.SINDICO = ROLE_CONFIG.ADMIN;

const ALL_MODULES = ["Units", "Deliveries", "Reservations", "Notices", "Tickets", "Visitors", "Audit"];
const ALL_STATS = ["Moradores", "Acessos", "Encomendas", "Reservas", "Avisos"];

function applyRoleBasedAccess(user) {
  const cfg = ROLE_CONFIG[user.tipo_usuario];
  if (!cfg) return;

  // Banner de contexto (compatibilidade se existir no DOM)
  const banner = $("roleContextBanner");
  if (banner) {
    banner.className = `role-context-banner ${cfg.bannerClass}`.trim();
    const bIcon = $("roleContextIcon");
    if (bIcon) bIcon.innerHTML = icon(cfg.bannerIcon, "ico");
    const bTitle = $("roleContextTitle");
    if (bTitle) bTitle.textContent = cfg.title;
    const bDesc = $("roleContextDesc");
    if (bDesc) bDesc.textContent = cfg.desc;
  }

  // Indicadores visíveis
  ALL_STATS.forEach((s) => {
    const stat = $(`cardStat${s}`);
    if (stat) stat.classList.toggle("hidden", !cfg.stats.includes(s));
  });

  // Textos adaptados ao perfil
  const statResLabel = $("statReservasLabel");
  if (statResLabel) statResLabel.textContent = cfg.reservasLabel;
  const navDelivLabel = $("navDeliveriesLabel");
  if (navDelivLabel) navDelivLabel.textContent = cfg.navDeliveries;

  // Rótulos específicos para visitantes conforme perfil
  const btnNewVisitorLabel = $("btnNewVisitorLabel");
  if (btnNewVisitorLabel) {
    btnNewVisitorLabel.textContent = user.tipo_usuario === "MORADOR" ? "Autorizar visitante" : "Registrar visitante";
  }
  const formNewVisitorTitle = $("formNewVisitorTitle");
  if (formNewVisitorTitle) {
    formNewVisitorTitle.textContent = user.tipo_usuario === "MORADOR"
      ? "Pré-autorizar convidado ou prestador de serviço"
      : "Registrar entrada de visitante ou prestador";
  }

  // Ações restritas
  const admin = isAdminRole(user);
  const staff = admin || user.tipo_usuario === "PORTARIA";
  const isMorador = user.tipo_usuario === "MORADOR";
  const isPortaria = user.tipo_usuario === "PORTARIA";

  const adminUnitActions = $("adminUnitActions");
  if (adminUnitActions) adminUnitActions.classList.toggle("hidden", !admin);

  const adminNoticeToolbar = $("adminNoticeToolbar");
  if (adminNoticeToolbar) adminNoticeToolbar.classList.toggle("hidden", !admin);

  const residentHelp = $("residentNoticeHelp");
  if (residentHelp) residentHelp.classList.toggle("hidden", admin);

  const staffDeliveryActions = $("staffDeliveryActions");
  if (staffDeliveryActions) staffDeliveryActions.classList.toggle("hidden", !staff);

  const residentReservationToolbar = $("residentReservationToolbar");
  if (residentReservationToolbar) residentReservationToolbar.classList.toggle("hidden", isPortaria);

  // Menu lateral espelha os módulos permitidos diretamente pela role
  document.querySelectorAll(".nav-item[data-card]").forEach((item) => {
    const modKey = (item.dataset.card || "").replace("cardModule", "");
    item.classList.toggle("hidden", !cfg.modules.includes(modKey));
  });

  const navSettings = $("navSettings");
  if (navSettings) {
    navSettings.classList.toggle("hidden", !admin);
  }

  // Cabeçalho Executivo Limpo da Visão Geral
  const greetingEl = $("overviewUserGreeting");
  if (greetingEl) {
    if (isMorador) {
      const firstName = (user.nome || "Condômino").split(" ")[0];
      greetingEl.textContent = `Olá, ${firstName}`;
    } else if (isPortaria) {
      greetingEl.textContent = "Painel da Portaria";
    } else {
      greetingEl.textContent = "Painel da Administração";
    }
  }

  const userSubEl = $("overviewUserSub");
  if (userSubEl) {
    if (isMorador) {
      userSubEl.textContent = "Avisos do condomínio, entregas e agendamento de áreas comuns";
    } else if (isPortaria) {
      userSubEl.textContent = "Guarita 24h • Ramal 100 • Controle de encomendas e visitantes";
    } else {
      const condoNome = (window.condoSettingsData && window.condoSettingsData.nome_condominio) || "Condomínio";
      userSubEl.textContent = `Gestão operacional e administrativa • ${condoNome}`;
    }
  }

  // Botões de Ação Direta no Cabeçalho da Visão Geral (Discretos e assertivos)
  const btnReserva = $("btnCleanReserva");
  if (btnReserva) btnReserva.classList.toggle("hidden", isPortaria);

  const btnVisitante = $("btnCleanVisitante");
  if (btnVisitante) btnVisitante.classList.toggle("hidden", !isMorador);

  const btnOcorrencia = $("btnCleanOcorrencia");
  if (btnOcorrencia) {
    btnOcorrencia.classList.toggle("hidden", isPortaria);
    const span = btnOcorrencia.querySelector("span");
    if (span) span.textContent = admin ? "Ver Ocorrências" : "Abrir Chamado";
  }

  const btnPortariaVisitante = $("btnCleanPortariaVisitante");
  if (btnPortariaVisitante) btnPortariaVisitante.classList.toggle("hidden", !isPortaria);

  const btnPortariaEncomenda = $("btnCleanPortariaEncomenda");
  if (btnPortariaEncomenda) btnPortariaEncomenda.classList.toggle("hidden", !isPortaria);

  const btnAdminAviso = $("btnCleanAdminAviso");
  if (btnAdminAviso) btnAdminAviso.classList.toggle("hidden", !admin);

  const btnAdminUnidade = $("btnCleanAdminUnidade");
  if (btnAdminUnidade) btnAdminUnidade.classList.toggle("hidden", !admin);

  // Rótulos do widget secundário da Visão Geral
  const overviewSecTitle = $("overviewSecTitle");
  if (overviewSecTitle) {
    overviewSecTitle.textContent = isMorador ? "Suas Encomendas na Guarita" : "Encomendas na Portaria";
  }

  loadQuickStatsForRole(user);
}

async function loadQuickStatsForRole(user) {
  const set = (id, value) => {
    const el = $(id);
    if (el) el.textContent = value;
  };

  const isMorador = user && user.tipo_usuario === "MORADOR";
  const isPortaria = user && user.tipo_usuario === "PORTARIA";
  const isAdmin = isAdminRole(user);

  // Alterna o painel diário do perfil correspondente
  const moradorPanel = $("moradorDailyPanel");
  const portariaPanel = $("portariaDailyPanel");
  const sindicoPanel = $("sindicoDailyPanel");

  if (moradorPanel) moradorPanel.classList.toggle("hidden", !isMorador);
  if (portariaPanel) portariaPanel.classList.toggle("hidden", !isPortaria);
  if (sindicoPanel) sindicoPanel.classList.toggle("hidden", !isAdmin);

  let notices = [];
  let deliveries = [];
  let reservations = [];

  const tasks = [
    api("/api/notices").then((n) => {
      notices = n || [];
      set("statAvisos", notices.length);
      renderOverviewNotices(notices);
    }).catch(() => { notices = []; }),

    api("/api/deliveries").then((d) => {
      deliveries = d || [];
      const pendentes = deliveries.filter((x) => x.status === "AGUARDANDO_RETIRADA");
      set(isMorador ? "statEncomendasMorador" : "statAcessos", pendentes.length);
      renderOverviewDeliveries(pendentes, user);
    }).catch(() => { deliveries = []; }),

    api("/api/reservations").then((r) => {
      reservations = r || [];
      const ativas = reservations.filter((x) => x.status === "CONFIRMADA");
      set("statReservas", ativas.length);
      renderOverviewAgenda(ativas, user);
    }).catch(() => { reservations = []; }),
  ];

  if (isAdmin) {
    tasks.push(
      api("/api/units").then((u) => {
        const ocupadas = (u || []).filter((x) => x.morador_responsavel).length;
        set("statMoradores", `${ocupadas} / ${(u || []).length}`);
      }).catch(() => {})
    );
  }

  // Falhas não quebram a interface
  await Promise.allSettled(tasks);

  // Renderiza o Painel do Dia sob medida para o perfil conectado
  if (isMorador) {
    renderMoradorDaily(user, notices, deliveries, reservations);
  } else if (isPortaria) {
    renderPortariaDaily(user, deliveries, reservations);
  } else if (isAdmin) {
    renderSindicoDaily(user, reservations);
  }

  checkActiveSlotOffers(user);
}

// ----------------------------------------------------
// 5.1 PAINEL DO DIA - MORADOR (ACOLHEDOR & DIRETO)
// ----------------------------------------------------
function renderMoradorDaily(user, notices, deliveries, reservations) {
  // 1. Alerta de Encomendas na Guarita
  const alertEl = $("moradorDeliveryAlert");
  const titleEl = $("moradorDeliveryTitle");
  const descEl = $("moradorDeliveryDesc");
  const itemsEl = $("moradorDeliveryItems");

  const pendentes = (deliveries || []).filter((d) => d.status === "AGUARDANDO_RETIRADA");
  if (alertEl && titleEl && descEl) {
    if (pendentes.length > 0) {
      alertEl.classList.add("has-packages");
      titleEl.textContent = `Você tem ${pendentes.length} encomenda${pendentes.length > 1 ? 's' : ''} aguardando retirada`;
      descEl.textContent = "Disponível na guarita 24h. Apresente documento de identidade para retirar.";
      if (itemsEl) {
        itemsEl.innerHTML = pendentes.slice(0, 3).map((p) => {
          const cod = p.codigo_rastreio ? `(${escapeHtml(p.codigo_rastreio)})` : "";
          const desc = escapeHtml(p.descricao || "Pacote");
          return `<span class="delivery-chip-item">${icon("package", "ico ico-xs")} ${desc} ${cod}</span>`;
        }).join("");
      }
    } else {
      alertEl.classList.remove("has-packages");
      titleEl.textContent = "Nenhuma encomenda aguardando retirada";
      descEl.textContent = "Suas correspondências estão em dia. Quando um pacote chegar na portaria, você será avisado aqui imediatamente.";
      if (itemsEl) itemsEl.innerHTML = "";
    }
  }

  // 2. Próxima Reserva
  const resBody = $("moradorReservationBody");
  if (resBody) {
    const hojeStr = new Date().toISOString().split("T")[0];
    const minhasFuturas = (reservations || [])
      .filter((r) => r.is_mine && r.status === "CONFIRMADA" && (!r.data_reserva || r.data_reserva >= hojeStr))
      .sort((a, b) => (a.data_reserva || "").localeCompare(b.data_reserva || ""));

    if (minhasFuturas.length > 0) {
      const prox = minhasFuturas[0];
      const dataFmt = prox.data_reserva
        ? new Date(prox.data_reserva + "T00:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" })
        : "Data a confirmar";
      const horario = prox.hora_inicio && prox.hora_fim ? `${prox.hora_inicio.slice(0, 5)} às ${prox.hora_fim.slice(0, 5)}` : "Horário comercial";
      const area = prox.area_comum ? escapeHtml(prox.area_comum.nome) : "Espaço Reservado";

      resBody.innerHTML = `
        <div class="daily-feed-info" style="gap:5px;">
          <strong style="font-size:1.05rem; color:var(--primary);">${area}</strong>
          <span style="font-size:0.92rem; color:var(--text-main); font-weight:600;">
            ${icon("calendar", "ico ico-xs")} ${dataFmt} &bull; ${horario}
          </span>
          <span class="muted" style="font-size:0.82rem;">${prox.chave_entregue ? "Chave já retirada com a guarita" : "Chave disponível na portaria no horário do evento"}</span>
        </div>
        <div style="margin-top:0.75rem; display:flex; gap:0.5rem; flex-wrap:wrap;">
          <button type="button" class="btn-daily-sm-action" onclick="openGuestsModal(${Number(prox.id)}, '${escapeHtml(area)}', '${prox.data_reserva || ''}', true)">
            ${icon("users", "ico ico-xs")}
            <span>Gerenciar Convidados</span>
          </button>
          <button type="button" class="daily-link" data-window="windowReservations">Ver detalhes &rarr;</button>
        </div>
      `;
    } else {
      resBody.innerHTML = `
        <p class="daily-placeholder-text" style="padding:0.6rem 0;">Você não possui reservas agendadas para os próximos dias.</p>
        <button type="button" class="btn-daily-sm-action" data-window="windowReservations" style="align-self:flex-start;">
          ${icon("plus", "ico ico-xs")}
          <span>Agendar Churrasqueira ou Salão</span>
        </button>
      `;
    }
  }

  // 3. Comunicado Recente
  const noticeBody = $("moradorNoticeBody");
  if (noticeBody) {
    if (notices && notices.length > 0) {
      const n = notices[0];
      const cat = (n.categoria || "GERAL").toLowerCase();
      const label = CATEGORY_LABEL[n.categoria] || n.categoria;
      const dataFmt = new Date(n.criado_em).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
      const snippet = n.mensagem ? (n.mensagem.length > 130 ? n.mensagem.substring(0, 127) + "..." : n.mensagem) : "";

      noticeBody.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.35rem;">
          <span class="clean-cat-pill ${cat}">${escapeHtml(label)}</span>
          <time class="clean-notice-date">${dataFmt}</time>
        </div>
        <strong style="font-size:1rem; color:var(--text-main); display:block; margin-bottom:0.25rem;">${escapeHtml(n.titulo)}</strong>
        <p style="font-size:0.88rem; color:var(--text-muted); line-height:1.45;">${escapeHtml(snippet)}</p>
        <button type="button" class="daily-link" data-window="windowNotices" style="margin-top:0.5rem; padding-left:0;">Ler comunicado no mural &rarr;</button>
      `;
    } else {
      noticeBody.innerHTML = `<p class="daily-placeholder-text">Nenhum comunicado recente publicado no mural.</p>`;
    }
  }

  document.querySelectorAll("#moradorDailyPanel [data-window]").forEach((el) => {
    el.addEventListener("click", () => navigateToWindow(el.dataset.window));
  });
}

// ----------------------------------------------------
// 5.2 PAINEL DO DIA - PORTARIA (AGILIDADE 24H)
// ----------------------------------------------------
let cachedUnitsForFastSearch = null;

function initPortariaFastSearch() {
  const inputSearch = $("inputPortariaFastSearch");
  const resultsBox = $("portariaFastSearchResults");
  const btnClear = $("btnPortariaFastSearchClear");
  if (!inputSearch || !resultsBox) return;

  if (btnClear) {
    btnClear.onclick = () => {
      inputSearch.value = "";
      resultsBox.classList.add("hidden");
      resultsBox.innerHTML = "";
      btnClear.classList.add("hidden");
    };
  }

  inputSearch.oninput = async () => {
    const q = inputSearch.value.trim().toLowerCase();
    if (btnClear) btnClear.classList.toggle("hidden", !q);

    if (q.length < 1) {
      resultsBox.classList.add("hidden");
      resultsBox.innerHTML = "";
      return;
    }

    if (!cachedUnitsForFastSearch) {
      try {
        cachedUnitsForFastSearch = await api("/api/units");
      } catch {
        cachedUnitsForFastSearch = [];
      }
    }

    const matches = (cachedUnitsForFastSearch || []).filter((u) => {
      const numMatch = String(u.numero || "").toLowerCase().includes(q);
      const blocoMatch = String(u.bloco || "").toLowerCase().includes(q);
      const moradorNome = u.morador_responsavel ? u.morador_responsavel.nome.toLowerCase() : "";
      const moradorMatch = moradorNome.includes(q);
      return numMatch || blocoMatch || moradorMatch;
    });

    if (!matches.length) {
      resultsBox.innerHTML = `<div style="padding:0.75rem 1rem; color:var(--text-dim); font-size:0.88rem;">Nenhum apartamento ou morador localizado para "${escapeHtml(q)}".</div>`;
      resultsBox.classList.remove("hidden");
      return;
    }

    resultsBox.innerHTML = matches.slice(0, 6).map((u) => {
      const blocoApto = `Bloco ${escapeHtml(u.bloco)} - Apto ${escapeHtml(u.numero)}`;
      const morador = u.morador_responsavel ? escapeHtml(u.morador_responsavel.nome) : `<span class="muted">Vago / Não atribuído</span>`;
      const tel = u.morador_responsavel && u.morador_responsavel.telefone ? ` &bull; Tel: ${escapeHtml(u.morador_responsavel.telefone)}` : "";

      return `
        <div class="portaria-search-result-item">
          <div>
            <strong>${blocoApto}</strong>
            <div style="font-size:0.82rem; color:var(--text-muted);">${morador}${tel}</div>
          </div>
          <div style="display:flex; gap:0.4rem;">
            <button type="button" class="btn-daily-sm-action" onclick="navigateToWindow('windowDeliveries')" title="Ir para encomendas">
              ${icon("package", "ico ico-xs")} Encomenda
            </button>
            <button type="button" class="btn-daily-sm-action" onclick="navigateToWindow('windowVisitors')" title="Ir para visitantes">
              ${icon("user-check", "ico ico-xs")} Visitante
            </button>
          </div>
        </div>`;
    }).join("");
    resultsBox.classList.remove("hidden");
  };
}

async function renderPortariaDaily(user, deliveries, reservations) {
  initPortariaFastSearch();

  // 1. Visitantes Esperados Hoje
  const guestsFeed = $("portariaTodayGuestsFeed");
  if (guestsFeed) {
    try {
      const guests = await api("/api/visitors/today").catch(() => []);
      if (!guests || !guests.length) {
        guestsFeed.innerHTML = `
          <p class="daily-placeholder-text">Nenhum visitante pré-autorizado para hoje até o momento.</p>`;
      } else {
        guestsFeed.innerHTML = guests.slice(0, 5).map((g) => {
          const nome = escapeHtml(g.nome || "Visitante");
          const destino = escapeHtml(g.unidade_desc || "Condomínio");
          const tipo = escapeHtml(g.tipo || "VISITANTE");
          const entradaRegistrada = !!g.entrada_em;
          const saidaRegistrada = !!g.saida_em;

          let btnAcao = "";
          if (!entradaRegistrada) {
            btnAcao = `<button type="button" class="daily-feed-btn entry" onclick="handleVisitorEntry(${g.id}, '${nome}')">${icon("check", "ico ico-xs")} Registrar Entrada</button>`;
          } else if (!saidaRegistrada) {
            btnAcao = `<button type="button" class="daily-feed-btn exit" onclick="handleVisitorExit(${g.id}, '${nome}')">${icon("arrow", "ico ico-xs")} Registrar Saída</button>`;
          } else {
            btnAcao = `<span class="badge-status entregue" style="font-size:0.75rem;">Finalizado</span>`;
          }

          return `
            <div class="daily-feed-row">
              <div class="daily-feed-info">
                <strong>${nome}</strong>
                <span>Destino: ${destino} &bull; Tipo: ${tipo}</span>
              </div>
              <div style="flex-shrink:0;">${btnAcao}</div>
            </div>`;
        }).join("");
      }
    } catch {
      guestsFeed.innerHTML = `<p class="daily-placeholder-text">Erro ao carregar visitantes de hoje.</p>`;
    }
  }

  // 2. Encomendas Pendentes de Retirada
  const packagesFeed = $("portariaPendingPackagesFeed");
  if (packagesFeed) {
    const pendentes = (deliveries || []).filter((d) => d.status === "AGUARDANDO_RETIRADA");
    if (!pendentes.length) {
      packagesFeed.innerHTML = `<p class="daily-placeholder-text">Nenhuma encomenda pendente de retirada na guarita.</p>`;
    } else {
      packagesFeed.innerHTML = pendentes.slice(0, 4).map((p) => {
        const dest = escapeHtml(p.destinatario || "Morador");
        const unid = p.unidade_desc ? escapeHtml(p.unidade_desc) : "";
        const rastreio = p.codigo_rastreio ? ` &bull; Cód: ${escapeHtml(p.codigo_rastreio)}` : "";

        return `
          <div class="daily-feed-row">
            <div class="daily-feed-info">
              <strong>${dest}</strong>
              <span>${unid}${rastreio}</span>
            </div>
            <div style="flex-shrink:0;">
              <button type="button" class="daily-feed-btn deliver" onclick="handleDeliverPackage(${p.id})">
                ${icon("check", "ico ico-xs")} Entregar ao Morador
              </button>
            </div>
          </div>`;
      }).join("");
    }
  }

  document.querySelectorAll("#portariaDailyPanel [data-window]").forEach((el) => {
    el.addEventListener("click", () => navigateToWindow(el.dataset.window));
  });
}

// ----------------------------------------------------
// 5.3 PAINEL DO DIA - SÍNDICO (GOVERNANÇA & DEMANDAS)
// ----------------------------------------------------
async function renderSindicoDaily(user, reservations) {
  // 1. Ocorrências e Chamados Pendentes
  const ticketsFeed = $("sindicoPendingTicketsFeed");
  if (ticketsFeed) {
    try {
      const allTickets = await api("/api/tickets").catch(() => []);
      const pendentes = (allTickets || []).filter((t) => t.status === "ABERTO" || t.status === "EM_ANALISE");
      if (!pendentes.length) {
        ticketsFeed.innerHTML = `<p class="daily-placeholder-text">Nenhuma ocorrência pendente de parecer no momento. Todas as solicitações foram respondidas!</p>`;
      } else {
        ticketsFeed.innerHTML = pendentes.slice(0, 3).map((t) => {
          const titulo = escapeHtml(t.titulo || "Ocorrência");
          const morador = escapeHtml(t.morador_nome || "Morador");
          const unid = escapeHtml(t.unidade_desc || "");
          const dataFmt = new Date(t.criado_em).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });

          return `
            <div class="daily-feed-row">
              <div class="daily-feed-info">
                <strong>${titulo}</strong>
                <span>${morador} (${unid}) &bull; Aberto em: ${dataFmt}</span>
              </div>
              <div style="flex-shrink:0;">
                <button type="button" class="daily-feed-btn reply" onclick="openReplyTicketModal(${t.id}, '${escapeHtml(t.status)}', '${escapeHtml(t.resposta_sindico || '')}')">
                  ${icon("clipboard", "ico ico-xs")} Responder
                </button>
              </div>
            </div>`;
        }).join("");
      }
    } catch {
      ticketsFeed.innerHTML = `<p class="daily-placeholder-text">Erro ao consultar ocorrências.</p>`;
    }
  }

  // 2. Ocupação de Áreas Comuns
  const agendaFeed = $("sindicoAgendaFeed");
  if (agendaFeed) {
    const hojeStr = new Date().toISOString().split("T")[0];
    const proximas = (reservations || [])
      .filter((r) => r.status === "CONFIRMADA" && (!r.data_reserva || r.data_reserva >= hojeStr))
      .sort((a, b) => (a.data_reserva || "").localeCompare(b.data_reserva || ""));

    if (!proximas.length) {
      agendaFeed.innerHTML = `<p class="daily-placeholder-text">Nenhum evento agendado nas áreas comuns para os próximos dias.</p>`;
    } else {
      agendaFeed.innerHTML = proximas.slice(0, 3).map((r) => {
        const area = r.area_comum ? escapeHtml(r.area_comum.nome) : "Área Comum";
        const dataFmt = r.data_reserva
          ? new Date(r.data_reserva + "T00:00:00").toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short" })
          : "Data";
        const horario = r.hora_inicio && r.hora_fim ? `${r.hora_inicio.slice(0, 5)} - ${r.hora_fim.slice(0, 5)}` : "";
        const solicitante = escapeHtml(r.morador_nome || r.unidade_desc || "Condômino");

        return `
          <div class="daily-feed-row">
            <div class="daily-feed-info">
              <strong>${area} &bull; ${dataFmt}</strong>
              <span>${horario ? horario + ' &bull; ' : ''}Solicitante: ${solicitante}</span>
            </div>
          </div>`;
      }).join("");
    }
  }

  document.querySelectorAll("#sindicoDailyPanel [data-window]").forEach((el) => {
    el.addEventListener("click", () => navigateToWindow(el.dataset.window));
  });
}



// ----------------------------------------------------
// 5.5 GAVETA LATERAL E NAVEGAÇÃO MÓVEL (OFF-CANVAS)
// ----------------------------------------------------
window.closeMobileDrawer = function () {
  const sidebar = document.querySelector(".sidebar");
  if (sidebar) sidebar.classList.remove("mobile-open");
  document.body.classList.remove("drawer-open");
};

function setupMobileDrawer() {
  const btnToggle = $("btnToggleMobileDrawer");
  const btnMenuBottom = $("mNavOpenMenu");
  const sidebar = document.querySelector(".sidebar");

  const toggle = () => {
    if (sidebar) sidebar.classList.toggle("mobile-open");
    document.body.classList.toggle("drawer-open");
  };

  if (btnToggle) btnToggle.addEventListener("click", toggle);
  if (btnMenuBottom) btnMenuBottom.addEventListener("click", toggle);

  // Fecha a gaveta ao clicar em qualquer item do menu ou fora
  document.querySelectorAll(".side-nav .nav-item").forEach((btn) => {
    btn.addEventListener("click", window.closeMobileDrawer);
  });

  document.body.addEventListener("click", (e) => {
    if (document.body.classList.contains("drawer-open") &&
        !e.target.closest(".sidebar") &&
        !e.target.closest("#btnToggleMobileDrawer") &&
        !e.target.closest("#mNavOpenMenu")) {
      window.closeMobileDrawer();
    }
  });
}

// Compatibilidade retroativa para funções de visão geral legadas
function renderOverviewNotices(notices) {
  const container = $("overviewNoticesList");
  if (!container) return;
  if (!notices || !notices.length) {
    container.innerHTML = `<p class="feed-placeholder">Nenhum aviso.</p>`;
    return;
  }
}

function renderOverviewAgenda(reservations, user) {
  const container = $("overviewAgendaList");
  if (!container) return;
  if (!reservations || !reservations.length) {
    container.innerHTML = `<p class="feed-placeholder">Nenhuma reserva.</p>`;
    return;
  }
}

function renderOverviewDeliveries(deliveries, user) {
  const container = $("overviewDeliveriesList");
  if (!container) return;
  if (!deliveries || !deliveries.length) {
    container.innerHTML = `<p class="feed-placeholder">Nenhuma entrega.</p>`;
    return;
  }
}

// ==========================================
// 6. UNIDADES E MORADORES
// ==========================================
const unitsTableBody = $("unitsTableBody");
const formNewUnit = $("formNewUnit");

$("btnToggleNewUnitForm").addEventListener("click", () => {
  formNewUnit.classList.toggle("hidden");
  if (!formNewUnit.classList.contains("hidden")) {
    formNewUnit.scrollIntoView({ behavior: "smooth", block: "start" });
    $("inputBloco").focus();
  }
});
$("btnCancelNewUnit").addEventListener("click", () => formNewUnit.classList.add("hidden"));

formNewUnit.addEventListener("submit", async (e) => {
  e.preventDefault();
  const bloco = $("inputBloco").value.trim();
  const numero = $("inputNumero").value.trim();
  const andarVal = $("inputAndar").value;
  const andar = andarVal ? parseInt(andarVal, 10) : null;

  try {
    await api("/api/units", { method: "POST", body: { bloco, numero, andar } });
    formNewUnit.reset();
    formNewUnit.classList.add("hidden");
    showToast("Unidade cadastrada com sucesso.", "success");
    loadUnits();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
});

async function loadUnits() {
  const user = getStoredUser();
  const isAdmin = isAdminRole(user);
  unitsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Carregando unidades...</td></tr>`;
  try {
    const units = await api("/api/units");
    if (!units.length) {
      unitsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Nenhuma unidade cadastrada.</td></tr>`;
      return;
    }

    unitsTableBody.innerHTML = units.map((u) => {
      const ocupado = !!u.morador_responsavel;
      const statusBadge = ocupado
        ? `<span class="badge-status ocupado">Ocupado</span>`
        : `<span class="badge-status vago">Disponível</span>`;

      const nome = ocupado
        ? `<strong>${escapeHtml(u.morador_responsavel.nome)}</strong>`
        : `<span class="muted">Não atribuído</span>`;
      const contato = ocupado
        ? escapeHtml(u.morador_responsavel.telefone || u.morador_responsavel.email)
        : `<span class="muted">-</span>`;
      const andar = u.andar ? `${escapeHtml(u.andar)}º andar` : "Térreo";

      let acao = `<span class="muted">-</span>`;
      if (isAdmin) {
        if (ocupado) {
          acao = `
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
              <button type="button" class="btn-action-deliver" onclick="openAssignResidentModal(${Number(u.id)}, '${escapeHtml(u.bloco)}', '${escapeHtml(u.numero)}', true)" title="Trocar morador">${icon("refresh")}Trocar</button>
              <button type="button" class="btn-action-danger" onclick="handleUnassignResident(${Number(u.id)}, '${escapeHtml(u.bloco)}', '${escapeHtml(u.numero)}')" title="Liberar apartamento">${icon("close")}Desvincular</button>
            </div>`;
        } else {
          acao = `<button type="button" class="btn-primary-sm" style="min-height:34px; padding:6px 12px; font-size:0.82rem;" onclick="openAssignResidentModal(${Number(u.id)}, '${escapeHtml(u.bloco)}', '${escapeHtml(u.numero)}', false)">${icon("plus")}Vincular Morador</button>`;
        }
      }

      return `
        <tr>
          <td data-label="Unidade">
            <strong>${escapeHtml(u.bloco)} - Apto ${escapeHtml(u.numero)}</strong>
            <small class="muted">${ocupado ? escapeHtml(u.morador_responsavel.nome) : 'Disponível'}</small>
          </td>
          <td data-label="Andar">${andar}</td>
          <td data-label="Morador">${nome}</td>
          <td data-label="Contato">${contato}</td>
          <td data-label="Status">${statusBadge}</td>
          <td data-label="Ações">${acao}</td>
        </tr>`;
    }).join("");
  } catch (err) {
    unitsTableBody.innerHTML = `<tr><td colspan="6" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

// Formulário de Cadastro e Vínculo de Morador na Unidade
const formAssignResident = $("formAssignResident");
const assignTargetUnitId = $("assignTargetUnitId");
const formAssignResidentTitle = $("formAssignResidentTitle");
const formAssignResidentSub = $("formAssignResidentSub");

window.openAssignResidentModal = function (unitId, bloco, numero, isReplacement) {
  assignTargetUnitId.value = unitId;
  formAssignResidentTitle.textContent = isReplacement
    ? `Trocar morador: ${bloco} - Apto ${numero}`
    : `Vincular morador: ${bloco} - Apto ${numero}`;
  formAssignResidentSub.textContent = `Cadastre os dados de login e senha para o novo morador deste apartamento.`;

  formAssignResident.classList.remove("hidden");
  $("inputResidentNome").focus();
  formAssignResident.scrollIntoView({ behavior: "smooth", block: "nearest" });
};

function closeAssignResidentModal() {
  formAssignResident.classList.add("hidden");
  formAssignResident.reset();
  $("inputResidentSenha").value = "Morador@123";
}

$("btnCancelAssignResident").addEventListener("click", closeAssignResidentModal);
$("btnCancelAssignResident2").addEventListener("click", closeAssignResidentModal);

formAssignResident.addEventListener("submit", async (e) => {
  e.preventDefault();
  const unitId = parseInt(assignTargetUnitId.value, 10);
  const nome = $("inputResidentNome").value.trim();
  const email = $("inputResidentEmail").value.trim();
  const telefone = $("inputResidentTelefone").value.trim();
  const senha = $("inputResidentSenha").value;

  if (!unitId || !nome || !email || !senha) {
    showToast("Preencha todos os campos obrigatórios.", "error");
    return;
  }

  try {
    // 1. Cadastra o novo morador já associando à unidade
    await api("/api/auth/register", {
      method: "POST",
      body: {
        nome,
        email,
        telefone: telefone || null,
        senha,
        tipo_usuario: "MORADOR",
        unidade_id: unitId
      }
    });

    closeAssignResidentModal();
    showToast(`Morador salvo com sucesso! Login: ${email} | Senha temporária: ${senha}`, "success");
    loadUnits();
    loadQuickStatsForRole(getStoredUser());

    // Mostra alerta visual para o síndico poder repassar as credenciais ao morador
    await showCustomConfirm({
      title: "Credenciais de Acesso Geradas",
      message: `O morador ${nome} foi vinculado com sucesso!\n\nDados para acesso inicial:\n• E-mail: ${email}\n• Senha temporária: ${senha}\n\nNota de segurança: No primeiro acesso, o sistema exigirá obrigatoriamente que o morador altere esta senha para uma definitiva.`,
      confirmText: "Entendido / Copiado",
      cancelText: "Fechar",
      iconName: "key"
    });
  } catch (err) {
    showToast(err.message, "error");
  }
});

window.handleUnassignResident = async function (unitId, bloco, numero) {
  const confirmed = await showCustomConfirm({
    title: "Liberar Apartamento",
    message: `Deseja desvincular o morador do apartamento ${bloco} - Apto ${numero}? A unidade voltará para o status "Disponível".`,
    confirmText: "Sim, Desvincular Morador",
    cancelText: "Cancelar",
    isDanger: true,
    iconName: "trash"
  });

  if (!confirmed) return;

  try {
    await api(`/api/units/${unitId}/assign`, {
      method: "PUT",
      body: { morador_id: null }
    });
    showToast("Morador desvinculado. O apartamento está disponível novamente.", "success");
    loadUnits();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 7. ENCOMENDAS
// ==========================================
const deliveriesTableBody = $("deliveriesTableBody");
const formNewDelivery = $("formNewDelivery");
const selectDeliveryUnit = $("selectDeliveryUnit");

$("btnCancelNewDelivery").addEventListener("click", () => formNewDelivery.classList.add("hidden"));

$("btnToggleNewDeliveryForm").addEventListener("click", async () => {
  formNewDelivery.classList.toggle("hidden");
  if (!formNewDelivery.classList.contains("hidden")) {
    await populateDeliveryUnitsSelect();
    formNewDelivery.scrollIntoView({ behavior: "smooth", block: "start" });
    selectDeliveryUnit.focus();
  }
});

async function populateDeliveryUnitsSelect() {
  try {
    const units = await api("/api/units");
    // Filtra apenas unidades ocupadas (com morador cadastrado para receber encomendas)
    const occupiedUnits = units.filter((u) => !!u.morador_responsavel);

    if (!occupiedUnits.length) {
      selectDeliveryUnit.innerHTML = `<option value="">Nenhum apartamento com morador vinculado</option>`;
      return;
    }

    selectDeliveryUnit.innerHTML =
      `<option value="">Selecione o apartamento de destino...</option>` +
      occupiedUnits.map((u) => {
        return `<option value="${escapeHtml(u.id)}">${escapeHtml(u.bloco)} - Apto ${escapeHtml(u.numero)} (${escapeHtml(u.morador_responsavel.nome)})</option>`;
      }).join("");
  } catch {
    selectDeliveryUnit.innerHTML = `<option value="">Não foi possível carregar os apartamentos</option>`;
  }
}

formNewDelivery.addEventListener("submit", async (e) => {
  e.preventDefault();
  const unidadeId = parseInt(selectDeliveryUnit.value, 10);
  const descricao = $("inputDeliveryDesc").value.trim();
  const codigoRastreio = $("inputDeliveryTracking").value.trim();

  if (!unidadeId || !descricao) {
    showToast("Selecione o apartamento e informe a descrição do pacote.", "error");
    return;
  }

  try {
    await api("/api/deliveries", {
      method: "POST",
      body: { unidade_id: unidadeId, descricao, codigo_rastreio: codigoRastreio || null },
    });
    formNewDelivery.reset();
    formNewDelivery.classList.add("hidden");
    showToast("Encomenda registrada com sucesso na portaria.", "success");
    loadDeliveries();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
});

async function loadDeliveries() {
  const user = getStoredUser();
  if (!user) return;
  const isMorador = user.tipo_usuario === "MORADOR";
  const thActions = $("thDeliveryActions");
  const sub = $("windowDeliveriesSub");

  thActions.classList.toggle("hidden", isMorador);
  sub.textContent = isMorador
    ? "Encomendas destinadas exclusivamente à sua residência"
    : "Controle geral de recebimento e entrega de pacotes aos condôminos";

  const cols = isMorador ? 5 : 6;
  deliveriesTableBody.innerHTML = `<tr><td colspan="${cols}" class="table-empty">Carregando encomendas...</td></tr>`;

  try {
    const deliveries = await api("/api/deliveries");
    if (!deliveries.length) {
      deliveriesTableBody.innerHTML = `<tr><td colspan="${cols}" class="table-empty">Nenhuma encomenda registrada no momento.</td></tr>`;
      return;
    }

    deliveriesTableBody.innerHTML = deliveries.map((d) => {
      const entregue = d.status === "ENTREGUE";
      const status = entregue
        ? `<span class="badge-status entregue">Entregue</span>`
        : `<span class="badge-status pendente">Aguardando retirada</span>`;
      const unidade = d.unidade
        ? `${escapeHtml(d.unidade.bloco)} - Apto ${escapeHtml(d.unidade.numero)}`
        : `Apto ${escapeHtml(d.unidade_id)}`;
      const chegada = new Date(d.data_chegada).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
      const rastreio = d.codigo_rastreio ? `<code>${escapeHtml(d.codigo_rastreio)}</code>` : `<span class="muted">-</span>`;

      let acao = "";
      if (!isMorador) {
        acao = entregue
          ? `<td data-label="Ação"><small class="muted">Entregue a: ${escapeHtml(d.retirado_por || "Morador")}</small></td>`
          : `<td data-label="Ação"><button type="button" class="btn-action-deliver" onclick="handleDeliverPackage(${Number(d.id)})">${icon("check")}Baixar retirada</button></td>`;
      }

      return `
        <tr>
          <td data-label="Unidade">
            <strong>${unidade}</strong>
            <small class="muted">${escapeHtml(d.descricao)}</small>
          </td>
          <td data-label="Descrição">${escapeHtml(d.descricao)}</td>
          <td data-label="Rastreio">${rastreio}</td>
          <td data-label="Chegada">${chegada}</td>
          <td data-label="Status">${status}</td>
          ${acao}
        </tr>`;
    }).join("");
  } catch (err) {
    deliveriesTableBody.innerHTML = `<tr><td colspan="${cols}" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

window.handleDeliverPackage = async function (deliveryId) {
  const retiradoPor = await showCustomPrompt({
    title: "Baixa de Encomenda",
    message: "Registre a entrega do pacote ao morador ou pessoa autorizada.",
    label: "Nome de quem está retirando o pacote na portaria:",
    placeholder: "Ex: Carlos Silva (Morador)",
    confirmText: "Confirmar Retirada",
    cancelText: "Voltar",
    iconName: "package"
  });

  if (retiradoPor === null) return;

  try {
    await api(`/api/deliveries/${deliveryId}/deliver`, {
      method: "PUT",
      body: { retirado_por: retiradoPor.trim() || null },
    });
    showToast("Baixa realizada. O pacote foi marcado como entregue.", "success");
    loadDeliveries();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 8. RESERVAS DE ÁREAS COMUNS (LGPD)
// ==========================================
const reservationsTableBody = $("reservationsTableBody");
const formNewReservation = $("formNewReservation");
const selectReservationArea = $("selectReservationArea");
const inputReservationDate = $("inputReservationDate");
const inputReservationTimeStart = $("inputReservationTimeStart");
const inputReservationTimeEnd = $("inputReservationTimeEnd");
const areaRulesHint = $("areaRulesHint");
const areaRulesHintText = $("areaRulesHintText");
const areasCardsList = $("areasCardsList");

let cachedCommonAreas = [];
let cachedAllReservations = [];
let calendarCurrentDate = new Date();

$("btnCancelNewReservation").addEventListener("click", () => formNewReservation.classList.add("hidden"));

$("btnToggleNewReservationForm").addEventListener("click", async () => {
  formNewReservation.classList.toggle("hidden");
  if (!formNewReservation.classList.contains("hidden")) {
    const today = new Date().toISOString().split("T")[0];
    inputReservationDate.min = today;
    if (!inputReservationDate.value) inputReservationDate.value = today;
    await populateReservationAreasSelect();
    checkReservationPriorityNotice();
    formNewReservation.scrollIntoView({ behavior: "smooth", block: "start" });
    if (selectReservationArea) selectReservationArea.focus();
  }
});

// Controles de Navegação e Filtros do Calendário
const btnCalPrevMonth = $("btnCalPrevMonth");
const btnCalNextMonth = $("btnCalNextMonth");
const btnCalToday = $("btnCalToday");
const calendarAreaFilter = $("calendarAreaFilter");

if (btnCalPrevMonth) {
  btnCalPrevMonth.addEventListener("click", () => {
    calendarCurrentDate.setMonth(calendarCurrentDate.getMonth() - 1);
    renderReservationsCalendar();
  });
}
if (btnCalNextMonth) {
  btnCalNextMonth.addEventListener("click", () => {
    calendarCurrentDate.setMonth(calendarCurrentDate.getMonth() + 1);
    renderReservationsCalendar();
  });
}
if (btnCalToday) {
  btnCalToday.addEventListener("click", () => {
    calendarCurrentDate = new Date();
    renderReservationsCalendar();
  });
}
if (calendarAreaFilter) {
  calendarAreaFilter.addEventListener("change", () => {
    renderReservationsCalendar();
  });
}

async function populateReservationAreasSelect() {
  try {
    cachedCommonAreas = await api("/api/reservations/areas");
    selectReservationArea.innerHTML =
      `<option value="">Selecione o espaço comum...</option>` +
      cachedCommonAreas.map((a) => {
        const taxa = a.taxa_limpeza > 0 ? ` (taxa R$ ${Number(a.taxa_limpeza).toFixed(2)})` : " (gratuito)";
        return `<option value="${escapeHtml(a.id)}">${escapeHtml(a.nome)} - capacidade ${escapeHtml(a.capacidade_pessoas)} pessoas${taxa}</option>`;
      }).join("");

    if (calendarAreaFilter) {
      const curVal = calendarAreaFilter.value;
      calendarAreaFilter.innerHTML =
        `<option value="">Todos os Espaços</option>` +
        cachedCommonAreas.map((a) => `<option value="${escapeHtml(a.id)}">${escapeHtml(a.nome)}</option>`).join("");
      calendarAreaFilter.value = curVal || "";
    }
  } catch {
    selectReservationArea.innerHTML = `<option value="">Não foi possível carregar as áreas</option>`;
  }
}

function renderReservationsCalendar() {
  const grid = $("reservationsCalendarGrid");
  const monthLabel = $("calCurrentMonthLabel");
  if (!grid || !monthLabel) return;

  const year = calendarCurrentDate.getFullYear();
  const month = calendarCurrentDate.getMonth();

  const monthNames = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
  ];
  monthLabel.textContent = `${monthNames[month]} ${year}`;

  const selectedAreaId = calendarAreaFilter && calendarAreaFilter.value ? parseInt(calendarAreaFilter.value, 10) : NaN;
  const user = getStoredUser();

  const firstDayIndex = new Date(year, month, 1).getDay();
  const totalDays = new Date(year, month + 1, 0).getDate();
  const prevMonthTotalDays = new Date(year, month, 0).getDate();

  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

  let cellsHtml = "";

  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const dayNum = prevMonthTotalDays - i;
    cellsHtml += `
      <div class="calendar-day-cell day-other-month day-past" role="gridcell" aria-disabled="true">
        <div class="calendar-day-header">
          <span class="calendar-day-number">${dayNum}</span>
        </div>
      </div>
    `;
  }

  for (let day = 1; day <= totalDays; day++) {
    const dayDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const isPast = dayDateStr < todayStr;
    const isToday = dayDateStr === todayStr;

    const dayReservations = cachedAllReservations.filter((r) => {
      const matchDate = r.data_reserva === dayDateStr;
      const matchStatus = r.status !== "CANCELADA" && r.status !== "DESBANCADA";
      const matchArea = isNaN(selectedAreaId) || r.area_comum_id === selectedAreaId;
      return matchDate && matchStatus && matchArea;
    });

    let hasMine = false;
    let hasStandby = false;
    let hasConfirmed = false;

    dayReservations.forEach((r) => {
      if (user && r.usuario_id === user.id) hasMine = true;
      if (r.status === "BAIXA_PRIORIDADE") hasStandby = true;
      if (r.status === "CONFIRMADA" || r.status === "EM_USO" || r.status === "CONCLUIDA") hasConfirmed = true;
    });

    let pips = [];
    let pills = [];

    if (hasMine) {
      pips.push(`<span class="calendar-status-pip mine" title="Minha Reserva"></span>`);
    }
    if (hasConfirmed) {
      pips.push(`<span class="calendar-status-pip booked" title="Reserva Confirmada"></span>`);
    }
    if (hasStandby) {
      pips.push(`<span class="calendar-status-pip standby" title="Standby / Baixa Prioridade (Disputável)"></span>`);
    }
    if (!dayReservations.length && !isPast) {
      pips.push(`<span class="calendar-status-pip free" title="Disponível"></span>`);
    }

    dayReservations.slice(0, 2).forEach((r) => {
      let pillClass = "pill-booked";
      let label = r.hora_inicio ? r.hora_inicio.slice(0, 5) : "";
      if (user && r.usuario_id === user.id) {
        pillClass = "pill-mine";
        label = `Minha: ${label}`;
      } else if (r.status === "BAIXA_PRIORIDADE") {
        pillClass = "pill-standby";
        label = `Standby: ${label}`;
      }
      pills.push(`<span class="cal-event-pill ${pillClass}">${escapeHtml(label)}</span>`);
    });

    if (dayReservations.length > 2) {
      pills.push(`<span class="cal-event-pill pill-booked">+${dayReservations.length - 2} mais</span>`);
    }

    const cellClasses = [
      "calendar-day-cell",
      isPast ? "day-past" : "",
      isToday ? "day-today" : "",
    ].filter(Boolean).join(" ");

    cellsHtml += `
      <div class="${cellClasses}" data-date="${dayDateStr}" role="gridcell" tabindex="${isPast ? '-1' : '0'}" onclick="handleCalendarDayClick('${dayDateStr}')">
        <div class="calendar-day-header">
          <span class="calendar-day-number">${day}</span>
          <div class="calendar-day-status-indicator">${pips.join("")}</div>
        </div>
        <div class="calendar-day-events">${pills.join("")}</div>
      </div>
    `;
  }

  const lastDayIndex = new Date(year, month, totalDays).getDay();
  if (lastDayIndex < 6) {
    for (let i = 1; i <= 6 - lastDayIndex; i++) {
      cellsHtml += `
        <div class="calendar-day-cell day-other-month day-past" role="gridcell" aria-disabled="true">
          <div class="calendar-day-header">
            <span class="calendar-day-number">${i}</span>
          </div>
        </div>
      `;
    }
  }

  grid.innerHTML = cellsHtml;
}

window.handleCalendarDayClick = function (dateStr) {
  const now = new Date();
  const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  if (dateStr < todayStr) {
    showToast("Não é possível solicitar reservas para datas retroativas.", "warning");
    return;
  }

  const form = $("formNewReservation");
  if (!form) return;
  form.classList.remove("hidden");

  $("inputReservationDate").value = dateStr;

  const calArea = $("calendarAreaFilter");
  if (calArea && calArea.value) {
    $("selectReservationArea").value = calArea.value;
  }

  if (!$("inputReservationTimeStart").value) $("inputReservationTimeStart").value = "10:00";
  if (!$("inputReservationTimeEnd").value) $("inputReservationTimeEnd").value = "16:00";

  checkReservationPriorityNotice();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
};

// Atualiza a dica visual com horário de abertura e limite de horas da área selecionada
async function checkReservationPriorityNotice() {
  const areaId = parseInt(selectReservationArea.value, 10);
  const dataReserva = inputReservationDate.value;
  const notice = $("reservationPriorityNotice");
  const title = $("priorityNoticeTitle");
  const desc = $("priorityNoticeDesc");
  const iconWrap = $("priorityNoticeIcon");

  if (!notice || !areaId || !dataReserva || isNaN(areaId)) {
    if (notice) notice.classList.add("hidden");
    return;
  }

  try {
    const res = await api(`/api/reservations/priority-check?area_id=${areaId}&data_reserva=${dataReserva}`);
    notice.classList.remove("hidden");
    if (res.tem_prioridade_alta) {
      notice.className = "reservation-priority-notice alta";
      iconWrap.innerHTML = icon("check");
      title.textContent = "Prioridade Regular Disponível";
      desc.textContent = res.mensagem;
    } else {
      notice.className = "reservation-priority-notice standby";
      iconWrap.innerHTML = icon("clock");
      title.textContent = "Agendamento em Standby (Baixa Prioridade)";
      desc.textContent = res.mensagem;
    }
  } catch (err) {
    notice.classList.add("hidden");
  }
}

selectReservationArea.addEventListener("change", () => {
  const areaId = parseInt(selectReservationArea.value, 10);
  const area = cachedCommonAreas.find((a) => a.id === areaId);
  if (!area) {
    areaRulesHint.classList.add("hidden");
    $("reservationPriorityNotice").classList.add("hidden");
    return;
  }

  const hIni = area.hora_inicio ? area.hora_inicio.substring(0, 5) : "08:00";
  const hFim = area.hora_fim ? area.hora_fim.substring(0, 5) : "22:00";
  const maxH = area.duracao_maxima_horas || 4;
  const interv = area.intervalo_dias_prioridade || 30;

  areaRulesHintText.textContent = `Regras de uso: Horário ${hIni} às ${hFim} | Duração máxima: ${maxH}h | Intervalo de prioridade regular: ${interv} dias.`;
  areaRulesHint.classList.remove("hidden");

  // Sugere horário inicial padrão se vazio
  if (!inputReservationTimeStart.value) inputReservationTimeStart.value = hIni;

  checkReservationPriorityNotice();
});

inputReservationDate.addEventListener("change", () => {
  checkReservationPriorityNotice();
});

// Elementos do cadastro de nova área comum
const btnToggleNewAreaForm = $("btnToggleNewAreaForm");
const formNewArea = $("formNewArea");
const btnCancelNewArea = $("btnCancelNewArea");

if (btnToggleNewAreaForm) {
  btnToggleNewAreaForm.addEventListener("click", () => {
    formNewArea.classList.toggle("hidden");
    if (!formNewArea.classList.contains("hidden")) {
      formNewArea.scrollIntoView({ behavior: "smooth", block: "start" });
      $("inputNewAreaNome").focus();
    }
  });
}
if (btnCancelNewArea) {
  btnCancelNewArea.addEventListener("click", () => {
    formNewArea.classList.add("hidden");
    formNewArea.reset();
  });
}

if (formNewArea) {
  formNewArea.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nome = $("inputNewAreaNome").value.trim();
    const capacidade = parseInt($("inputNewAreaCapacidade").value, 10);
    const taxa = parseFloat($("inputNewAreaTaxa").value) || 0.0;
    const horaInicio = $("inputNewAreaHoraIni").value;
    const horaFim = $("inputNewAreaHoraFim").value;
    const maxHoras = parseInt($("inputNewAreaMaxHoras").value, 10);
    const intervalo = parseInt($("inputNewAreaIntervalo").value, 10) || 30;
    const maxAtivas = parseInt($("inputNewAreaMaxAtivas").value, 10) || 2;
    const prazoStandby = parseInt($("inputNewAreaPrazoStandby").value, 10) || 48;

    if (horaInicio >= horaFim) {
      showToast("O horário de abertura deve ser menor que o de encerramento.", "error");
      return;
    }

    try {
      await api("/api/reservations/areas", {
        method: "POST",
        body: {
          nome,
          capacidade_pessoas: capacidade,
          taxa_limpeza: taxa,
          hora_inicio: horaInicio,
          hora_fim: horaFim,
          duracao_maxima_horas: maxHoras,
          intervalo_dias_prioridade: intervalo,
          max_reservas_ativas: maxAtivas,
          prazo_standby_horas: prazoStandby
        }
      });
      showToast("Novo espaço cadastrado com sucesso!", "success");
      formNewArea.reset();
      formNewArea.classList.add("hidden");
      await populateReservationAreasSelect();
      await loadAreasManagementList();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

// Painel do Síndico: Gerenciamento Modular das Áreas
async function loadAreasManagementList() {
  areasCardsList.innerHTML = `<p class="muted">Carregando áreas comuns do condomínio...</p>`;
  try {
    const areas = await api("/api/reservations/areas?include_inactive=true");
    cachedCommonAreas = areas;

    if (!areas.length) {
      areasCardsList.innerHTML = `<p class="muted">Nenhuma área comum cadastrada.</p>`;
      return;
    }

    areasCardsList.innerHTML = areas.map((a) => {
      const hIni = a.hora_inicio ? a.hora_inicio.substring(0, 5) : "08:00";
      const hFim = a.hora_fim ? a.hora_fim.substring(0, 5) : "22:00";

      const btnToggle = a.ativo
        ? `<button type="button" class="btn-action-danger" onclick="handleToggleAreaActive(${a.id}, false)">${icon("close")}Desativar área</button>`
        : `<button type="button" class="btn-action-deliver" onclick="handleToggleAreaActive(${a.id}, true)">${icon("check")}Ativar área</button>`;

      return `
        <div class="area-manage-card" id="areaCard-${a.id}">
          <div class="area-manage-card-header">
            <div>
              <h5>${escapeHtml(a.nome)}</h5>
              <p class="area-manage-card-desc">Capacidade: ${escapeHtml(a.capacidade_pessoas)} pessoas | Taxa: R$ ${Number(a.taxa_limpeza).toFixed(2)}</p>
            </div>
            <span class="badge-status ${a.ativo ? 'ocupado' : 'falha'}">${a.ativo ? 'Ativo' : 'Desativado'}</span>
          </div>

          <div class="area-manage-fields">
            <div class="area-field-item">
              <label for="areaHoraIni-${a.id}">Abre às:</label>
              <input type="time" id="areaHoraIni-${a.id}" value="${hIni}" />
            </div>
            <div class="area-field-item">
              <label for="areaHoraFim-${a.id}">Fecha às:</label>
              <input type="time" id="areaHoraFim-${a.id}" value="${hFim}" />
            </div>
            <div class="area-field-item">
              <label for="areaMaxHoras-${a.id}">Máx. Horas:</label>
              <input type="number" id="areaMaxHoras-${a.id}" min="1" max="24" value="${a.duracao_maxima_horas || 4}" />
            </div>
            <div class="area-field-item">
              <label for="areaCapacidade-${a.id}">Capacidade:</label>
              <input type="number" id="areaCapacidade-${a.id}" min="1" value="${a.capacidade_pessoas}" />
            </div>
            <div class="area-field-item">
              <label for="areaIntervalo-${a.id}">Intervalo Prioridade (dias):</label>
              <input type="number" id="areaIntervalo-${a.id}" min="1" max="365" value="${a.intervalo_dias_prioridade || 30}" title="Carência entre reservas com prioridade regular" />
            </div>
            <div class="area-field-item">
              <label for="areaMaxAtivas-${a.id}">Máx. Reservas Ativas:</label>
              <input type="number" id="areaMaxAtivas-${a.id}" min="1" max="10" value="${a.max_reservas_ativas || 2}" title="Limite de reservas ativas por morador" />
            </div>
            <div class="area-field-item">
              <label for="areaPrazoStandby-${a.id}">Corte Standby (h antes):</label>
              <input type="number" id="areaPrazoStandby-${a.id}" min="1" max="168" value="${a.prazo_standby_horas || 48}" title="Horas de antecedência para confirmação definitiva do standby" />
            </div>
          </div>

          <div class="area-manage-card-actions">
            ${btnToggle}
            <button type="button" class="btn-primary-sm" onclick="handleSaveAreaRules(${a.id})">Salvar regras</button>
          </div>
        </div>`;
    }).join("");
  } catch (err) {
    areasCardsList.innerHTML = `<p class="table-error">${escapeHtml(err.message)}</p>`;
  }
}

window.handleToggleAreaActive = async function (areaId, activate) {
  const confirmed = await showCustomConfirm({
    title: activate ? "Reativar Área Comum" : "Desativar Área Comum",
    message: activate
      ? "Deseja reativar este espaço comum para agendamentos?"
      : "Ao desativar este espaço, novos agendamentos não poderão ser feitos por moradores. Confirmar?",
    confirmText: activate ? "Sim, Reativar" : "Sim, Desativar",
    cancelText: "Voltar",
    isDanger: !activate,
    iconName: activate ? "check" : "trash"
  });

  if (!confirmed) return;

  try {
    await api(`/api/reservations/areas/${areaId}`, {
      method: "PUT",
      body: { ativo: activate }
    });
    showToast(`Espaço ${activate ? "reativado" : "desativado"} com sucesso.`, "success");
    await populateReservationAreasSelect();
    await loadAreasManagementList();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleSaveAreaRules = async function (areaId) {
  const horaInicio = $(`areaHoraIni-${areaId}`).value;
  const horaFim = $(`areaHoraFim-${areaId}`).value;
  const duracaoMaxima = parseInt($(`areaMaxHoras-${areaId}`).value, 10);
  const capacidade = parseInt($(`areaCapacidade-${areaId}`).value, 10);
  const intervalo = parseInt($(`areaIntervalo-${areaId}`).value, 10);
  const maxAtivas = parseInt($(`areaMaxAtivas-${areaId}`).value, 10);
  const prazoStandby = parseInt($(`areaPrazoStandby-${areaId}`).value, 10);

  if (!horaInicio || !horaFim) {
    showToast("Informe o horário de abertura e fechamento.", "error");
    return;
  }

  if (horaInicio >= horaFim) {
    showToast("O horário de abertura deve ser menor que o de fechamento.", "error");
    return;
  }

  try {
    await api(`/api/reservations/areas/${areaId}`, {
      method: "PUT",
      body: {
        hora_inicio: horaInicio,
        hora_fim: horaFim,
        duracao_maxima_horas: duracaoMaxima,
        capacidade_pessoas: capacidade,
        intervalo_dias_prioridade: intervalo,
        max_reservas_ativas: maxAtivas,
        prazo_standby_horas: prazoStandby
      }
    });
    showToast("Regras, horários e prioridades atualizados com sucesso!", "success");
    await populateReservationAreasSelect();
    await loadAreasManagementList();
  } catch (err) {
    showToast(err.message, "error");
  }
};

formNewReservation.addEventListener("submit", async (e) => {
  e.preventDefault();
  const areaId = parseInt(selectReservationArea.value, 10);
  const dataReserva = inputReservationDate.value;
  const horaInicio = inputReservationTimeStart.value;
  const horaFim = inputReservationTimeEnd.value;
  const observacoes = $("inputReservationObs").value.trim();

  if (!areaId || !dataReserva || !horaInicio || !horaFim) {
    showToast("Selecione a área comum, a data e os horários de início e término.", "error");
    return;
  }

  if (horaInicio >= horaFim) {
    showToast("O horário de início deve ser anterior ao horário de término.", "error");
    return;
  }

  try {
    const created = await api("/api/reservations", {
      method: "POST",
      body: {
        area_comum_id: areaId,
        data_reserva: dataReserva,
        hora_inicio: horaInicio,
        hora_fim: horaFim,
        observacoes: observacoes || null
      },
    });
    formNewReservation.reset();
    formNewReservation.classList.add("hidden");
    areaRulesHint.classList.add("hidden");
    if ($("reservationPriorityNotice")) $("reservationPriorityNotice").classList.add("hidden");
    const msg = created.status === "BAIXA_PRIORIDADE"
      ? "Solicitação registrada em Standby (Baixa Prioridade). A vaga torna-se definitiva caso não haja pedido prioritário até 48h antes."
      : "Reserva confirmada com sucesso com Prioridade Regular!";
    showToast(msg, "success");
    loadReservations();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
});

async function loadReservations() {
  const user = getStoredUser();
  if (!user) return;
  const isMorador = user.tipo_usuario === "MORADOR";
  const isAdmin = isAdminRole(user);

  if (isMorador) {
    $("windowReservationsSub").textContent =
      "Cronograma de áreas comuns. Reservas de vizinhos são exibidas com privacidade (LGPD).";
  } else if (user.tipo_usuario === "PORTARIA") {
    $("windowReservationsSub").textContent =
      "Controle de acesso e entrega de chaves para os espaços comuns reservados pelos condôminos.";
  } else {
    $("windowReservationsSub").textContent =
      "Gestão unificada de regras, prioridades, horários e controle de chaves do condomínio.";
  }

  if (!cachedCommonAreas.length) {
    await populateReservationAreasSelect();
  }

  checkActiveSlotOffers(user);
  reservationsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Carregando agendamentos...</td></tr>`;

  try {
    const reservas = await api("/api/reservations");
    cachedAllReservations = reservas;
    renderReservationsCalendar();

    if (!reservas.length) {
      reservationsTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Nenhum agendamento registrado no momento.</td></tr>`;
      return;
    }

    const isStaff = user.tipo_usuario === "PORTARIA" || isAdmin;

    reservationsTableBody.innerHTML = reservas.map((r) => {
      const data = new Date(`${r.data_reserva}T00:00:00`).toLocaleDateString("pt-BR");
      const hIni = r.hora_inicio ? r.hora_inicio.substring(0, 5) : "--:--";
      const hFim = r.hora_fim ? r.hora_fim.substring(0, 5) : "--:--";
      const periodo = `${data} <span class="muted font-mono">(${hIni} às ${hFim})</span>`;

      const confirmada = r.status === "CONFIRMADA";
      let status = "";
      if (confirmada) {
        status = `<span class="badge-status ocupado" title="Reserva com data confirmada">${icon("check")}Confirmada</span>`;
      } else if (r.status === "BAIXA_PRIORIDADE") {
        status = `<span class="badge-status standby" title="Em Standby. Vira definitiva se nenhum morador prioritário solicitar até 48h antes">${icon("clock")}Standby (48h)</span>`;
      } else if (r.status === "OFERTA_RETOMADA") {
        status = `<span class="badge-status retomada" title="Direito de Preferência: Vaga desimpedida para você!">${icon("zap")}Vaga Liberada (24h)</span>`;
      } else if (r.status === "DESBANCADA") {
        status = `<span class="badge-status desbancada" title="Data cedida para condômino com prioridade regular">${icon("close")}Vaga cedida</span>`;
      } else if (r.status === "CANCELADA") {
        status = `<span class="badge-status cancelado">Cancelada</span>`;
      } else {
        status = `<span class="badge-status vago">${escapeHtml(r.status)}</span>`;
      }

      let solicitante;
      if (r.is_mine) {
        solicitante = `<strong>${escapeHtml(r.morador_nome)} (${escapeHtml(r.unidade_desc)})</strong><span class="badge-status mine">Sua reserva</span>`;
      } else if (isMorador) {
        solicitante = `<span class="privacy-note">${icon("lock")}${escapeHtml(r.morador_nome)}</span>`;
      } else {
        solicitante = `<strong>${escapeHtml(r.morador_nome)}</strong> (${escapeHtml(r.unidade_desc)})`;
      }

      // Controle de entrega/devolução de chave
      let chaveStatus = "";
      if (r.chave_devolvida) {
        const devEm = r.chave_devolvida_em ? new Date(r.chave_devolvida_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        chaveStatus = `<span class="badge-status entregue" title="Chave devolvida às ${devEm}">${icon("check")}Chave devolvida</span>`;
      } else if (r.chave_entregue) {
        const entEm = r.chave_entregue_em ? new Date(r.chave_entregue_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        chaveStatus = `<div><span class="badge-status pendente" title="Entregue às ${entEm}">${icon("key")}Com: ${escapeHtml(r.chave_entregue_para || "Morador")}</span>`;
        if (isStaff && confirmada) {
          chaveStatus += ` <button type="button" class="btn-action-deliver" onclick="handleReturnKey(${Number(r.id)})" title="Registrar devolução da chave">Receber chave</button>`;
        }
        chaveStatus += `</div>`;
      } else {
        chaveStatus = `<span class="badge-status vago">Na portaria</span>`;
        if (isStaff && confirmada) {
          chaveStatus += ` <button type="button" class="btn-action-deliver" onclick="handleHandoverKey(${Number(r.id)})" title="Registrar para quem a chave foi entregue">${icon("key")}Entregar chave</button>`;
        }
      }

      let acoesList = [];
      const podeGerenciarConvidados = (confirmada || r.status === "BAIXA_PRIORIDADE" || r.status === "OFERTA_RETOMADA") && (r.is_mine || isStaff);
      if (podeGerenciarConvidados) {
        acoesList.push(`<button type="button" class="btn-action-guest" onclick="openGuestsModal(${Number(r.id)}, '${escapeHtml(r.area_nome || '')}', '${escapeHtml(data)}', ${r.is_mine ? 'true' : 'false'})" title="Gerenciar convidados do evento">${icon("users")}Convidados (${r.total_convidados || 0})</button>`);
      }

      if (r.status === "OFERTA_RETOMADA" && r.is_mine) {
        acoesList.push(`<button type="button" class="btn-action-deliver" onclick="handleAcceptOffer(${Number(r.id)})" title="Confirmar e garantir sua vaga">${icon("check")}Confirmar</button>`);
        acoesList.push(`<button type="button" class="btn-action-danger" onclick="handleDeclineOffer(${Number(r.id)})" title="Dispensar direito de preferência">Dispensar</button>`);
      }

      const chaveRetirada = r.chave_entregue || r.chave_devolvida;
      const podeCancelar = (confirmada || r.status === "BAIXA_PRIORIDADE") && !chaveRetirada && (r.is_mine || isAdminRole(user));
      if (podeCancelar) {
        acoesList.push(`<button type="button" class="btn-action-danger" onclick="handleCancelReservation(${Number(r.id)})">Cancelar</button>`);
      }

      const acao = acoesList.length ? `<div style="display:flex; gap:0.35rem; align-items:center; flex-wrap:wrap;">${acoesList.join(" ")}</div>` : `<span class="muted">-</span>`;

      return `
        <tr>
          <td data-label="Espaço">
            <strong>${escapeHtml(r.area_nome)}</strong>
            <small class="muted">${data} (${hIni} às ${hFim})</small>
          </td>
          <td data-label="Data e Período">${periodo}</td>
          <td data-label="Solicitante">${solicitante}</td>
          <td data-label="Status">${status}</td>
          <td data-label="Chaves">${chaveStatus}</td>
          <td data-label="Ações">${acao}</td>
        </tr>`;
    }).join("");
  } catch (err) {
    reservationsTableBody.innerHTML = `<tr><td colspan="6" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

window.handleHandoverKey = async function (reservationId) {
  const entreguePara = await showCustomPrompt({
    title: "Entrega de Chave de Espaço",
    message: "Registre a entrega da chave ou tag de acesso à área reservada.",
    label: "Nome do morador ou responsável retirando a chave:",
    placeholder: "Ex: Roberto Souza",
    confirmText: "Registrar Entrega",
    cancelText: "Voltar",
    iconName: "key"
  });

  if (entreguePara === null) return;
  if (!entreguePara.trim()) {
    showToast("Por favor, informe o nome de quem retirou a chave.", "error");
    return;
  }

  try {
    await api(`/api/reservations/${reservationId}/handover-key`, {
      method: "PUT",
      body: { entregue_para: entreguePara.trim() }
    });
    showToast("Entrega de chave registrada com sucesso no sistema.", "success");
    loadReservations();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleReturnKey = async function (reservationId) {
  const confirmed = await showCustomConfirm({
    title: "Devolução de Chave",
    message: "Confirmar que a chave deste espaço foi devolvida na portaria?",
    confirmText: "Confirmar Devolução",
    cancelText: "Voltar",
    isDanger: false,
    iconName: "key"
  });

  if (!confirmed) return;

  try {
    await api(`/api/reservations/${reservationId}/return-key`, {
      method: "PUT"
    });
    showToast("Devolução da chave registrada com sucesso.", "success");
    loadReservations();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleCancelReservation = async function (reservationId) {
  const confirmed = await showCustomConfirm({
    title: "Cancelar Reserva",
    message: "Tem certeza que deseja cancelar esta reserva? Esta ação liberará a data para outros condôminos.",
    confirmText: "Sim, Cancelar Reserva",
    cancelText: "Manter Reserva",
    isDanger: true,
    iconName: "trash"
  });

  if (!confirmed) return;

  try {
    await api(`/api/reservations/${reservationId}/cancel`, { method: "PUT" });
    showToast("Reserva cancelada com sucesso.", "success");
    loadReservations();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 9. MURAL DE AVISOS
// ==========================================
const formNewNotice = $("formNewNotice");
const noticesContainer = $("noticesContainer");

const CATEGORY_LABEL = {
  URGENTE: "Urgente",
  MANUTENCAO: "Manutenção",
  ASSEMBLEIA: "Assembleia",
  GERAL: "Geral",
};

$("btnToggleNewNoticeForm").addEventListener("click", () => {
  formNewNotice.classList.toggle("hidden");
  if (!formNewNotice.classList.contains("hidden")) {
    formNewNotice.scrollIntoView({ behavior: "smooth", block: "start" });
    $("inputNoticeTitle").focus();
  }
});
$("btnCancelNewNotice").addEventListener("click", () => {
  formNewNotice.classList.add("hidden");
  formNewNotice.reset();
});

function formatMessageWithLinks(text) {
  const escaped = escapeHtml(text);
  const urlRegex = /(https?:\/\/[^\s<]+)/g;
  return escaped.replace(urlRegex, (url) => {
    return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
}

formNewNotice.addEventListener("submit", async (e) => {
  e.preventDefault();
  const titulo = $("inputNoticeTitle").value.trim();
  const categoria = $("selectNoticeCategory").value;
  const mensagem = $("inputNoticeMessage").value.trim();
  const linkAnexo = $("inputNoticeLink") ? $("inputNoticeLink").value.trim() : "";
  const btnSubmit = formNewNotice.querySelector("button[type='submit']");

  if (!titulo || titulo.length < 3) {
    showToast("O título do comunicado deve ter no mínimo 3 caracteres.", "error");
    $("inputNoticeTitle").focus();
    return;
  }

  if (!mensagem || mensagem.length < 5) {
    showToast("A mensagem do comunicado deve ter no mínimo 5 caracteres.", "error");
    $("inputNoticeMessage").focus();
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.textContent = "Publicando...";
  }

  try {
    await api("/api/notices", {
      method: "POST",
      body: {
        titulo,
        categoria,
        mensagem,
        link_anexo: linkAnexo || null
      }
    });
    showToast("Comunicado publicado para todos os moradores.", "success");
    formNewNotice.reset();
    formNewNotice.classList.add("hidden");
    loadNotices();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.textContent = "Publicar para todos";
    }
  }
});

async function loadNotices() {
  const admin = isAdminRole(getStoredUser());
  noticesContainer.innerHTML = `<p class="table-empty">Carregando comunicados...</p>`;

  try {
    const notices = await api("/api/notices");
    const stat = $("statAvisos");
    if (stat) stat.textContent = notices.length;

    if (!notices.length) {
      noticesContainer.innerHTML = `
        <div class="notice-empty">
          <strong>Nenhum comunicado cadastrado no momento.</strong>
          Avisos publicados pela administração aparecerão neste mural.
        </div>`;
      return;
    }

    noticesContainer.innerHTML = notices.map((n) => {
      const cat = (n.categoria || "GERAL").toLowerCase();
      const label = CATEGORY_LABEL[n.categoria] || n.categoria;
      const data = new Date(n.criado_em).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
      const excluir = admin
        ? `<button type="button" class="btn-action-danger" onclick="handleDeleteNotice(${Number(n.id)})">${icon("trash")}Excluir</button>`
        : "";

      let linkHtml = "";
      if (n.link_anexo) {
        const urlLower = n.link_anexo.toLowerCase();
        let linkClass = "";
        let linkIcon = "link";
        let linkLabel = "Acessar link da reunião ou vídeo";

        if (urlLower.includes("meet.google.com")) {
          linkClass = "meet";
          linkIcon = "video";
          linkLabel = "Entrar na Reunião (Google Meet)";
        } else if (urlLower.includes("zoom.us")) {
          linkClass = "meet";
          linkIcon = "video";
          linkLabel = "Entrar na Reunião (Zoom)";
        } else if (urlLower.includes("teams.microsoft.com") || urlLower.includes("teams.live.com")) {
          linkClass = "meet";
          linkIcon = "video";
          linkLabel = "Entrar na Reunião (Microsoft Teams)";
        } else if (urlLower.includes("youtube.com") || urlLower.includes("youtu.be")) {
          linkClass = "video";
          linkIcon = "video";
          linkLabel = "Assistir ao Vídeo (YouTube)";
        }

        linkHtml = `
          <div class="notice-link-attachment">
            <a href="${escapeHtml(n.link_anexo)}" target="_blank" rel="noopener noreferrer" class="notice-link-btn ${linkClass}">
              ${icon(linkIcon, "ico ico-sm")}
              <span>${escapeHtml(linkLabel)}</span>
            </a>
          </div>`;
      }

      return `
        <article class="notice-card ${escapeHtml(cat)}">
          <div class="notice-header-row">
            <span class="notice-cat-badge ${escapeHtml(cat)}">${escapeHtml(label)}</span>
            <span class="notice-date">${data}</span>
          </div>
          <h4 class="notice-title">${escapeHtml(n.titulo)}</h4>
          <p class="notice-message">${formatMessageWithLinks(n.mensagem)}</p>
          ${linkHtml}
          <div class="notice-footer">
            <span>Publicado por <strong>${escapeHtml(n.autor_nome || "Administração")}</strong></span>
            ${excluir}
          </div>
        </article>`;
    }).join("");
  } catch (err) {
    noticesContainer.innerHTML = `<p class="table-error">${escapeHtml(err.message)}</p>`;
  }
}

window.handleDeleteNotice = async function (noticeId) {
  const confirmed = await showCustomConfirm({
    title: "Excluir Comunicado",
    message: "Tem certeza que deseja excluir permanentemente este comunicado oficial do mural?",
    confirmText: "Sim, Excluir",
    cancelText: "Cancelar",
    isDanger: true,
    iconName: "trash"
  });

  if (!confirmed) return;

  try {
    await api(`/api/notices/${noticeId}`, { method: "DELETE" });
    showToast("Comunicado excluído com sucesso.", "success");
    loadNotices();
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 10. AUDITORIA E SEGURANÇA OPERACIONAL
// ==========================================
const auditTableBody = $("auditTableBody");

$("btnRefreshAudit").addEventListener("click", loadAuditLogs);

async function loadAuditLogs() {
  auditTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Consultando registros de auditoria e segurança...</td></tr>`;
  try {
    const logs = await api("/api/audit/logs?limit=50");
    $("auditCount").textContent = logs.length;

    if (!logs.length) {
      auditTableBody.innerHTML = `<tr><td colspan="6" class="table-empty">Nenhum registro de auditoria encontrado.</td></tr>`;
      return;
    }

    auditTableBody.innerHTML = logs.map((l) => {
      const dataHora = new Date(l.data_hora).toLocaleString("pt-BR");
      const resultado = l.sucesso
        ? `<span class="badge-status sucesso">Acesso autorizado</span>`
        : `<span class="badge-status falha">Credencial incorreta</span>`;
      const uaRaw = l.user_agent || "N/D";
      const uaShort = uaRaw.length > 38 ? `${uaRaw.substring(0, 35)}...` : uaRaw;

      return `
        <tr>
          <td data-label="Data e Hora">
            <strong>${escapeHtml(dataHora)}</strong>
            <small class="muted">${escapeHtml(l.email_informado)}</small>
          </td>
          <td data-label="Usuário/E-mail">${escapeHtml(l.email_informado)}</td>
          <td data-label="IP"><code>${escapeHtml(l.ip_origem || "127.0.0.1")}</code></td>
          <td data-label="Dispositivo" title="${escapeHtml(uaRaw)}">${escapeHtml(uaShort)}</td>
          <td data-label="Resultado">${resultado}</td>
          <td data-label="Ação"><span class="badge-status procedure">Autenticação Web / API</span></td>
        </tr>`;
    }).join("");
  } catch (err) {
    auditTableBody.innerHTML = `<tr><td colspan="6" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

// ==========================================
// 11. LIVRO DE OCORRÊNCIAS E CHAMADOS
// ==========================================
const ticketsTableBody = $("ticketsTableBody");
const formNewTicket = $("formNewTicket");
const btnNewTicketToggle = $("btnNewTicketToggle");
const filterTicketStatus = $("filterTicketStatus");
const modalReplyTicket = $("modalReplyTicket");
const formReplyTicket = $("formReplyTicket");

if (btnNewTicketToggle) {
  btnNewTicketToggle.addEventListener("click", () => {
    formNewTicket.classList.toggle("hidden");
    if (!formNewTicket.classList.contains("hidden")) {
      formNewTicket.scrollIntoView({ behavior: "smooth", block: "start" });
      $("inputTicketTitulo").focus();
    }
  });
}

const btnCancelTicket = $("btnCancelTicket");
const btnCancelTicket2 = $("btnCancelTicket2");
if (btnCancelTicket) btnCancelTicket.addEventListener("click", () => formNewTicket.classList.add("hidden"));
if (btnCancelTicket2) btnCancelTicket2.addEventListener("click", () => formNewTicket.classList.add("hidden"));

if (filterTicketStatus) {
  filterTicketStatus.addEventListener("change", loadTickets);
}

const btnRefreshTickets = $("btnRefreshTickets");
if (btnRefreshTickets) {
  btnRefreshTickets.addEventListener("click", loadTickets);
}

if (formNewTicket) {
  formNewTicket.addEventListener("submit", async (e) => {
    e.preventDefault();
    const titulo = $("inputTicketTitulo").value.trim();
    const categoria = $("selectTicketCategoria").value;
    const descricao = $("inputTicketDescricao").value.trim();

    if (!titulo || !descricao) {
      showToast("Preencha o título e a descrição da ocorrência.", "error");
      return;
    }

    try {
      await api("/api/tickets", {
        method: "POST",
        body: { titulo, categoria, descricao },
      });
      formNewTicket.reset();
      formNewTicket.classList.add("hidden");
      showToast("Ocorrência registrada com sucesso. A administração foi notificada.", "success");
      loadTickets();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

async function loadTickets() {
  if (!ticketsTableBody) return;
  const user = getStoredUser();
  if (!user) return;

  const statusFilter = filterTicketStatus ? filterTicketStatus.value : "";
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";

  ticketsTableBody.innerHTML = `<tr><td colspan="7" class="table-empty">Carregando ocorrências e chamados...</td></tr>`;

  try {
    const tickets = await api(`/api/tickets${query}`);
    if (!tickets.length) {
      ticketsTableBody.innerHTML = `<tr><td colspan="7" class="table-empty">Nenhum chamado encontrado com os filtros atuais.</td></tr>`;
      return;
    }

    const isAdmin = isAdminRole(user);

    ticketsTableBody.innerHTML = tickets.map((t) => {
      const dataCriacao = new Date(t.criado_em).toLocaleDateString("pt-BR", {
        day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
      });

      let statusBadge = `<span class="badge-status pendente">Em aberto</span>`;
      if (t.status === "EM_ANALISE") statusBadge = `<span class="badge-status analise">Em análise</span>`;
      else if (t.status === "CONCLUIDO") statusBadge = `<span class="badge-status concluido">Concluído</span>`;
      else if (t.status === "CANCELADO") statusBadge = `<span class="badge-status cancelado">Cancelado</span>`;

      const catLabels = {
        BARULHO: "Barulho",
        MANUTENCAO: "Manutenção",
        VAZAMENTO: "Vazamento",
        SEGURANCA: "Segurança",
        OUTROS: "Geral / Outros",
      };
      const catLabel = catLabels[t.categoria] || t.categoria;

      let parecerHtml = `<span class="muted">Aguardando análise</span>`;
      if (t.resposta_sindico) {
        const respEm = t.respondido_em
          ? new Date(t.respondido_em).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })
          : "";
        parecerHtml = `
          <div class="ticket-reply-box">
            <div>${escapeHtml(t.resposta_sindico)}</div>
            <span class="ticket-reply-meta">Parecer por: ${escapeHtml(t.respondido_por_nome || "Síndico")}${respEm ? ` em ${respEm}` : ""}</span>
          </div>`;
      }

      let acoesHtml = `<span class="muted">-</span>`;
      if (isAdmin && t.status !== "CANCELADO") {
        acoesHtml = `
          <button type="button" class="btn-action-primary" onclick="openReplyTicketModal(${t.id}, '${escapeHtml(t.status)}', '${escapeHtml(t.resposta_sindico || '')}')">
            ${icon("clipboard")}Dar Parecer
          </button>`;
      } else if (!isAdmin && t.is_mine && t.status === "ABERTO") {
        acoesHtml = `
          <button type="button" class="btn-action-danger" onclick="handleCancelTicket(${t.id})">
            ${icon("close")}Cancelar
          </button>`;
      }

      return `
        <tr>
          <td data-label="Assunto">
            <strong>${escapeHtml(t.titulo)}</strong>
            <small class="muted">${escapeHtml(t.unidade_desc)} &bull; ${escapeHtml(t.morador_nome)}</small>
          </td>
          <td data-label="Data"><small>${escapeHtml(dataCriacao)}</small></td>
          <td data-label="Unidade">
            <strong>${escapeHtml(t.unidade_desc)}</strong>
            <br><small class="muted">${escapeHtml(t.morador_nome)}</small>
          </td>
          <td data-label="Categoria"><span class="notice-cat-badge geral">${escapeHtml(catLabel)}</span></td>
          <td data-label="Status">${statusBadge}</td>
          <td data-label="Parecer">${parecerHtml}</td>
          <td data-label="Ações">${acoesHtml}</td>
        </tr>`;
    }).join("");
  } catch (err) {
    ticketsTableBody.innerHTML = `<tr><td colspan="7" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

window.openReplyTicketModal = function (ticketId, currentStatus, currentReply) {
  if (!modalReplyTicket) return;
  $("replyTargetTicketId").value = ticketId;
  $("selectReplyStatus").value = currentStatus === "EM_ANALISE" ? "EM_ANALISE" : "CONCLUIDO";
  $("inputReplyParecer").value = currentReply || "";
  modalReplyTicket.classList.remove("hidden");
  document.body.classList.add("modal-open");
  setTimeout(() => $("inputReplyParecer").focus(), 100);
};

function closeReplyTicketModal() {
  if (modalReplyTicket) modalReplyTicket.classList.add("hidden");
  document.body.classList.remove("modal-open");
}

const btnCancelReplyTicket = $("btnCancelReplyTicket");
const btnCancelReplyTicketX = $("btnCancelReplyTicketX");
if (btnCancelReplyTicket) btnCancelReplyTicket.addEventListener("click", closeReplyTicketModal);
if (btnCancelReplyTicketX) btnCancelReplyTicketX.addEventListener("click", closeReplyTicketModal);

if (formReplyTicket) {
  formReplyTicket.addEventListener("submit", async (e) => {
    e.preventDefault();
    const ticketId = parseInt($("replyTargetTicketId").value, 10);
    const status = $("selectReplyStatus").value;
    const resposta_sindico = $("inputReplyParecer").value.trim();

    if (!ticketId || !resposta_sindico) {
      showToast("Informe o parecer oficial da administração.", "error");
      return;
    }

    try {
      await api(`/api/tickets/${ticketId}/reply`, {
        method: "PUT",
        body: { status, resposta_sindico },
      });
      closeReplyTicketModal();
      showToast("Parecer oficial gravado com sucesso.", "success");
      loadTickets();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

window.handleCancelTicket = async function (ticketId) {
  const confirmed = await showCustomConfirm({
    title: "Cancelar Chamado",
    message: "Tem certeza de que deseja cancelar esta ocorrência? Ela será encerrada sem parecer.",
    confirmText: "Sim, Cancelar Chamado",
    cancelText: "Voltar",
    isDanger: true,
    iconName: "close",
  });

  if (!confirmed) return;

  try {
    await api(`/api/tickets/${ticketId}/cancel`, { method: "PUT" });
    showToast("Ocorrência cancelada com sucesso.", "info");
    loadTickets();
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 12. CONTROLE DE PORTARIA E VISITANTES
// ==========================================
const visitorsTableBody = $("visitorsTableBody");
const formNewVisitor = $("formNewVisitor");
const btnNewVisitorToggle = $("btnNewVisitorToggle");
const selectVisitorUnit = $("selectVisitorUnit");
const filterVisitorStatus = $("filterVisitorStatus");

if (btnNewVisitorToggle) {
  btnNewVisitorToggle.addEventListener("click", async () => {
    formNewVisitor.classList.toggle("hidden");
    if (!formNewVisitor.classList.contains("hidden")) {
      await loadVisitorUnitsSelect();
      const inputData = $("inputVisitorData");
      if (inputData && !inputData.value) {
        inputData.value = new Date().toISOString().split("T")[0];
      }
      formNewVisitor.scrollIntoView({ behavior: "smooth", block: "start" });
      $("inputVisitorNome").focus();
    }
  });
}

const btnCancelVisitor = $("btnCancelVisitor");
const btnCancelVisitor2 = $("btnCancelVisitor2");
if (btnCancelVisitor) btnCancelVisitor.addEventListener("click", () => formNewVisitor.classList.add("hidden"));
if (btnCancelVisitor2) btnCancelVisitor2.addEventListener("click", () => formNewVisitor.classList.add("hidden"));

if (filterVisitorStatus) {
  filterVisitorStatus.addEventListener("change", loadVisitors);
}

const btnRefreshVisitors = $("btnRefreshVisitors");
if (btnRefreshVisitors) {
  btnRefreshVisitors.addEventListener("click", loadVisitors);
}

async function loadVisitorUnitsSelect() {
  if (!selectVisitorUnit) return;
  const user = getStoredUser();
  if (!user) return;
  const groupUnit = $("groupVisitorUnit");

  if (user.tipo_usuario === "MORADOR") {
    if (groupUnit) groupUnit.classList.add("hidden");
    selectVisitorUnit.required = false;
    selectVisitorUnit.innerHTML = `<option value="${user.unidade_id || ''}" selected>Minha residência</option>`;
    return;
  }

  if (groupUnit) groupUnit.classList.remove("hidden");
  selectVisitorUnit.required = true;

  try {
    const units = await api("/api/units");
    selectVisitorUnit.innerHTML =
      `<option value="">Selecione o apartamento de destino...</option>` +
      units.map((u) => {
        const morador = u.morador_responsavel ? ` (${escapeHtml(u.morador_responsavel.nome)})` : " (Disponível)";
        return `<option value="${u.id}">${escapeHtml(u.bloco)} - Apto ${escapeHtml(u.numero)}${morador}</option>`;
      }).join("");
  } catch {
    selectVisitorUnit.innerHTML = `<option value="">Erro ao carregar unidades</option>`;
  }
}

if (formNewVisitor) {
  formNewVisitor.addEventListener("submit", async (e) => {
    e.preventDefault();
    const user = getStoredUser();
    const unidadeIdVal = selectVisitorUnit.value ? parseInt(selectVisitorUnit.value, 10) : (user ? user.unidade_id : null);
    const nome = $("inputVisitorNome").value.trim();
    const documento = $("inputVisitorDoc").value.trim() || null;
    const tipo = $("selectVisitorTipo").value;
    const dataPrevista = $("inputVisitorData").value;
    const observacoes = $("inputVisitorObs").value.trim() || null;

    if (!nome || !dataPrevista || (user && user.tipo_usuario !== "MORADOR" && !unidadeIdVal)) {
      showToast("Preencha todos os campos obrigatórios.", "error");
      return;
    }

    try {
      await api("/api/visitors", {
        method: "POST",
        body: {
          unidade_id: unidadeIdVal,
          nome,
          documento,
          tipo,
          data_prevista: dataPrevista,
          observacoes,
        },
      });
      formNewVisitor.reset();
      formNewVisitor.classList.add("hidden");
      showToast("Autorização salva com sucesso.", "success");
      loadVisitors();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

async function loadVisitors() {
  if (!visitorsTableBody) return;
  const user = getStoredUser();
  if (!user) return;

  const statusFilter = filterVisitorStatus ? filterVisitorStatus.value : "";
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";

  visitorsTableBody.innerHTML = `<tr><td colspan="9" class="table-empty">Carregando controle de portaria...</td></tr>`;

  try {
    const visitors = await api(`/api/visitors${query}`);
    if (!visitors.length) {
      visitorsTableBody.innerHTML = `<tr><td colspan="9" class="table-empty">Nenhum registro de visitante encontrado com os filtros atuais.</td></tr>`;
      return;
    }

    const isStaff = isAdminRole(user) || user.tipo_usuario === "PORTARIA";

    visitorsTableBody.innerHTML = visitors.map((v) => {
      const dataPrevista = new Date(v.data_prevista + "T00:00:00").toLocaleDateString("pt-BR");

      let statusBadge = `<span class="badge-status pendente">Aguardando</span>`;
      if (v.status === "NO_LOCAL") statusBadge = `<span class="badge-status nolocal">No condomínio</span>`;
      else if (v.status === "FINALIZADO") statusBadge = `<span class="badge-status finalizado">Finalizado</span>`;
      else if (v.status === "CANCELADO") statusBadge = `<span class="badge-status cancelado">Cancelado</span>`;

      const tipoLabels = {
        VISITANTE: "Visitante",
        PRESTADOR_SERVICO: "Prestador",
        DELIVERY: "Delivery",
      };
      const tipoLabel = tipoLabels[v.tipo] || v.tipo;

      const entrada = v.hora_entrada
        ? new Date(v.hora_entrada).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
        : `<span class="muted">-</span>`;
      const saida = v.hora_saida
        ? new Date(v.hora_saida).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
        : `<span class="muted">-</span>`;

      let acoes = `<span class="muted">-</span>`;
      if (isStaff) {
        if (v.status === "AGUARDANDO") {
          acoes = `
            <button type="button" class="btn-action-deliver" onclick="handleVisitorEntry(${v.id}, '${escapeHtml(v.nome)}')">
              ${icon("check")}Entrada
            </button>`;
        } else if (v.status === "NO_LOCAL") {
          acoes = `
            <button type="button" class="btn-action-warning" onclick="handleVisitorExit(${v.id}, '${escapeHtml(v.nome)}')">
              ${icon("arrow")}Saída
            </button>`;
        }
      }

      if (v.status === "AGUARDANDO" && (v.is_my_unit || isAdminRole(user))) {
        if (!isStaff) {
          acoes = `
            <button type="button" class="btn-action-danger" onclick="handleCancelVisitor(${v.id})">
              ${icon("close")}Cancelar
            </button>`;
        }
      }

      const docStr = v.documento ? `<code>${escapeHtml(v.documento)}</code>` : `<span class="muted">-</span>`;
      const obsStr = v.observacoes ? `<br><small class="muted">${escapeHtml(v.observacoes)}</small>` : "";

      return `
        <tr>
          <td data-label="Visitante">
            <strong>${escapeHtml(v.nome)}</strong>
            <small class="muted">${escapeHtml(v.unidade_desc)} &bull; ${escapeHtml(tipoLabel)}</small>
          </td>
          <td data-label="Data"><strong>${escapeHtml(dataPrevista)}</strong></td>
          <td data-label="Destino">${escapeHtml(v.unidade_desc)}</td>
          <td data-label="Documento">${docStr}</td>
          <td data-label="Tipo"><span class="notice-cat-badge manutencao">${escapeHtml(tipoLabel)}</span></td>
          <td data-label="Status">${statusBadge}</td>
          <td data-label="Entrada">${entrada}</td>
          <td data-label="Saída">${saida}</td>
          <td data-label="Ações">${acoes}</td>
        </tr>`;
    }).join("");
  } catch (err) {
    visitorsTableBody.innerHTML = `<tr><td colspan="9" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }

  // Atualiza também a tabela de convidados de eventos do dia
  loadTodayGuests();
}

async function loadTodayGuests() {
  const tbody = $("todayGuestsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="5" class="table-empty">Carregando convidados dos eventos de hoje...</td></tr>`;

  try {
    const guests = await api("/api/guests/today");
    if (!guests || !guests.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="table-empty">Nenhum evento com convidados agendados para hoje.</td></tr>`;
      return;
    }

    const user = getStoredUser();
    const isStaff = isAdminRole(user) || (user && user.tipo_usuario === "PORTARIA");

    tbody.innerHTML = guests.map((g) => {
      let statusBadge = `<span class="badge-guest-waiting">Aguardando chegada</span>`;
      if (g.saida_registrada) {
        const outTime = g.saida_em ? new Date(g.saida_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        statusBadge = `<span class="badge-guest-exited">${icon("arrow")}Saída (${outTime})</span>`;
      } else if (g.entrada_registrada) {
        const inTime = g.entrada_em ? new Date(g.entrada_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        statusBadge = `<span class="badge-guest-entered">${icon("check")}Presente (${inTime})</span>`;
      }

      const destino = `<strong>${escapeHtml(g.area_nome || "Espaço Comum")}</strong><br><small class="muted">Apto ${escapeHtml(g.bloco || "")}-${escapeHtml(g.numero || "")} &bull; ${escapeHtml(g.morador_nome || "")}</small>`;
      const horario = `${g.hora_inicio ? g.hora_inicio.slice(0, 5) : "--:--"} às ${g.hora_fim ? g.hora_fim.slice(0, 5) : "--:--"}`;
      const doc = g.documento ? `<br><small class="muted">Doc: ${escapeHtml(g.documento)}</small>` : "";

      let acao = `<span class="muted">-</span>`;
      if (isStaff) {
        if (!g.entrada_registrada) {
          acao = `<button type="button" class="btn-action-deliver" onclick="handleTodayGuestCheckin(${g.id}, '${escapeHtml(g.nome_completo)}')">${icon("check")}Entrada</button>`;
        } else if (!g.saida_registrada) {
          acao = `<button type="button" class="btn-action-checkout" onclick="handleTodayGuestCheckout(${g.id}, '${escapeHtml(g.nome_completo)}')">${icon("arrow")}Registrar Saída</button>`;
        } else {
          acao = `<span class="badge-guest-waiting">Finalizado</span>`;
        }
      }

      return `
        <tr>
          <td data-label="Convidado">
            <strong>${escapeHtml(g.nome_completo)}</strong>
            <small class="muted">${escapeHtml(g.area_nome || "Espaço Comum")} &bull; ${horario}</small>
          </td>
          <td data-label="Evento / Destino">${destino}</td>
          <td data-label="Horário">${horario}</td>
          <td data-label="Status">${statusBadge}</td>
          <td data-label="Ação"><div style="display:flex; gap:0.35rem; align-items:center;">${acao}</div></td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

window.handleTodayGuestCheckin = async function (guestId, nome) {
  try {
    await api(`/api/guests/${guestId}/checkin`, { method: "PUT" });
    showToast(`Entrada de "${nome}" liberada e registrada na guarita!`, "success");
    loadTodayGuests();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleTodayGuestCheckout = async function (guestId, nome) {
  try {
    await api(`/api/guests/${guestId}/checkout`, { method: "PUT" });
    showToast(`Saída de "${nome}" registrada na guarita.`, "info");
    loadTodayGuests();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleVisitorEntry = async function (visitorId, nome) {
  const confirmed = await showCustomConfirm({
    title: "Registrar Entrada na Portaria",
    message: `Confirmar a entrada de "${nome}" no condomínio neste momento?`,
    confirmText: "Confirmar Entrada",
    cancelText: "Voltar",
    iconName: "check",
  });

  if (!confirmed) return;

  try {
    await api(`/api/visitors/${visitorId}/entry`, { method: "PUT" });
    showToast(`Entrada de ${nome} registrada na portaria.`, "success");
    loadVisitors();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleVisitorExit = async function (visitorId, nome) {
  const confirmed = await showCustomConfirm({
    title: "Registrar Saída na Portaria",
    message: `Registrar a saída de "${nome}" do condomínio?`,
    confirmText: "Confirmar Saída",
    cancelText: "Voltar",
    iconName: "arrow",
  });

  if (!confirmed) return;

  try {
    await api(`/api/visitors/${visitorId}/exit`, { method: "PUT" });
    showToast(`Saída de ${nome} registrada. Acesso finalizado.`, "info");
    loadVisitors();
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleCancelVisitor = async function (visitorId) {
  const confirmed = await showCustomConfirm({
    title: "Cancelar Autorização",
    message: "Tem certeza de que deseja cancelar esta autorização de acesso?",
    confirmText: "Sim, Cancelar",
    cancelText: "Voltar",
    isDanger: true,
    iconName: "close",
  });

  if (!confirmed) return;

  try {
    await api(`/api/visitors/${visitorId}/cancel`, { method: "PUT" });
    showToast("Autorização de acesso cancelada com sucesso.", "info");
    loadVisitors();
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 13. ANTI-SABOTAGEM & OFERTAS DE RETOMADA
// ==========================================
async function checkActiveSlotOffers(user) {
  const b1 = $("overviewRecoveryBanner");
  const b2 = $("reservationsRecoveryBanner");

  if (!user || user.tipo_usuario !== "MORADOR") {
    if (b1) b1.classList.add("hidden");
    if (b2) b2.classList.add("hidden");
    return;
  }

  try {
    const offers = await api("/api/reservations/active-offers");
    if (!offers || !offers.length) {
      if (b1) b1.classList.add("hidden");
      if (b2) b2.classList.add("hidden");
      return;
    }

    const offer = offers[0];
    const dataFmt = offer.data_reserva ? new Date(`${offer.data_reserva}T00:00:00`).toLocaleDateString("pt-BR") : "";
    const hIni = offer.hora_inicio ? offer.hora_inicio.substring(0, 5) : "--:--";
    const hFim = offer.hora_fim ? offer.hora_fim.substring(0, 5) : "--:--";
    const areaNome = offer.area_nome || "Área Comum";

    let prazoStr = "24 horas";
    if (offer.oferta_retomada_ate) {
      const ate = new Date(offer.oferta_retomada_ate);
      prazoStr = ate.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) + " de " + ate.toLocaleDateString("pt-BR");
    }

    const metaHtml = `
      <span>Espaço: <strong>${escapeHtml(areaNome)}</strong></span>
      <span>&bull;</span>
      <span>Data pretendida: <strong>${dataFmt} (${hIni} às ${hFim})</strong></span>
      <span>&bull;</span>
      <span>Direito de preferência até: <strong>${prazoStr}</strong></span>
    `;

    [b1, b2].forEach((banner) => {
      if (!banner) return;
      banner.classList.remove("hidden");
      const metaEl = banner.querySelector(".recovery-offer-meta");
      if (metaEl) metaEl.innerHTML = metaHtml;
    });

    const btnAcceptOverview = $("btnOverviewAcceptOffer");
    if (btnAcceptOverview) {
      btnAcceptOverview.onclick = () => handleAcceptOffer(offer.id);
    }
    const btnDeclineOverview = $("btnOverviewDeclineOffer");
    if (btnDeclineOverview) {
      btnDeclineOverview.onclick = () => handleDeclineOffer(offer.id);
    }
    const btnAcceptRes = $("btnResAcceptOffer");
    if (btnAcceptRes) {
      btnAcceptRes.onclick = () => handleAcceptOffer(offer.id);
    }
    const btnDeclineRes = $("btnResDeclineOffer");
    if (btnDeclineRes) {
      btnDeclineRes.onclick = () => handleDeclineOffer(offer.id);
    }
  } catch (err) {
    console.warn("Erro ao checar ofertas ativas de retomada de vaga:", err);
  }
}

window.handleAcceptOffer = async function (reservationId) {
  const confirmed = await showCustomConfirm({
    title: "Confirmar Direito de Preferência",
    message: "Deseja garantir esta reserva agora mesmo com exclusividade? A data passará para confirmada sob seu nome.",
    confirmText: "Sim, Confirmar Minha Vaga",
    cancelText: "Voltar",
    iconName: "check",
    isDanger: false,
  });

  if (!confirmed) return;

  try {
    await api(`/api/reservations/${reservationId}/accept-offer`, { method: "PUT" });
    showToast("Parabéns! Sua vaga foi reativada e confirmada com sucesso via direito de preferência.", "success");
    checkActiveSlotOffers(getStoredUser());
    loadReservations();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleDeclineOffer = async function (reservationId) {
  const confirmed = await showCustomConfirm({
    title: "Dispensar Vaga",
    message: "Tem certeza de que deseja dispensar esta oportunidade de reserva? A data ficará disponível para outros condôminos.",
    confirmText: "Sim, Dispensar",
    cancelText: "Voltar",
    iconName: "close",
    isDanger: true,
  });

  if (!confirmed) return;

  try {
    await api(`/api/reservations/${reservationId}/decline-offer`, { method: "PUT" });
    showToast("Você dispensou a preferência. A vaga foi liberada para a comunidade.", "info");
    checkActiveSlotOffers(getStoredUser());
    loadReservations();
    loadQuickStatsForRole(getStoredUser());
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 14. LISTA DE CONVIDADOS DA RESERVA & CONVITE DIGITAL
// ==========================================
let currentGuestsReservationId = null;

window.openGuestsModal = async function (reservationId, areaNome, dataFmt, isMine) {
  currentGuestsReservationId = reservationId;
  const modal = $("modalGuestsList");
  if (!modal) return;

  $("guestTargetReservationId").value = reservationId;
  $("guestAreaName").textContent = areaNome;
  $("guestReservationDate").textContent = dataFmt;

  const formAdd = $("formAddGuest");
  const notice = $("guestNonOwnerNotice");
  if (formAdd) {
    formAdd.classList.toggle("hidden", !isMine);
    formAdd.reset();
  }
  if (notice) {
    notice.classList.toggle("hidden", isMine);
  }
  if ($("chkGuestSendInvite")) {
    $("chkGuestSendInvite").checked = false;
  }

  modal.classList.remove("hidden");
  document.body.classList.add("modal-open");
  await loadReservationGuests(reservationId, isMine);
};

async function loadReservationGuests(reservationId, isMine) {
  const tbody = $("guestsTableBody");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="6" class="table-empty">Carregando lista de convidados...</td></tr>`;

  try {
    const guests = await api(`/api/guests/reservation/${reservationId}`);
    const total = guests.length;
    const entered = guests.filter((g) => g.entrada_registrada).length;
    const invited = guests.filter((g) => g.convite_enviado).length;

    $("guestCountTotal").textContent = total;
    $("guestCountEntered").textContent = entered;
    $("guestCountInvited").textContent = invited;

    if (!guests.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="table-empty">Nenhum convidado cadastrado até o momento.</td></tr>`;
      return;
    }

    const user = getStoredUser();
    const isStaff = isAdminRole(user) || (user && user.tipo_usuario === "PORTARIA");

    tbody.innerHTML = guests.map((g) => {
      let inviteBadge = `<span class="badge-guest-waiting">Não enviado</span>`;
      if (g.convite_enviado) {
        inviteBadge = `<span class="badge-guest-invite-sent">${icon("mail")}Enviado</span>`;
      }

      let entryStatus = `<span class="badge-guest-waiting">Aguardando</span>`;
      if (g.saida_registrada) {
        const outTime = g.saida_em ? new Date(g.saida_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        entryStatus = `<span class="badge-guest-exited">${icon("arrow")}Saída (${outTime})</span>`;
      } else if (g.entrada_registrada) {
        const entTime = g.entrada_em ? new Date(g.entrada_em).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "";
        entryStatus = `<span class="badge-guest-entered">${icon("check")}Presente (${entTime})</span>`;
      }

      let acoes = [];
      if (isStaff && !g.entrada_registrada) {
        acoes.push(`<button type="button" class="btn-action-deliver" onclick="handleCheckinGuest(${Number(g.id)}, '${escapeHtml(g.nome_completo)}')">${icon("check")}Check-in</button>`);
      }
      if (g.email && isMine) {
        acoes.push(`<button type="button" class="btn-action-guest" onclick="handleResendGuestInvite(${Number(g.id)})" title="Reenviar convite por e-mail">${icon("refresh")}</button>`);
      }
      if (isMine) {
        acoes.push(`<button type="button" class="btn-action-danger" onclick="handleDeleteGuest(${Number(g.id)})" title="Remover da lista">${icon("trash")}</button>`);
      }

      const docStr = g.documento ? escapeHtml(g.documento) : `<span class="muted">(Não informado)</span>`;

      return `
        <tr>
          <td data-label="Nome">
            <strong>${escapeHtml(g.nome_completo)}</strong>
            <small class="muted">${g.email ? escapeHtml(g.email) : docStr}</small>
          </td>
          <td data-label="Documento">${docStr}</td>
          <td data-label="E-mail">${g.email ? escapeHtml(g.email) : '<span class="muted">-</span>'}</td>
          <td data-label="Convite">${inviteBadge}</td>
          <td data-label="Status">${entryStatus}</td>
          <td data-label="Ações"><div style="display:flex; gap:0.35rem; align-items:center; flex-wrap:wrap;">${acoes.join(" ") || '<span class="muted">-</span>'}</div></td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="table-error">${escapeHtml(err.message)}</td></tr>`;
  }
}

async function handleAddGuestSubmit(e) {
  e.preventDefault();
  if (!currentGuestsReservationId) return;

  const nome = $("inputGuestNome").value.trim();
  const doc = $("inputGuestDoc").value.trim();
  const email = $("inputGuestEmail").value.trim();
  const enviarConvite = $("chkGuestSendInvite") ? $("chkGuestSendInvite").checked && Boolean(email) : false;
  const btnSubmit = $("btnAddGuestSubmit");
  const originalHtml = btnSubmit ? btnSubmit.innerHTML : "Adicionar à Lista";

  if (!nome) {
    showToast("Por favor, preencha o nome completo do convidado.", "error");
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `${icon("clock")} Gravando...`;
  }

  try {
    const res = await api(`/api/guests/reservation/${currentGuestsReservationId}`, {
      method: "POST",
      body: {
        nome_completo: nome,
        documento: doc || null,
        email: email || null,
        enviar_convite: enviarConvite,
      },
    });

    const msg = res && res.convite_enviado
      ? `Convidado "${nome}" adicionado! Convite digital despachado por e-mail com sucesso.`
      : `Convidado "${nome}" adicionado à lista do evento.`;

    showToast(msg, "success");
    $("formAddGuest").reset();
    if ($("chkGuestSendInvite")) $("chkGuestSendInvite").checked = false;
    const inputNome = $("inputGuestNome");
    if (inputNome) inputNome.focus();
    await loadReservationGuests(currentGuestsReservationId, true);
    loadReservations();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = originalHtml;
    }
  }
}

window.handleCheckinGuest = async function (guestId, nome) {
  try {
    await api(`/api/guests/${guestId}/checkin`, { method: "PUT" });
    showToast(`Entrada de "${nome}" liberada e registrada na portaria.`, "success");
    if (currentGuestsReservationId) {
      loadReservationGuests(currentGuestsReservationId, true);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleDeleteGuest = async function (guestId) {
  const confirmed = await showCustomConfirm({
    title: "Remover Convidado",
    message: "Tem certeza de que deseja remover este convidado da lista do evento?",
    confirmText: "Sim, Remover",
    cancelText: "Voltar",
    iconName: "trash",
    isDanger: true,
  });

  if (!confirmed) return;

  try {
    await api(`/api/guests/${guestId}`, { method: "DELETE" });
    showToast("Convidado removido da lista.", "info");
    if (currentGuestsReservationId) {
      loadReservationGuests(currentGuestsReservationId, true);
      loadReservations();
    }
  } catch (err) {
    showToast(err.message, "error");
  }
};

window.handleResendGuestInvite = async function (guestId) {
  try {
    await api(`/api/guests/${guestId}/send-invite`, { method: "POST" });
    showToast("Convite digital reenviado com sucesso por e-mail!", "success");
    if (currentGuestsReservationId) {
      loadReservationGuests(currentGuestsReservationId, true);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
};

// ==========================================
// 15. CONFIGURAÇÕES MODULARES DO CONDOMÍNIO (SÍNDICO)
// ==========================================
function computeCondoMonogram(name) {
  if (!name) return "SGC";
  const words = name.trim().split(/\s+/).filter((w) => w.length > 2 && !["dos", "das", "de", "do", "da", "e"].includes(w.toLowerCase()));
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return name.substring(0, 3).toUpperCase();
}

async function loadCondoSettings() {
  try {
    const settings = await api("/api/settings/public");
    if (settings && settings.nome_condominio) {
      window.condoSettingsData = settings;
      const name = settings.nome_condominio;
      const monogram = computeCondoMonogram(name);

      document.title = `${name} | SGC Sistema de Gestão de Condomínio`;

      // Monograma da marca
      document.querySelectorAll(".monogram-letter, #condoMonogram").forEach((el) => {
        el.textContent = monogram;
      });

      // Título e identificadores do condomínio
      document.querySelectorAll(".brand-mini span:last-child, .sidebar-brand-text strong, .condo-badge, .hero-brand-title, #topbarCondoName, #heroCondoTitle, #sidebarCondoName, #headerCondoBadge").forEach((el) => {
        el.textContent = name;
      });

      // Rodapé da tela de login
      const footCondo = $("footCondoName");
      if (footCondo) footCondo.textContent = `SGC ${name}`;

      // Subtítulo do síndico
      const userSub = $("overviewUserSub");
      const user = getStoredUser();
      if (userSub && user && (user.tipo_usuario === "ADMIN" || user.tipo_usuario === "SINDICO")) {
        userSub.textContent = `Gestão operacional e administrativa • ${name}`;
      }

      if (settings.endereco) {
        const locChip = document.querySelector(".hero-location-chip span");
        if (locChip) locChip.textContent = `${settings.endereco} • Portaria 24h`;
      }
    }
  } catch (err) {
    console.warn("Não foi possível obter dados públicos de identificação:", err);
  }
}

async function loadCondoSettingsForm() {
  try {
    const s = await api("/api/settings");
    if (!s) return;
    $("setCondoNome").value = s.nome_condominio || "";
    $("setCondoEndereco").value = s.endereco || "";
    $("setCondoTelefone").value = s.telefone_portaria || "";
    $("setCondoEmail").value = s.email_contato || "";
    $("setIntervaloDias").value = s.intervalo_padrao_dias || 30;
    $("setPrazoStandby").value = s.prazo_standby_horas || 48;
    $("setPrazoRetomada").value = s.prazo_retomada_horas || 24;
    if ($("setDiasPenalidadeQueima")) {
      $("setDiasPenalidadeQueima").value = s.dias_penalidade_queima || 30;
    }
    $("setQueimaPrioridade").checked = s.queima_prioridade_cancelamento ?? true;
    $("setEnviarEmailAtivo").checked = s.enviar_email_ativo ?? true;
  } catch (err) {
    showToast("Erro ao carregar configurações do condomínio: " + err.message, "error");
  }
}

async function handleSaveCondoSettings(e) {
  e.preventDefault();
  const btn = $("btnSaveCondoSettings");
  btn.disabled = true;

  try {
    const payload = {
      nome_condominio: $("setCondoNome").value.trim(),
      endereco: $("setCondoEndereco").value.trim() || null,
      telefone_portaria: $("setCondoTelefone").value.trim() || null,
      email_contato: $("setCondoEmail").value.trim() || null,
      intervalo_padrao_dias: parseInt($("setIntervaloDias").value, 10),
      prazo_standby_horas: parseInt($("setPrazoStandby").value, 10),
      prazo_retomada_horas: parseInt($("setPrazoRetomada").value, 10),
      dias_penalidade_queima: $("setDiasPenalidadeQueima") ? parseInt($("setDiasPenalidadeQueima").value, 10) || 30 : 30,
      queima_prioridade_cancelamento: $("setQueimaPrioridade").checked,
      enviar_email_ativo: $("setEnviarEmailAtivo").checked,
    };

    const updated = await api("/api/settings", {
      method: "PUT",
      body: payload,
    });

    showToast("Configurações do condomínio salvas com sucesso!", "success");
    loadCondoSettings();
    if (payload.nome_condominio) {
      document.title = `${payload.nome_condominio} | SGC Sistema de Gestão de Condomínio`;
    }
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
  }
}

// ==========================================
// 16. ORDENAÇÃO DINÂMICA DE TABELAS (TABLE SORTING)
// ==========================================
function parseCellValue(text) {
  const clean = (text || "").trim();
  // 1. Data brasileira (DD/MM/AAAA ou DD/MM/AAAA HH:MM)
  const dmyMatch = clean.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
  if (dmyMatch) {
    const [, d, m, y, h, min] = dmyMatch;
    return new Date(y, m - 1, d, h || 0, min || 0).getTime();
  }
  // 2. Horário simples (HH:MM)
  const timeMatch = clean.match(/^(\d{2}):(\d{2})$/);
  if (timeMatch) {
    return parseInt(timeMatch[1], 10) * 60 + parseInt(timeMatch[2], 10);
  }
  // 3. Número com prefixo ou moeda (ex: Apto 101, R$ 50,00, 100)
  const onlyNum = clean.replace(/^[^\d]+/, "").replace(/[^\d.,]/g, "").replace(",", ".");
  if (onlyNum && !isNaN(onlyNum)) {
    return parseFloat(onlyNum);
  }
  // 4. Texto padrão (ignora acentos)
  return clean.toLowerCase();
}

function enableTableSorting() {
  document.querySelectorAll("table.data-table").forEach((table) => {
    const thead = table.querySelector("thead");
    if (!thead || thead.dataset.sortInitialized === "true") return;
    thead.dataset.sortInitialized = "true";

    const ths = thead.querySelectorAll("th");
    ths.forEach((th, colIdx) => {
      const title = th.textContent.trim().toLowerCase();
      // Não ordena colunas de ações
      if (title.includes("ação") || title.includes("ações") || th.dataset.sortable === "false") {
        return;
      }

      th.classList.add("sortable-th");
      th.setAttribute("title", "Clique para ordenar esta coluna");
      const iconSpan = document.createElement("span");
      iconSpan.className = "sort-icon";
      iconSpan.textContent = "↕";
      th.appendChild(iconSpan);

      let currentDir = "none";

      th.addEventListener("click", () => {
        const tbody = table.querySelector("tbody");
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll("tr")).filter(
          (r) => !r.querySelector(".table-empty") && !r.querySelector(".table-error")
        );
        if (rows.length < 2) return;

        currentDir = currentDir === "asc" ? "desc" : "asc";

        ths.forEach((otherTh) => {
          if (otherTh !== th) {
            otherTh.classList.remove("sort-asc", "sort-desc");
            const icon = otherTh.querySelector(".sort-icon");
            if (icon) icon.textContent = "↕";
          }
        });

        th.classList.toggle("sort-asc", currentDir === "asc");
        th.classList.toggle("sort-desc", currentDir === "desc");
        iconSpan.textContent = currentDir === "asc" ? "▲" : "▼";

        rows.sort((rowA, rowB) => {
          const cellA = rowA.children[colIdx]?.innerText || "";
          const cellB = rowB.children[colIdx]?.innerText || "";
          const valA = parseCellValue(cellA);
          const valB = parseCellValue(cellB);

          let comp = 0;
          if (typeof valA === "number" && typeof valB === "number") {
            comp = valA - valB;
          } else {
            comp = String(valA).localeCompare(String(valB), "pt-BR");
          }
          return currentDir === "asc" ? comp : -comp;
        });

        rows.forEach((r) => tbody.appendChild(r));
      });
    });
  });
}

// ==========================================
// 16. ACCORDION / SANFONA INTERATIVA (MOBILE <= 640px)
// ==========================================
document.addEventListener("click", (e) => {
  if (window.innerWidth > 640) return;
  const tr = e.target.closest(".data-table tbody tr");
  if (!tr) return;
  if (tr.querySelector(".table-empty, .table-error")) return;
  if (e.target.closest("button, a, input, select, textarea, label")) return;

  tr.classList.toggle("is-open");
});

// ==========================================
// 17. SUPORTE PWA MOBILE E SERVICE WORKER
// ==========================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((reg) => console.log('[PWA] Service Worker registrado com sucesso! Escopo:', reg.scope))
      .catch((err) => console.warn('[PWA] Falha ao registrar Service Worker:', err));
  });
}

let deferredInstallPrompt = null;
const btnInstallPwa = document.getElementById('btnInstallPwa');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (btnInstallPwa) {
    btnInstallPwa.classList.remove('hidden');
  }
});

if (btnInstallPwa) {
  btnInstallPwa.addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const { outcome } = await deferredInstallPrompt.userChoice;
      console.log('[PWA] Resposta da instalação:', outcome);
      deferredInstallPrompt = null;
      btnInstallPwa.classList.add('hidden');
    } else {
      if (typeof showCustomConfirm === 'function') {
        showCustomConfirm({
          title: 'Instalar Aplicativo SGC',
          message: 'Para instalar o aplicativo no seu smartphone:\n\n• No Android/Chrome: Toque no menu (⋮) e selecione "Instalar aplicativo" ou "Adicionar à tela inicial".\n• No iPhone/Safari: Toque no botão de Compartilhar e selecione "Adicionar à Tela de Início".',
          confirmText: 'Entendi',
          cancelText: 'Fechar',
          isDanger: false,
          iconName: 'building'
        });
      } else {
        alert('Para instalar o aplicativo no seu celular:\n\n• No Android: Abra o menu do Chrome e selecione "Instalar aplicativo".\n• No iPhone: Toque em Compartilhar no Safari e selecione "Adicionar à Tela de Início".');
      }
    }
  });
}

window.addEventListener('appinstalled', () => {
  console.log('[PWA] Aplicativo instalado com sucesso no aparelho!');
  if (btnInstallPwa) {
    btnInstallPwa.classList.add('hidden');
  }
  if (typeof showToast === 'function') {
    showToast('Aplicativo instalado com sucesso na sua tela de início!', 'success');
  }
});

