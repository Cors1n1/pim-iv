/**
 * CONDOHUB CONSOLE — CENTRAL DE OPERAÇÕES DO SUPER ADMIN
 * Gestão de Rede Multi-Condomínio, Suporte Executivo e Auditoria LGPD
 */

const API_BASE = '/api/console';
let currentToken = localStorage.getItem('console_token') || localStorage.getItem('superadmin_token');
let allCondominios = [];
let activeTab = 'condos';
let currentDetailsCondo = null;

// ============================================================================
// Referências do DOM
// ============================================================================

// Elementos Principais
const loginView = document.getElementById('loginView');
const dashboardView = document.getElementById('dashboardView');
const formConsoleLogin = document.getElementById('formConsoleLogin');
const loginError = document.getElementById('loginError');
const btnLogout = document.getElementById('btnLogout');
const btnRefresh = document.getElementById('btnRefresh');
const btnRefreshAudit = document.getElementById('btnRefreshAudit');

// Abas de Navegação Master
const tabCondos = document.getElementById('tabCondos');
const tabCondoDetails = document.getElementById('tabCondoDetails');
const tabDetailsTitle = document.getElementById('tabDetailsTitle');
const tabBadgeDetails = document.getElementById('tabBadgeDetails');
const tabUsers = document.getElementById('tabUsers');
const tabBadgeUsers = document.getElementById('tabBadgeUsers');
const tabAudit = document.getElementById('tabAudit');
const tabBadgeAudit = document.getElementById('tabBadgeAudit');
const tabBroadcast = document.getElementById('tabBroadcast');
const tabSupportSettings = document.getElementById('tabSupportSettings');

const sectionCondos = document.getElementById('sectionCondos');
const sectionCondoDetails = document.getElementById('sectionCondoDetails');
const sectionUsers = document.getElementById('sectionUsers');
const sectionAudit = document.getElementById('sectionAudit');
const sectionBroadcast = document.getElementById('sectionBroadcast');
const sectionSupportSettings = document.getElementById('sectionSupportSettings');
const tabBadgeCondos = document.getElementById('tabBadgeCondos');

// Elementos da Aba de Canais de Suporte
const formSupportSettings = document.getElementById('formSupportSettings');
const cfgSuporteEmail = document.getElementById('cfgSuporteEmail');
const cfgSuporteTelefone = document.getElementById('cfgSuporteTelefone');
const cfgSuporteHorario = document.getElementById('cfgSuporteHorario');
const cfgTituloRegularizacao = document.getElementById('cfgTituloRegularizacao');
const cfgMensagemRegularizacao = document.getElementById('cfgMensagemRegularizacao');
const btnResetSupportDefaults = document.getElementById('btnResetSupportDefaults');
const btnSaveSupportSettings = document.getElementById('btnSaveSupportSettings');
const btnRefreshSupportSettings = document.getElementById('btnRefreshSupportSettings');

const previewActionTitle = document.getElementById('previewActionTitle');
const previewActionDesc = document.getElementById('previewActionDesc');
const previewSupportEmail = document.getElementById('previewSupportEmail');
const previewSupportPhone = document.getElementById('previewSupportPhone');
const previewSupportHours = document.getElementById('previewSupportHours');
const hintSupportContactsDisplay = document.getElementById('hintSupportContactsDisplay');
const btnGoToSupportSettingsFromModal = document.getElementById('btnGoToSupportSettingsFromModal');

// Elementos da Aba Dedicada de Gestão do Condomínio
const detailsEmptyState = document.getElementById('detailsEmptyState');
const detailsActiveContent = document.getElementById('detailsActiveContent');
const btnBackToCondosTop = document.getElementById('btnBackToCondosTop');
const btnBackToCondosBottom = document.getElementById('btnBackToCondosBottom');
const btnGoToCondosFromEmpty = document.getElementById('btnGoToCondosFromEmpty');

const tabDetailsCondoNameBreadcrumb = document.getElementById('tabDetailsCondoNameBreadcrumb');
const tabDetailsBtnImpersonate = document.getElementById('tabDetailsBtnImpersonate');
const tabDetailsBtnEdit = document.getElementById('tabDetailsBtnEdit');
const tabDetailsBtnResetPass = document.getElementById('tabDetailsBtnResetPass');
const tabDetailsBtnToggleStatus = document.getElementById('tabDetailsBtnToggleStatus');
const tabDetailsToggleStatusLabel = document.getElementById('tabDetailsToggleStatusLabel');
const tabDetailsSuspendedAlert = document.getElementById('tabDetailsSuspendedAlert');
const tabDetailsBtnAlertReactivate = document.getElementById('tabDetailsBtnAlertReactivate');

const tabDetailsBannerBg = document.getElementById('tabDetailsBannerBg');
const tabDetailsPlanoDisplay = document.getElementById('tabDetailsPlanoDisplay');
const tabDetailsNomeDisplay = document.getElementById('tabDetailsNomeDisplay');
const tabDetailsStatusBadge = document.getElementById('tabDetailsStatusBadge');
const tabDetailsCnpjDisplay = document.getElementById('tabDetailsCnpjDisplay');
const tabDetailsCreatedDisplay = document.getElementById('tabDetailsCreatedDisplay');
const tabDetailsIdDisplay = document.getElementById('tabDetailsIdDisplay');
const tabDetailsMotivoBannerWrapper = document.getElementById('tabDetailsMotivoBannerWrapper');
const tabDetailsMotivoBanner = document.getElementById('tabDetailsMotivoBanner');
const tabDetailsMotivoBadge = document.getElementById('tabDetailsMotivoBadge');
const tabDetailsMotivoDetail = document.getElementById('tabDetailsMotivoDetail');
const tabDetailsMotivoText = document.getElementById('tabDetailsMotivoText');

const tabDetailsUrlDisplay = document.getElementById('tabDetailsUrlDisplay');
const tabBtnCopyCondoUrl = document.getElementById('tabBtnCopyCondoUrl');
const tabBtnOpenCondoUrl = document.getElementById('tabBtnOpenCondoUrl');

const tabDetailsUnidadesCount = document.getElementById('tabDetailsUnidadesCount');
const tabDetailsUnidadesSub = document.getElementById('tabDetailsUnidadesSub');
const tabDetailsCapacityBar = document.getElementById('tabDetailsCapacityBar');
const tabDetailsMoradoresCount = document.getElementById('tabDetailsMoradoresCount');
const tabDetailsEncomendasCount = document.getElementById('tabDetailsEncomendasCount');
const tabDetailsPorteirosCount = document.getElementById('tabDetailsPorteirosCount');
const tabDetailsOcorrenciasCount = document.getElementById('tabDetailsOcorrenciasCount');
const tabDetailsOcorrenciasStatus = document.getElementById('tabDetailsOcorrenciasStatus');
const tabDetailsAreasCount = document.getElementById('tabDetailsAreasCount');
const tabDetailsReservasCount = document.getElementById('tabDetailsReservasCount');

const tabDetailsSindicoAvatar = document.getElementById('tabDetailsSindicoAvatar');
const tabDetailsSindicoNome = document.getElementById('tabDetailsSindicoNome');
const tabDetailsSindicoEmail = document.getElementById('tabDetailsSindicoEmail');
const tabDetailsSindicoTelefoneBadge = document.getElementById('tabDetailsSindicoTelefoneBadge');
const tabDetailsSindicoWhatsApp = document.getElementById('tabDetailsSindicoWhatsApp');
const tabBtnDetailsResetSindico = document.getElementById('tabBtnDetailsResetSindico');

const tabDetailsEnderecoVal = document.getElementById('tabDetailsEnderecoVal');
const tabDetailsTelefoneVal = document.getElementById('tabDetailsTelefoneVal');
const tabDetailsEmailVal = document.getElementById('tabDetailsEmailVal');
const tabDetailsDotPrimaria = document.getElementById('tabDetailsDotPrimaria');
const tabDetailsDotSecundaria = document.getElementById('tabDetailsDotSecundaria');

// Central de Usuários da Rede (com Filtros Avançados)
const inputSearchUser = document.getElementById('inputSearchUser');
const selectFilterUserCondo = document.getElementById('selectFilterUserCondo');
const inputFilterUserUnit = document.getElementById('inputFilterUserUnit');
const selectFilterUserRole = document.getElementById('selectFilterUserRole');
const selectFilterUserStatus = document.getElementById('selectFilterUserStatus');
const btnResetUserFilters = document.getElementById('btnResetUserFilters');
const btnRefreshUsers = document.getElementById('btnRefreshUsers');
const usersTableBody = document.getElementById('usersTableBody');

// Usuários do Condomínio Selecionado (Aba Dedicada de Gestão do Condomínio)
const tabDetailsUsersTableBody = document.getElementById('tabDetailsUsersTableBody');
const tabDetailsUsersBadgeCount = document.getElementById('tabDetailsUsersBadgeCount');
const inputDetailsUserSearch = document.getElementById('inputDetailsUserSearch');
const selectDetailsUserRole = document.getElementById('selectDetailsUserRole');
const btnRefreshDetailsUsers = document.getElementById('btnRefreshDetailsUsers');

// Central de Broadcast Master
const formBroadcastMaster = document.getElementById('formBroadcastMaster');
const broadcastTitulo = document.getElementById('broadcastTitulo');
const broadcastCategoria = document.getElementById('broadcastCategoria');
const broadcastDestino = document.getElementById('broadcastDestino');
const broadcastMensagem = document.getElementById('broadcastMensagem');
const btnSendBroadcast = document.getElementById('btnSendBroadcast');
const categoryChipsGroup = document.getElementById('categoryChipsGroup');
const broadcastAudienceBadge = document.getElementById('broadcastAudienceBadge');
const broadcastCharCount = document.getElementById('broadcastCharCount');
const btnInsertBroadcastBullet = document.getElementById('btnInsertBroadcastBullet');
const btnResetBroadcast = document.getElementById('btnResetBroadcast');
const broadcastHistoryTableBody = document.getElementById('broadcastHistoryTableBody');
const badgeBroadcastHistoryCount = document.getElementById('badgeBroadcastHistoryCount');
const btnRefreshBroadcasts = document.getElementById('btnRefreshBroadcasts');

// Busca
const inputSearchCondo = document.getElementById('inputSearchCondo');
const btnClearSearch = document.getElementById('btnClearSearch');

// Métricas Gerais do Topo
const metricCondosAtivos = document.getElementById('metricCondosAtivos');
const metricCondosTotal = document.getElementById('metricCondosTotal');
const metricTotalUnidades = document.getElementById('metricTotalUnidades');
const metricTotalMoradores = document.getElementById('metricTotalMoradores');
const metricTotalUsuarios = document.getElementById('metricTotalUsuarios');
const metricEventos = document.getElementById('metricEventos');

// Lista e Hub de Condomínios da Rede
const condosListContainer = document.getElementById('condosListContainer') || document.getElementById('condosTableBody');
const condosTableBody = condosListContainer;
const statusFilterPills = document.getElementById('statusFilterPills');
const countFilterAll = document.getElementById('countFilterAll');
const countFilterAtivos = document.getElementById('countFilterAtivos');
const countFilterSuspensos = document.getElementById('countFilterSuspensos');
let currentStatusFilter = 'ALL';
const auditTableBody = document.getElementById('auditTableBody');

// Modal Novo Condomínio
const modalNewCondo = document.getElementById('modalNewCondo');
const btnOpenNewCondo = document.getElementById('btnOpenNewCondo');
const btnCloseModalNewCondo = document.getElementById('btnCloseModalNewCondo');
const btnCancelNewCondo = document.getElementById('btnCancelNewCondo');
const formCreateCondo = document.getElementById('formCreateCondo');
const newCondoNome = document.getElementById('newCondoNome');
const newCondoSlug = document.getElementById('newCondoSlug');
const slugPreviewText = document.getElementById('slugPreviewText');
let userCustomizedNewSlug = false;
const newCondoCorPrimaria = document.getElementById('newCondoCorPrimaria');
const labelCorPrimaria = document.getElementById('labelCorPrimaria');
const newCondoCorSecundaria = document.getElementById('newCondoCorSecundaria');
const labelCorSecundaria = document.getElementById('labelCorSecundaria');
const newCondoCorSidebar = document.getElementById('newCondoCorSidebar');
const labelNewCondoSidebar = document.getElementById('labelNewCondoSidebar');
const newSindicoNome = document.getElementById('newSindicoNome');
const newSindicoEmail = document.getElementById('newSindicoEmail');
const newSindicoTelefone = document.getElementById('newSindicoTelefone');
const newCondoLimite = document.getElementById('newCondoLimite');
const newSindicoSenha = document.getElementById('newSindicoSenha');
const btnGenPasswordNew = document.getElementById('btnGenPasswordNew');
const btnToggleNewPassword = document.getElementById('btnToggleNewPassword');

window.setNewCondoCapacity = function(val) {
  if (newCondoLimite) {
    newCondoLimite.value = val;
    document.querySelectorAll('.btn-capacity-chip').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.trim().startsWith(String(val)));
    });
  }
};

if (newCondoLimite) {
  newCondoLimite.addEventListener('input', () => {
    const val = newCondoLimite.value.trim();
    document.querySelectorAll('.btn-capacity-chip').forEach(btn => {
      btn.classList.toggle('active', btn.textContent.trim().startsWith(val));
    });
  });
}

// Governança & Administradora no Modal Novo
const radioGovAutogestao = document.getElementById('radioGovAutogestao');
const radioGovCompartilhada = document.getElementById('radioGovCompartilhada');
const cardGovAutogestao = document.getElementById('cardGovAutogestao');
const cardGovCompartilhada = document.getElementById('cardGovCompartilhada');
const wrapperAdmFields = document.getElementById('wrapperAdmFields');
const newAdmNome = document.getElementById('newAdmNome');
const newAdmEmail = document.getElementById('newAdmEmail');
const newAdmTelefone = document.getElementById('newAdmTelefone');

// Governança: Subsíndico no Modal Novo
const toggleNewTemSubsindico = document.getElementById('toggleNewTemSubsindico');
const wrapperSubsindicoFields = document.getElementById('wrapperSubsindicoFields');
const newSubsindicoNome = document.getElementById('newSubsindicoNome');
const newSubsindicoEmail = document.getElementById('newSubsindicoEmail');
const newSubsindicoTelefone = document.getElementById('newSubsindicoTelefone');

// Modal Sucesso do Convite de Ativação
const modalInviteSuccess = document.getElementById('modalInviteSuccess');
const btnCloseModalInviteSuccess = document.getElementById('btnCloseModalInviteSuccess');
const btnDoneInviteSuccess = document.getElementById('btnDoneInviteSuccess');
const succCondoNome = document.getElementById('succCondoNome');
const succSindicoNomeDisplay = document.getElementById('succSindicoNomeDisplay');
const succSindicoEmail = document.getElementById('succSindicoEmail');
const succSenhaProvisoria = document.getElementById('succSenhaProvisoria');
const btnCopySenhaProvisoria = document.getElementById('btnCopySenhaProvisoria');
const succActivationUrl = document.getElementById('succActivationUrl');
const btnCopyActivationUrl = document.getElementById('btnCopyActivationUrl');
const succCopyHint = document.getElementById('succCopyHint');
const btnShareWhatsApp = document.getElementById('btnShareWhatsApp');
const btnOpenAtivarPreview = document.getElementById('btnOpenAtivarPreview');

// Elementos de Ativação da Administradora
const cardInviteAdm = document.getElementById('cardInviteAdm');
const succAdmNomeDisplay = document.getElementById('succAdmNomeDisplay');
const succAdmEmail = document.getElementById('succAdmEmail');
const succAdmActivationUrl = document.getElementById('succAdmActivationUrl');
const btnCopyAdmActivationUrl = document.getElementById('btnCopyAdmActivationUrl');
const btnShareWhatsAppAdm = document.getElementById('btnShareWhatsAppAdm');
const btnOpenAtivarPreviewAdm = document.getElementById('btnOpenAtivarPreviewAdm');

// Elementos de Ativação do Subsíndico
const cardInviteSubsindico = document.getElementById('cardInviteSubsindico');
const succSubsindicoNomeDisplay = document.getElementById('succSubsindicoNomeDisplay');
const succSubsindicoEmail = document.getElementById('succSubsindicoEmail');
const succSubActivationUrl = document.getElementById('succSubActivationUrl');
const btnCopySubActivationUrl = document.getElementById('btnCopySubActivationUrl');
const btnShareWhatsAppSub = document.getElementById('btnShareWhatsAppSub');
const btnOpenAtivarPreviewSub = document.getElementById('btnOpenAtivarPreviewSub');

// Modal Editar Condomínio
const modalEditCondo = document.getElementById('modalEditCondo');
const btnCloseModalEditCondo = document.getElementById('btnCloseModalEditCondo');
const btnCancelEditCondo = document.getElementById('btnCancelEditCondo');
const formEditCondo = document.getElementById('formEditCondo');
const editCondoId = document.getElementById('editCondoId');
const editCondoNome = document.getElementById('editCondoNome');
const editCondoSlug = document.getElementById('editCondoSlug');
const editSlugPreview = document.getElementById('editSlugPreview');
const editCondoCnpj = document.getElementById('editCondoCnpj');
const editCondoEndereco = document.getElementById('editCondoEndereco');
const editCondoTelefone = document.getElementById('editCondoTelefone');
const editCondoEmail = document.getElementById('editCondoEmail');
const editCondoLimite = document.getElementById('editCondoLimite');
const editCondoCorPrimaria = document.getElementById('editCondoCorPrimaria');
const labelEditCorPrimaria = document.getElementById('labelEditCorPrimaria');
const editCondoCorSecundaria = document.getElementById('editCondoCorSecundaria');
const labelEditCorSecundaria = document.getElementById('labelEditCorSecundaria');
const editCondoCorSidebar = document.getElementById('editCondoCorSidebar');
const labelEditCorSidebar = document.getElementById('labelEditCorSidebar');
const editSindicoNome = document.getElementById('editSindicoNome');
const editSindicoEmail = document.getElementById('editSindicoEmail');
const editSindicoTelefone = document.getElementById('editSindicoTelefone');
const editSindicoSenha = document.getElementById('editSindicoSenha');
const btnGenPasswordEdit = document.getElementById('btnGenPasswordEdit');
const btnToggleEditPassword = document.getElementById('btnToggleEditPassword');

// Subsíndico no Modal Editar
const editTemSubsindico = document.getElementById('editTemSubsindico');
const labelEditTemSubsindico = document.getElementById('labelEditTemSubsindico');
const badgeEditSubStatus = document.getElementById('badgeEditSubStatus');
const wrapperEditSubsindicoFields = document.getElementById('wrapperEditSubsindicoFields');
const editSubsindicoNome = document.getElementById('editSubsindicoNome');
const editSubsindicoEmail = document.getElementById('editSubsindicoEmail');
const editSubsindicoTelefone = document.getElementById('editSubsindicoTelefone');
const editSubsindicoSenha = document.getElementById('editSubsindicoSenha');
const btnGenPasswordEditSub = document.getElementById('btnGenPasswordEditSub');
const btnToggleEditSubPassword = document.getElementById('btnToggleEditSubPassword');
const btnRemoveEditSubsindico = document.getElementById('btnRemoveEditSubsindico');

// Governança no Modal Editar
const cardEditGovAutogestao = document.getElementById('cardEditGovAutogestao');
const cardEditGovCompartilhada = document.getElementById('cardEditGovCompartilhada');
const radioEditGovAutogestao = document.getElementById('radioEditGovAutogestao');
const radioEditGovCompartilhada = document.getElementById('radioEditGovCompartilhada');
const wrapperEditAdmFields = document.getElementById('wrapperEditAdmFields');
const editAdmNome = document.getElementById('editAdmNome');
const editAdmEmail = document.getElementById('editAdmEmail');
const editAdmTelefone = document.getElementById('editAdmTelefone');

// Painel Administradora na Aba de Detalhes
const tabDetailsAdmBox = document.getElementById('tabDetailsAdmBox');
const tabDetailsAdmAvatar = document.getElementById('tabDetailsAdmAvatar');
const tabDetailsAdmNome = document.getElementById('tabDetailsAdmNome');
const tabDetailsAdmEmail = document.getElementById('tabDetailsAdmEmail');
const tabDetailsAdmStatusBadge = document.getElementById('tabDetailsAdmStatusBadge');
const tabDetailsAdmTelefoneBadge = document.getElementById('tabDetailsAdmTelefoneBadge');
const tabDetailsAdmWhatsApp = document.getElementById('tabDetailsAdmWhatsApp');
const tabBtnDetailsResendAdmInvite = document.getElementById('tabBtnDetailsResendAdmInvite');

// Painel Subsíndico na Aba de Detalhes
const tabDetailsSubBox = document.getElementById('tabDetailsSubBox');
const tabDetailsNoSubBox = document.getElementById('tabDetailsNoSubBox');
const tabDetailsSubAvatar = document.getElementById('tabDetailsSubAvatar');
const tabDetailsSubNome = document.getElementById('tabDetailsSubNome');
const tabDetailsSubEmail = document.getElementById('tabDetailsSubEmail');
const tabDetailsSubStatusBadge = document.getElementById('tabDetailsSubStatusBadge');
const tabDetailsSubTelefoneBadge = document.getElementById('tabDetailsSubTelefoneBadge');
const tabDetailsSubWhatsApp = document.getElementById('tabDetailsSubWhatsApp');
const tabBtnDetailsResendSubInvite = document.getElementById('tabBtnDetailsResendSubInvite');
const tabBtnDetailsResetSub = document.getElementById('tabBtnDetailsResetSub');
const tabBtnDetailsAddSub = document.getElementById('tabBtnDetailsAddSub');

// Modal Resetar Senha
const modalResetPassword = document.getElementById('modalResetPassword');
const btnCloseModalResetPassword = document.getElementById('btnCloseModalResetPassword');
const btnCancelResetPassword = document.getElementById('btnCancelResetPassword');
const formResetPassword = document.getElementById('formResetPassword');
const resetCondoId = document.getElementById('resetCondoId');
const resetPapelRole = document.getElementById('resetPapelRole');
const resetTargetRoleLabel = document.getElementById('resetTargetRoleLabel');
const resetCondoNomeDisplay = document.getElementById('resetCondoNomeDisplay');
const resetSindicoEmailDisplay = document.getElementById('resetSindicoEmailDisplay');
const resetNovaSenha = document.getElementById('resetNovaSenha');
const btnGenPasswordReset = document.getElementById('btnGenPasswordReset');

// Modal Resetar Senha de Usuário da Rede
const modalResetUserPassword = document.getElementById('modalResetUserPassword');
const btnCloseModalResetUserPassword = document.getElementById('btnCloseModalResetUserPassword');
const btnCancelResetUserPassword = document.getElementById('btnCancelResetUserPassword');
const formResetUserPassword = document.getElementById('formResetUserPassword');
const resetTargetUserId = document.getElementById('resetTargetUserId');
const resetUserAvatar = document.getElementById('resetUserAvatar');
const resetUserNomeDisplay = document.getElementById('resetUserNomeDisplay');
const resetUserEmailDisplay = document.getElementById('resetUserEmailDisplay');
const resetUserRoleBadge = document.getElementById('resetUserRoleBadge');
const resetUserCondoDisplay = document.getElementById('resetUserCondoDisplay');
const resetUserNovaSenha = document.getElementById('resetUserNovaSenha');
const btnToggleUserPwVisibility = document.getElementById('btnToggleUserPwVisibility');
const iconEyeUserPw = document.getElementById('iconEyeUserPw');
const btnGenPasswordUserReset = document.getElementById('btnGenPasswordUserReset');
const btnCopyPasswordUserReset = document.getElementById('btnCopyPasswordUserReset');
const resetUserForceChange = document.getElementById('resetUserForceChange');
const btnSaveResetUserPassword = document.getElementById('btnSaveResetUserPassword');

// Modal Dossiê Executivo do Condomínio
const modalCondoDetails = document.getElementById('modalCondoDetails');
const btnCloseModalDetails = document.getElementById('btnCloseModalDetails');
const btnCancelDetails = document.getElementById('btnCancelDetails');
const btnDetailsEditThisCondo = document.getElementById('btnDetailsEditThisCondo');
const btnDetailsImpersonate = document.getElementById('btnDetailsImpersonate');
const btnDetailsResetPassword = document.getElementById('btnDetailsResetPassword');
const btnCopyCondoUrl = document.getElementById('btnCopyCondoUrl');
const btnOpenCondoUrl = document.getElementById('btnOpenCondoUrl');

const detailsBannerBg = document.getElementById('detailsBannerBg');
const detailsPlanoDisplay = document.getElementById('detailsPlanoDisplay');
const detailsCondoNomeDisplay = document.getElementById('detailsCondoNomeDisplay');
const detailsStatusBadge = document.getElementById('detailsStatusBadge');
const detailsCnpjDisplay = document.getElementById('detailsCnpjDisplay');
const detailsCreatedDisplay = document.getElementById('detailsCreatedDisplay');
const detailsIdDisplay = document.getElementById('detailsIdDisplay');
const detailsUrlDisplay = document.getElementById('detailsUrlDisplay');

const detailsUnidadesCount = document.getElementById('detailsUnidadesCount');
const detailsUnidadesSub = document.getElementById('detailsUnidadesSub');
const detailsCapacityBar = document.getElementById('detailsCapacityBar');
const detailsMoradoresCount = document.getElementById('detailsMoradoresCount');
const detailsEncomendasCount = document.getElementById('detailsEncomendasCount');
const detailsPorteirosCount = document.getElementById('detailsPorteirosCount');
const detailsOcorrenciasCount = document.getElementById('detailsOcorrenciasCount');
const detailsOcorrenciasStatus = document.getElementById('detailsOcorrenciasStatus');
const detailsAreasCount = document.getElementById('detailsAreasCount');
const detailsReservasCount = document.getElementById('detailsReservasCount');

const detailsSindicoAvatar = document.getElementById('detailsSindicoAvatar');
const detailsSindicoNome = document.getElementById('detailsSindicoNome');
const detailsSindicoEmail = document.getElementById('detailsSindicoEmail');
const detailsSindicoTelefoneBadge = document.getElementById('detailsSindicoTelefoneBadge');
const detailsSindicoWhatsApp = document.getElementById('detailsSindicoWhatsApp');

const detailsEnderecoVal = document.getElementById('detailsEnderecoVal');
const detailsTelefoneVal = document.getElementById('detailsTelefoneVal');
const detailsEmailVal = document.getElementById('detailsEmailVal');
const detailsDotPrimaria = document.getElementById('detailsDotPrimaria');
const detailsDotSecundaria = document.getElementById('detailsDotSecundaria');

// Modal Suspender ou Reativar Condomínio
const modalToggleCondoStatus = document.getElementById('modalToggleCondoStatus');
const btnCloseModalToggleStatus = document.getElementById('btnCloseModalToggleStatus');
const btnCancelToggleStatus = document.getElementById('btnCancelToggleStatus');
const formToggleCondoStatus = document.getElementById('formToggleCondoStatus');

const statusTargetCondoId = document.getElementById('statusTargetCondoId');
const statusTargetNextAction = document.getElementById('statusTargetNextAction');
const statusTargetCondoNome = document.getElementById('statusTargetCondoNome');

const statusModalIconBadge = document.getElementById('statusModalIconBadge');
const statusModalTitle = document.getElementById('statusModalTitle');
const statusModalSubtitle = document.getElementById('statusModalSubtitle');

const statusModalAvatar = document.getElementById('statusModalAvatar');
const statusModalCondoNome = document.getElementById('statusModalCondoNome');
const statusModalCnpjBadge = document.getElementById('statusModalCnpjBadge');
const statusModalUnidadesBadge = document.getElementById('statusModalUnidadesBadge');
const statusModalStatusBadge = document.getElementById('statusModalStatusBadge');

const statusSectionSuspend = document.getElementById('statusSectionSuspend');
const statusSectionReactivate = document.getElementById('statusSectionReactivate');
const statusSuspendReason = document.getElementById('statusSuspendReason');
const statusSuspendNotes = document.getElementById('statusSuspendNotes');
const chkConfirmSuspend = document.getElementById('chkConfirmSuspend');
const reactivateMotivoBox = document.getElementById('reactivateMotivoBox');
const reactivateCurrentMotivoText = document.getElementById('reactivateCurrentMotivoText');

const btnSubmitToggleStatus = document.getElementById('btnSubmitToggleStatus');
const btnSubmitToggleStatusIcon = document.getElementById('btnSubmitToggleStatusIcon');
const btnSubmitToggleStatusText = document.getElementById('btnSubmitToggleStatusText');

// ============================================================================
// Utilitários
// ============================================================================

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function slugify(text) {
  return text
    .toString()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9 ]/g, '')
    .replace(/\s+/g, '-');
}

function generateStrongPassword() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%';
  let pass = '';
  for (let i = 0; i < 10; i++) {
    pass += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return `Condo@${pass}`;
}

function debounce(fn, ms = 300) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}

window.copyToClipboard = function(text, successMsg = 'Copiado com sucesso!') {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast(successMsg, 'success');
    }).catch(() => fallbackCopy(text, successMsg));
  } else {
    fallbackCopy(text, successMsg);
  }
};

function fallbackCopy(text, successMsg) {
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    showToast(successMsg, 'success');
  } catch (err) {
    showToast('Não foi possível copiar automaticamente.', 'error');
  }
  document.body.removeChild(ta);
}

function togglePasswordVisibility(inputEl, btnEl) {
  if (!inputEl) return;
  const isPass = inputEl.type === 'password';
  inputEl.type = isPass ? 'text' : 'password';
  if (btnEl) {
    btnEl.innerHTML = isPass
      ? '<svg class="ico"><use href="#i-eye-off"/></svg>'
      : '<svg class="ico"><use href="#i-eye"/></svg>';
  }
}

// ============================================================================
// Inicialização de Eventos
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  const savedEmail = localStorage.getItem('console_user_email');
  if (savedEmail) {
    const displayEmail = document.getElementById('displayAdminEmail');
    if (displayEmail) displayEmail.textContent = savedEmail;
  }

  // Pickers de cores do modal novo
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

  // Pickers de cores do modal editar
  if (editCondoCorPrimaria && labelEditCorPrimaria) {
    editCondoCorPrimaria.addEventListener('input', (e) => {
      labelEditCorPrimaria.textContent = e.target.value;
    });
  }
  if (editCondoCorSecundaria && labelEditCorSecundaria) {
    editCondoCorSecundaria.addEventListener('input', (e) => {
      labelEditCorSecundaria.textContent = e.target.value;
    });
  }
  if (editCondoCorSidebar && labelEditCorSidebar) {
    editCondoCorSidebar.addEventListener('input', (e) => {
      labelEditCorSidebar.textContent = e.target.value;
    });
  }

  // Configura prefixo dinâmico das URLs com o domínio atual
  document.querySelectorAll('.url-domain-prefix').forEach(el => {
    el.textContent = `${window.location.origin}/c/`;
  });

  if (newCondoSlug) {
    newCondoSlug.addEventListener('input', () => {
      userCustomizedNewSlug = true;
      newCondoSlug.value = newCondoSlug.value
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9-]/g, '-');
    });
  }

  // Slug em tempo real no cadastro
  if (newCondoNome) {
    newCondoNome.addEventListener('input', (e) => {
      if (!userCustomizedNewSlug && newCondoSlug) {
        newCondoSlug.value = slugify(e.target.value);
      }
    });
  }

  // Slug em tempo real na edição
  if (editCondoSlug) {
    editCondoSlug.addEventListener('input', () => {
      editCondoSlug.value = editCondoSlug.value
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9-]/g, '-');
    });
  }

  // Paletas Rápidas no Modal Novo
  document.querySelectorAll('.btn-theme-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-theme-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const p = btn.getAttribute('data-primary');
      const s = btn.getAttribute('data-secondary');
      if (newCondoCorPrimaria) {
        newCondoCorPrimaria.value = p;
        labelCorPrimaria.textContent = p;
      }
      if (newCondoCorSecundaria) {
        newCondoCorSecundaria.value = s;
        labelCorSecundaria.textContent = s;
      }
    });
  });

  // Paletas Rápidas no Modal Editar
  document.querySelectorAll('.btn-theme-chip-edit').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-theme-chip-edit').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const p = btn.getAttribute('data-primary');
      const s = btn.getAttribute('data-secondary');
      if (editCondoCorPrimaria) {
        editCondoCorPrimaria.value = p;
        labelEditCorPrimaria.textContent = p;
      }
      if (editCondoCorSecundaria) {
        editCondoCorSecundaria.value = s;
        labelEditCorSecundaria.textContent = s;
      }
    });
  });

  // Sidebar Presets no Modal Novo
  document.querySelectorAll('.btn-sidebar-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-sidebar-chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const side = btn.getAttribute('data-sidebar');
      if (newCondoCorSidebar) newCondoCorSidebar.value = side;
      if (labelNewCondoSidebar) labelNewCondoSidebar.textContent = side;
    });
  });

  // Sidebar Presets no Modal Editar
  document.querySelectorAll('.btn-sidebar-chip-edit').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-sidebar-chip-edit').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const side = btn.getAttribute('data-sidebar');
      if (editCondoCorSidebar) {
        editCondoCorSidebar.value = side;
        if (labelEditCorSidebar) labelEditCorSidebar.textContent = side;
      }
    });
  });

  // Geradores de senha
  if (btnGenPasswordNew && newSindicoSenha) {
    btnGenPasswordNew.addEventListener('click', () => {
      newSindicoSenha.value = generateStrongPassword();
      showToast('Senha forte gerada para o síndico!', 'info');
    });
  }
  if (btnGenPasswordEdit && editSindicoSenha) {
    btnGenPasswordEdit.addEventListener('click', () => {
      editSindicoSenha.value = generateStrongPassword();
      showToast('Nova senha forte gerada!', 'info');
    });
  }
  if (btnGenPasswordReset && resetNovaSenha) {
    btnGenPasswordReset.addEventListener('click', () => {
      resetNovaSenha.value = generateStrongPassword();
      showToast('Nova senha gerada!', 'info');
    });
  }

  // Toggles de visualização de senha
  if (btnToggleNewPassword && newSindicoSenha) {
    btnToggleNewPassword.addEventListener('click', () => {
      togglePasswordVisibility(newSindicoSenha, btnToggleNewPassword);
    });
  }
  if (btnToggleEditPassword && editSindicoSenha) {
    btnToggleEditPassword.addEventListener('click', () => {
      togglePasswordVisibility(editSindicoSenha, btnToggleEditPassword);
    });
  }

  // Dossiê: Botões de Fechamento e Cópia
  if (btnCloseModalDetails) {
    btnCloseModalDetails.addEventListener('click', closeCondoDetailsModal);
  }
  if (btnCancelDetails) {
    btnCancelDetails.addEventListener('click', closeCondoDetailsModal);
  }
  if (btnCopyCondoUrl) {
    btnCopyCondoUrl.addEventListener('click', () => {
      if (currentDetailsCondo) {
        const fullUrl = `${window.location.origin}/c/${currentDetailsCondo.slug || ''}/`;
        copyToClipboard(fullUrl, 'URL exclusiva copiada para a área de transferência!');
      }
    });
  }
  if (btnDetailsEditThisCondo) {
    btnDetailsEditThisCondo.addEventListener('click', () => {
      if (currentDetailsCondo) {
        closeCondoDetailsModal();
        openEditCondoModal(currentDetailsCondo.id);
      }
    });
  }
  if (btnDetailsImpersonate) {
    btnDetailsImpersonate.addEventListener('click', () => {
      if (currentDetailsCondo) {
        impersonateCondo(currentDetailsCondo.id, currentDetailsCondo.nome, currentDetailsCondo.slug);
      }
    });
  }
  if (tabDetailsBtnImpersonate) {
    tabDetailsBtnImpersonate.addEventListener('click', (e) => {
      if (e) e.preventDefault();
      if (currentDetailsCondo) {
        impersonateCondo(currentDetailsCondo.id, currentDetailsCondo.nome, currentDetailsCondo.slug);
      }
    });
  }
  if (tabBtnOpenCondoUrl) {
    tabBtnOpenCondoUrl.addEventListener('click', (e) => {
      if (e) e.preventDefault();
      if (currentDetailsCondo) {
        impersonateCondo(currentDetailsCondo.id, currentDetailsCondo.nome, currentDetailsCondo.slug);
      }
    });
  }
  if (btnDetailsResetPassword) {
    btnDetailsResetPassword.addEventListener('click', () => {
      if (currentDetailsCondo) {
        closeCondoDetailsModal();
        openResetPasswordModal(currentDetailsCondo.id, currentDetailsCondo.nome, currentDetailsCondo.sindico_email);
      }
    });
  }

  // Abas Master
  tabCondos.addEventListener('click', () => switchTab('condos'));
  if (tabCondoDetails) tabCondoDetails.addEventListener('click', () => switchTab('condoDetails'));
  if (tabUsers) tabUsers.addEventListener('click', () => switchTab('users'));
  tabAudit.addEventListener('click', () => switchTab('audit'));
  if (tabBroadcast) tabBroadcast.addEventListener('click', () => switchTab('broadcast'));
  if (tabSupportSettings) tabSupportSettings.addEventListener('click', () => switchTab('supportSettings'));

  // Eventos dos Canais de Suporte
  if (btnRefreshSupportSettings) {
    btnRefreshSupportSettings.addEventListener('click', () => {
      loadSupportSettings();
      showToast('Canais de suporte recarregados.', 'info');
    });
  }
  if (formSupportSettings) {
    formSupportSettings.addEventListener('submit', handleSupportSettingsSubmit);
  }
  if (btnResetSupportDefaults) {
    btnResetSupportDefaults.addEventListener('click', resetSupportDefaults);
  }
  if (btnGoToSupportSettingsFromModal) {
    btnGoToSupportSettingsFromModal.addEventListener('click', () => {
      closeToggleStatusModal();
      switchTab('supportSettings');
    });
  }
  [cfgSuporteEmail, cfgSuporteTelefone, cfgSuporteHorario, cfgTituloRegularizacao, cfgMensagemRegularizacao].forEach(input => {
    if (input) {
      input.addEventListener('input', updateSupportLivePreview);
    }
  });

  // Botões de voltar na aba dedicada
  if (btnBackToCondosTop) btnBackToCondosTop.addEventListener('click', () => switchTab('condos'));
  if (btnBackToCondosBottom) btnBackToCondosBottom.addEventListener('click', () => switchTab('condos'));
  if (btnGoToCondosFromEmpty) btnGoToCondosFromEmpty.addEventListener('click', () => switchTab('condos'));

  // Copiar URL na aba dedicada
  if (tabBtnCopyCondoUrl) {
    tabBtnCopyCondoUrl.addEventListener('click', () => {
      if (currentDetailsCondo) {
        const fullUrl = `${window.location.origin}/c/${currentDetailsCondo.slug || ''}/`;
        copyToClipboard(fullUrl, 'URL do portal copiada!');
      }
    });
  }

  // Redefinir senha síndico na aba dedicada
  if (tabBtnDetailsResetSindico) {
    tabBtnDetailsResetSindico.addEventListener('click', () => {
      if (currentDetailsCondo) {
        openResetPasswordModal(currentDetailsCondo.id, currentDetailsCondo.nome, currentDetailsCondo.sindico_email);
      }
    });
  }

  // Reenviar convite na aba dedicada (Header e Card do Síndico)
  const tabDetailsBtnResendInvite = document.getElementById('tabDetailsBtnResendInvite');
  if (tabDetailsBtnResendInvite) {
    tabDetailsBtnResendInvite.addEventListener('click', () => {
      if (currentDetailsCondo) {
        resendSindicoInvite(currentDetailsCondo.id, currentDetailsCondo.nome);
      }
    });
  }
  const tabBtnDetailsResendInviteCard = document.getElementById('tabBtnDetailsResendInviteCard');
  if (tabBtnDetailsResendInviteCard) {
    tabBtnDetailsResendInviteCard.addEventListener('click', () => {
      if (currentDetailsCondo) {
        resendSindicoInvite(currentDetailsCondo.id, currentDetailsCondo.nome);
      }
    });
  }

  // Reenviar convite da Administradora na aba dedicada
  if (tabBtnDetailsResendAdmInvite) {
    tabBtnDetailsResendAdmInvite.addEventListener('click', async () => {
      if (!currentDetailsCondo) return;
      try {
        const res = await fetchAdmin(`/condominios/${currentDetailsCondo.id}/resend-invite?papel=ADMIN`, {
          method: 'POST'
        });
        showToast(res.message, 'success');
        if (res.activation_url) {
          openInviteSuccessModal({
            nome: currentDetailsCondo.nome,
            slug: currentDetailsCondo.slug,
            sindico_nome: currentDetailsCondo.sindico_nome,
            sindico_email: currentDetailsCondo.sindico_email,
            tipo_gestao: 'COMPARTILHADA',
            administradora_nome: currentDetailsCondo.administradora_nome,
            administradora_email: currentDetailsCondo.administradora_email,
            administradora_activation_url: res.activation_url,
            administradora_activation_token: res.activation_token
          });
        }
      } catch (err) {
        showToast(`Erro ao reenviar convite da administradora: ${err.message}`, 'error');
      }
    });
  }

  // Reenviar convite do Subsíndico na aba dedicada
  if (tabBtnDetailsResendSubInvite) {
    tabBtnDetailsResendSubInvite.addEventListener('click', async () => {
      if (!currentDetailsCondo) return;
      try {
        const res = await fetchAdmin(`/condominios/${currentDetailsCondo.id}/resend-invite?papel=SUBSINDICO`, {
          method: 'POST'
        });
        showToast(res.message, 'success');
        if (res.activation_url) {
          openInviteSuccessModal({
            nome: currentDetailsCondo.nome,
            slug: currentDetailsCondo.slug,
            sindico_nome: currentDetailsCondo.sindico_nome,
            sindico_email: currentDetailsCondo.sindico_email,
            tem_subsindico: true,
            subsindico_nome: currentDetailsCondo.subsindico_nome,
            subsindico_email: currentDetailsCondo.subsindico_email,
            subsindico_activation_url: res.activation_url,
            subsindico_activation_token: res.activation_token
          });
        }
      } catch (err) {
        showToast(`Erro ao reenviar convite do subsíndico: ${err.message}`, 'error');
      }
    });
  }

  // Redefinir senha do Subsíndico na aba dedicada
  if (tabBtnDetailsResetSub) {
    tabBtnDetailsResetSub.addEventListener('click', () => {
      if (currentDetailsCondo && currentDetailsCondo.subsindico_email) {
        openResetPasswordModal(
          currentDetailsCondo.id,
          currentDetailsCondo.nome,
          currentDetailsCondo.subsindico_email,
          'Subsíndico(a) Responsável',
          'SUBSINDICO'
        );
      } else {
        showToast('Nenhum e-mail de subsíndico registrado.', 'warning');
      }
    });
  }

  // Atalho para cadastrar subsíndico a partir da aba dedicada
  if (tabBtnDetailsAddSub) {
    tabBtnDetailsAddSub.addEventListener('click', () => {
      if (currentDetailsCondo) {
        openEditCondoModal(currentDetailsCondo.id);
        setTimeout(() => {
          if (editTemSubsindico) {
            editTemSubsindico.checked = true;
            editTemSubsindico.dispatchEvent(new Event('change'));
          }
          if (editSubsindicoNome) editSubsindicoNome.focus();
        }, 300);
      }
    });
  }

  // Alternância de governança no Modal Editar
  function setEditGovernance(tipo) {
    const isComp = (tipo === 'COMPARTILHADA');
    if (radioEditGovCompartilhada) radioEditGovCompartilhada.checked = isComp;
    if (radioEditGovAutogestao) radioEditGovAutogestao.checked = !isComp;
    if (cardEditGovCompartilhada) cardEditGovCompartilhada.classList.toggle('active', isComp);
    if (cardEditGovAutogestao) cardEditGovAutogestao.classList.toggle('active', !isComp);
    if (wrapperEditAdmFields) wrapperEditAdmFields.classList.toggle('hidden', !isComp);
    if (editAdmNome) editAdmNome.required = isComp;
    if (editAdmEmail) editAdmEmail.required = isComp;
  }
  window.setEditGovernance = setEditGovernance;

  if (cardEditGovAutogestao) {
    cardEditGovAutogestao.addEventListener('click', () => setEditGovernance('AUTOGESTAO'));
  }
  if (cardEditGovCompartilhada) {
    cardEditGovCompartilhada.addEventListener('click', () => setEditGovernance('COMPARTILHADA'));
  }

  // Modal de Suspender / Reativar Condomínio
  if (btnCloseModalToggleStatus) btnCloseModalToggleStatus.addEventListener('click', closeToggleStatusModal);
  if (btnCancelToggleStatus) btnCancelToggleStatus.addEventListener('click', closeToggleStatusModal);
  if (formToggleCondoStatus) formToggleCondoStatus.addEventListener('submit', handleToggleStatusSubmit);

  // Busca e Filtros de Usuários da Rede (4 Dimensões)
  if (inputSearchUser) {
    inputSearchUser.addEventListener('input', debounce(() => loadGlobalUsers(), 300));
  }
  if (selectFilterUserCondo) {
    selectFilterUserCondo.addEventListener('change', () => loadGlobalUsers());
  }
  if (inputFilterUserUnit) {
    inputFilterUserUnit.addEventListener('input', debounce(() => loadGlobalUsers(), 300));
  }
  if (selectFilterUserRole) {
    selectFilterUserRole.addEventListener('change', () => loadGlobalUsers());
  }
  if (selectFilterUserStatus) {
    selectFilterUserStatus.addEventListener('change', () => loadGlobalUsers());
  }
  if (btnResetUserFilters) {
    btnResetUserFilters.addEventListener('click', () => {
      if (inputSearchUser) inputSearchUser.value = '';
      if (selectFilterUserCondo) selectFilterUserCondo.value = '';
      if (inputFilterUserUnit) inputFilterUserUnit.value = '';
      if (selectFilterUserRole) selectFilterUserRole.value = '';
      if (selectFilterUserStatus) selectFilterUserStatus.value = '';
      loadGlobalUsers();
      showToast('Filtros de usuários redefinidos.', 'info');
    });
  }
  if (btnRefreshUsers) {
    btnRefreshUsers.addEventListener('click', () => {
      loadGlobalUsers();
      showToast('Lista de usuários atualizada.', 'info');
    });
  }

  // Busca e Filtros de Usuários na Aba de Gestão do Condomínio
  if (inputDetailsUserSearch) {
    inputDetailsUserSearch.addEventListener('input', debounce(() => {
      if (currentDetailsCondo) loadCondoDetailsUsers(currentDetailsCondo.id);
    }, 300));
  }
  if (selectDetailsUserRole) {
    selectDetailsUserRole.addEventListener('change', () => {
      if (currentDetailsCondo) loadCondoDetailsUsers(currentDetailsCondo.id);
    });
  }
  if (btnRefreshDetailsUsers) {
    btnRefreshDetailsUsers.addEventListener('click', () => {
      if (currentDetailsCondo) {
        loadCondoDetailsUsers(currentDetailsCondo.id);
        showToast('Usuários do condomínio atualizados.', 'info');
      }
    });
  }

  // Form Broadcast Master & Live Preview
  if (formBroadcastMaster) {
    formBroadcastMaster.addEventListener('submit', handleBroadcastSubmit);
  }
  if (btnRefreshBroadcasts) {
    btnRefreshBroadcasts.addEventListener('click', () => {
      loadBroadcastHistory();
      showToast('Histórico de comunicados atualizado.', 'info');
    });
  }
  if (btnResetBroadcast) {
    btnResetBroadcast.addEventListener('click', resetBroadcastForm);
  }
  if (btnInsertBroadcastBullet) {
    btnInsertBroadcastBullet.addEventListener('click', insertBroadcastBullet);
  }
  if (categoryChipsGroup) {
    categoryChipsGroup.addEventListener('click', (e) => {
      const chip = e.target.closest('.btn-category-chip');
      if (!chip) return;
      categoryChipsGroup.querySelectorAll('.btn-category-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const cat = chip.getAttribute('data-cat') || 'GERAL';
      if (broadcastCategoria) broadcastCategoria.value = cat;
    });
  }
  if (broadcastMensagem) {
    broadcastMensagem.addEventListener('input', () => {
      if (broadcastCharCount) {
        const len = broadcastMensagem.value.length;
        broadcastCharCount.textContent = `${len} ${len === 1 ? 'caractere' : 'caracteres'}`;
      }
    });
  }
  if (broadcastDestino) {
    broadcastDestino.addEventListener('change', updateBroadcastAudienceBadge);
  }

  // Busca e Filtros de Condomínios
  inputSearchCondo.addEventListener('input', handleSearch);
  btnClearSearch.addEventListener('click', () => {
    inputSearchCondo.value = '';
    btnClearSearch.classList.add('hidden');
    applyCondoFilters();
  });

  if (statusFilterPills) {
    statusFilterPills.addEventListener('click', (e) => {
      const btn = e.target.closest('.filter-pill');
      if (!btn) return;
      statusFilterPills.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      currentStatusFilter = btn.dataset.status || 'ALL';
      applyCondoFilters();
    });
  }

  // Refresh
  btnRefresh.addEventListener('click', () => {
    loadMetrics();
    loadCondominios();
    showToast('Dados atualizados com sucesso.', 'info');
  });
  if (btnRefreshAudit) {
    btnRefreshAudit.addEventListener('click', () => {
      loadGlobalAudit();
      showToast('Trilha de auditoria atualizada.', 'info');
    });
  }

  if (currentToken) {
    showDashboard();
  } else {
    showLogin();
  }
});

// ============================================================================
// Controle de Abas Master
// ============================================================================

function switchTab(tab) {
  activeTab = tab;
  const tabConfigs = [
    { id: 'condos', btn: tabCondos, sec: sectionCondos },
    { id: 'condoDetails', btn: tabCondoDetails, sec: sectionCondoDetails },
    { id: 'users', btn: tabUsers, sec: sectionUsers },
    { id: 'audit', btn: tabAudit, sec: sectionAudit },
    { id: 'broadcast', btn: tabBroadcast, sec: sectionBroadcast },
    { id: 'supportSettings', btn: tabSupportSettings, sec: sectionSupportSettings }
  ];

  tabConfigs.forEach(t => {
    if (t.btn) t.btn.classList.toggle('active', t.id === tab);
    if (t.sec) t.sec.classList.toggle('hidden', t.id !== tab);
  });

  if (tab === 'users') {
    loadGlobalUsers();
  } else if (tab === 'condoDetails') {
    if (currentDetailsCondo) {
      loadCondoDetailsUsers(currentDetailsCondo.id);
    }
  } else if (tab === 'audit') {
    loadGlobalAudit();
  } else if (tab === 'broadcast') {
    populateBroadcastDestinations();
    loadBroadcastHistory();
    updateBroadcastAudienceBadge();
  } else if (tab === 'supportSettings') {
    loadSupportSettings();
  }
}

// ============================================================================
// Autenticação & Telas
// ============================================================================

function showLogin() {
  loginView.classList.remove('hidden');
  dashboardView.classList.add('hidden');
}

function showDashboard() {
  loginView.classList.add('hidden');
  dashboardView.classList.remove('hidden');
  loadMetrics();
  loadCondominios();
  loadSupportSettings();
}

formConsoleLogin.addEventListener('submit', async (e) => {
  e.preventDefault();
  loginError.classList.add('hidden');
  loginError.textContent = '';

  const email = document.getElementById('consoleEmail').value.trim();
  const senha = document.getElementById('consolePassword').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Falha na autenticação do Console.');
    }

    const data = await res.json();
    currentToken = data.access_token;
    localStorage.setItem('console_token', currentToken);
    if (data.user && data.user.email) {
      localStorage.setItem('console_user_email', data.user.email);
      const displayEmail = document.getElementById('displayAdminEmail');
      if (displayEmail) displayEmail.textContent = data.user.email;
    }
    showToast('Acesso master concedido com sucesso.', 'success');
    showDashboard();
  } catch (err) {
    loginError.textContent = err.message;
    loginError.classList.remove('hidden');
  }
});

btnLogout.addEventListener('click', () => {
  localStorage.removeItem('console_token');
  localStorage.removeItem('console_user_email');
  localStorage.removeItem('superadmin_token');
  currentToken = null;
  showLogin();
  showToast('Sessão master encerrada com segurança.');
});

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

  if (res.status === 401) {
    localStorage.removeItem('console_token');
    localStorage.removeItem('superadmin_token');
    currentToken = null;
    showLogin();
    showToast('Sessão expirada. Faça login novamente.', 'error');
    throw new Error('Sessão expirada.');
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    let errMsg = `Erro na requisição (${res.status})`;
    if (typeof data.detail === 'string') {
      errMsg = data.detail;
    } else if (Array.isArray(data.detail)) {
      errMsg = data.detail.map(d => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(' | ');
    } else if (data.message) {
      errMsg = data.message;
    }
    throw new Error(errMsg);
  }

  return res.json();
}

// ============================================================================
// Métricas & Dados
// ============================================================================

async function loadMetrics() {
  try {
    const m = await fetchAdmin('/metrics');
    metricCondosAtivos.textContent = m.condominios_ativos || 0;
    metricCondosTotal.textContent = `${m.total_condominios || 0} cadastrados no total (${m.condominios_bloqueados || 0} suspensos)`;
    metricTotalUnidades.textContent = m.total_unidades || 0;
    metricTotalMoradores.textContent = `${m.total_moradores || 0} moradores ativos`;
    metricTotalUsuarios.textContent = m.total_usuarios || 0;
    metricEventos.textContent = (m.total_reservas || 0) + (m.total_ocorrencias || 0);
  } catch (err) {
    console.error('Erro ao carregar métricas:', err);
  }
}

function escapeJsString(str) {
  if (!str) return '';
  return String(str).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

async function loadCondominios() {
  window.loadCondos = loadCondominios;
  if (condosListContainer) {
    condosListContainer.innerHTML = `
      <div class="condos-loading-state">
        <div class="spinner-dot"></div>
        <span>Carregando condomínios da rede...</span>
      </div>
    `;
  }
  try {
    const condos = await fetchAdmin('/condominios');
    allCondominios = condos || [];
    tabBadgeCondos.textContent = allCondominios.length;
    updateStatusPillCounts();
    applyCondoFilters();
    populateUserCondoFilterOptions();
  } catch (err) {
    if (condosListContainer) {
      condosListContainer.innerHTML = `
        <div class="condos-empty-state" style="border-color: rgba(244, 63, 94, 0.35);">
          <div class="empty-state-icon" style="background: rgba(244, 63, 94, 0.1); color: var(--rose);">
            <svg class="ico"><use href="#i-alert-circle"/></svg>
          </div>
          <h4>Erro ao carregar condomínios</h4>
          <p>${err.message}</p>
        </div>
      `;
    }
  }
}

function updateStatusPillCounts() {
  const total = allCondominios.length;
  const ativos = allCondominios.filter(c => c.status === 'ATIVO').length;
  const suspensos = allCondominios.filter(c => c.status === 'BLOQUEADO').length;

  if (countFilterAll) countFilterAll.textContent = total;
  if (countFilterAtivos) countFilterAtivos.textContent = ativos;
  if (countFilterSuspensos) countFilterSuspensos.textContent = suspensos;
}

function applyCondoFilters() {
  const query = (inputSearchCondo ? inputSearchCondo.value : '').toLowerCase().trim();
  if (btnClearSearch) {
    if (query) {
      btnClearSearch.classList.remove('hidden');
    } else {
      btnClearSearch.classList.add('hidden');
    }
  }

  const filtered = allCondominios.filter(c => {
    // Filtro por status
    if (currentStatusFilter === 'ATIVO' && c.status !== 'ATIVO') return false;
    if (currentStatusFilter === 'BLOQUEADO' && c.status !== 'BLOQUEADO') return false;

    // Filtro por busca de texto
    if (!query) return true;
    return (
      (c.nome && c.nome.toLowerCase().includes(query)) ||
      (c.cnpj && c.cnpj.toLowerCase().includes(query)) ||
      (c.slug && c.slug.toLowerCase().includes(query)) ||
      (c.sindico_nome && c.sindico_nome.toLowerCase().includes(query)) ||
      (c.sindico_email && c.sindico_email.toLowerCase().includes(query)) ||
      (c.sindico_telefone && c.sindico_telefone.toLowerCase().includes(query)) ||
      (c.endereco && c.endereco.toLowerCase().includes(query))
    );
  });

  renderCondominios(filtered);
}

function handleSearch() {
  applyCondoFilters();
}

function renderCondominios(condos) {
  if (!condosListContainer) return;

  if (!condos || condos.length === 0) {
    condosListContainer.innerHTML = `
      <div class="condos-empty-state">
        <div class="empty-state-icon">
          <svg class="ico"><use href="#i-search"/></svg>
        </div>
        <h4>Nenhum condomínio encontrado</h4>
        <p>Não há condomínios correspondentes aos filtros ou pesquisa aplicados.</p>
      </div>
    `;
    return;
  }

  const originUrl = window.location.origin;

  condosListContainer.innerHTML = condos.map(c => {
    const isAtivo = c.status === 'ATIVO';
    const statusBadge = isAtivo
      ? `<span class="badge-status-modern ativo"><span class="dot-status"></span> Ativo</span>`
      : `<span class="badge-status-modern bloqueado"><span class="dot-status"></span> Suspenso</span>`;

    const primaryColor = c.cor_primaria || '#3b82f6';
    const secondaryColor = c.cor_secundaria || '#1d4ed8';

    // Síndico info resumido (Nome + Avatar)
    let sindicoHtml = '';
    if (c.sindico_nome) {
      sindicoHtml = `
        <div class="sindico-block" title="Síndico: ${c.sindico_nome} (${c.sindico_email || 'sem e-mail'})">
          <div class="sindico-avatar" style="background: linear-gradient(135deg, ${primaryColor}, ${secondaryColor});">
            ${c.sindico_nome.charAt(0).toUpperCase()}
          </div>
          <div class="sindico-details">
            <strong class="sindico-name" title="${c.sindico_nome}">${c.sindico_nome}</strong>
            <span class="sindico-role-sub" style="display: flex; align-items: center; gap: 4px; margin-top: 2px;">
              <span>Síndico</span>
              ${c.tipo_gestao === 'COMPARTILHADA'
                ? `<span class="badge-governance compartilhada" title="Gestão Compartilhada com ${c.administradora_nome || 'Administradora'}">+ Adm</span>`
                : `<span class="badge-governance autogestao" title="Autogestão Exclusiva">Autogestão</span>`}
              ${c.tem_subsindico ? `<span class="badge-governance subsindico" title="Subsíndico(a): ${c.subsindico_nome || 'Cadastrado'}">+ Sub</span>` : ''}
            </span>
          </div>
        </div>
      `;
    } else {
      sindicoHtml = `
        <div class="sindico-empty">
          <span class="sindico-empty-dot">○</span>
          <span>Sem síndico</span>
        </div>
      `;
    }

    // Capacidade & Ocupação resumida
    const pct = c.limite_unidades > 0 ? Math.min(100, Math.round((c.total_unidades / c.limite_unidades) * 100)) : 0;
    const progressColor = pct > 90 ? 'var(--rose, #f43f5e)' : (pct > 70 ? 'var(--amber, #f59e0b)' : (c.cor_primaria || 'var(--primary, #3b82f6)'));

    const capacidadeHtml = `
      <div class="occupancy-block">
        <div class="occupancy-info-row">
          <span class="occupancy-count"><strong>${c.total_unidades}</strong> / ${c.limite_unidades} <span class="occupancy-label">aptos</span></span>
          <span class="occupancy-badge" style="color: ${progressColor}; background: ${progressColor}18; border: 1px solid ${progressColor}35;">${pct}%</span>
        </div>
        <div class="occupancy-progress-bg">
          <div class="occupancy-progress-fill" style="width: ${pct}%; background: linear-gradient(90deg, ${primaryColor}, ${progressColor});"></div>
        </div>
      </div>
    `;

    return `
      <div class="condo-hub-card" style="--card-accent: linear-gradient(180deg, ${primaryColor}, ${secondaryColor}); --card-glow: ${primaryColor};" onclick="goToCondoDetailsTab(${c.id})" title="Abrir gestão de ${c.nome}">
        <!-- Coluna 1: Identidade & Slug -->
        <div class="card-col-identity">
          <div class="condo-icon-box" style="background: ${primaryColor}18; border-color: ${primaryColor}40; color: ${primaryColor};">
            <svg class="ico"><use href="#i-building"/></svg>
          </div>
          <div class="condo-info-stack">
            <div class="condo-title-row">
              <h4 class="condo-hub-name" title="${c.nome}">${c.nome}</h4>
              ${statusBadge}
            </div>
            <div class="condo-slug-sub" title="Portal exclusivo: /c/${c.slug || ''}/">
              /c/${c.slug || ''}/
            </div>
          </div>
        </div>

        <!-- Coluna 2: Síndico Responsável -->
        <div class="card-col-sindico">
          ${sindicoHtml}
        </div>

        <!-- Coluna 3: Capacidade & Ocupação -->
        <div class="card-col-occupancy">
          ${capacidadeHtml}
        </div>

        <!-- Coluna 4: Ações Rápidas (Alinhamento Fixo 100% Preciso) -->
        <div class="card-col-actions">
          <div class="card-actions-group">
            <button type="button" class="btn-card-action manage" onclick="event.stopPropagation(); goToCondoDetailsTab(${c.id})" title="Abrir gestão completa e métricas">
              <span>Gerenciar</span>
              <span class="action-arrow">&rarr;</span>
            </button>
            <button type="button" class="btn-card-action enter" onclick="event.stopPropagation(); impersonateCondo(${c.id}, '${escapeJsString(c.nome)}', '${c.slug || ''}')" title="Acessar painel como Síndico (Suporte)">
              <svg class="ico"><use href="#i-external"/></svg>
              <span>Entrar</span>
            </button>
            ${c.id !== 1 ? `
            <button type="button" class="btn-card-action-icon delete" onclick="event.stopPropagation(); confirmDeleteCondo(${c.id}, '${escapeJsString(c.nome)}')" title="Excluir condomínio">
              <svg class="ico"><use href="#i-trash"/></svg>
            </button>` : `<div class="action-placeholder"></div>`}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// ============================================================================
// Aba Separada: Gestão do Condomínio (Dossiê Executivo Dedicado)
// ============================================================================

window.goToCondoDetailsTab = async function(condoId) {
  try {
    const condo = await fetchAdmin(`/condominios/${condoId}`);
    renderDedicatedCondoView(condo);
    switchTab('condoDetails');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    showToast(`Erro ao abrir gestão do condomínio: ${err.message}`, 'error');
  }
};

function renderDedicatedCondoView(condo) {
  if (!condo) return;
  currentDetailsCondo = condo;

  const pColor = condo.cor_primaria || '#3b82f6';
  const sColor = condo.cor_secundaria || '#1d4ed8';

  // Breadcrumbs e Título de Aba
  if (tabDetailsTitle) {
    tabDetailsTitle.textContent = 'Gestão: ' + (condo.nome.length > 18 ? condo.nome.substring(0, 18) + '...' : condo.nome);
  }
  if (tabBadgeDetails) {
    tabBadgeDetails.textContent = `#${condo.id}`;
  }
  if (tabDetailsCondoNameBreadcrumb) {
    tabDetailsCondoNameBreadcrumb.textContent = `${condo.nome} (ID: #${condo.id})`;
  }

  // Hero Card com Acabamento Dark Glass e Acento de Marca Sutil (Sem verde radioativo)
  if (tabDetailsBannerBg) {
    tabDetailsBannerBg.style.setProperty('--condo-accent', pColor);
  }
  if (tabDetailsAvatarBox) {
    tabDetailsAvatarBox.style.background = `${pColor}18`;
    tabDetailsAvatarBox.style.borderColor = `${pColor}40`;
    tabDetailsAvatarBox.style.color = pColor;
  }
  if (tabDetailsNomeDisplay) tabDetailsNomeDisplay.textContent = condo.nome;
  if (tabDetailsIdDisplay) tabDetailsIdDisplay.textContent = `ID: #${condo.id}`;
  if (tabDetailsCnpjDisplay) tabDetailsCnpjDisplay.textContent = condo.cnpj ? `CNPJ: ${condo.cnpj}` : 'CNPJ não informado';
  if (tabDetailsCreatedDisplay) tabDetailsCreatedDisplay.textContent = condo.criado_em ? `Cadastrado em ${new Date(condo.criado_em).toLocaleDateString('pt-BR')}` : '-';

  const isAtivo = condo.status === 'ATIVO';

  // Badge de Status no Título
  if (tabDetailsStatusBadge) {
    tabDetailsStatusBadge.className = `badge-status-modern ${isAtivo ? 'ativo' : 'bloqueado'}`;
    tabDetailsStatusBadge.innerHTML = `<span class="dot-status"></span> ${isAtivo ? 'Ativo' : 'Suspenso'}`;
  }

  // Pill de Capacidade & Plano no Card Executivo
  if (tabDetailsPlanoDisplay) {
    tabDetailsPlanoDisplay.className = 'hero-plan-tag';
    tabDetailsPlanoDisplay.textContent = `Limite: ${condo.limite_unidades || 44} aptos • Plano ${condo.plano || 'PADRÃO'}`;
  }

  // Botão Suspender / Reativar no Cabeçalho (Estilo Unificado & Sem Cores Estranhas)
  if (tabDetailsBtnToggleStatus) {
    if (isAtivo) {
      tabDetailsBtnToggleStatus.className = 'btn-header-action danger';
      tabDetailsBtnToggleStatus.innerHTML = `<svg class="ico"><use href="#i-lock"/></svg> <span id="tabDetailsToggleStatusLabel">Suspender Condomínio</span>`;
      tabDetailsBtnToggleStatus.title = 'Pausar temporariamente o acesso do condomínio';
      tabDetailsBtnToggleStatus.onclick = () => toggleStatus(condo.id, 'BLOQUEADO', condo.nome);
    } else {
      tabDetailsBtnToggleStatus.className = 'btn-header-action success';
      tabDetailsBtnToggleStatus.innerHTML = `<svg class="ico"><use href="#i-unlock"/></svg> <span id="tabDetailsToggleStatusLabel">Reativar Condomínio</span>`;
      tabDetailsBtnToggleStatus.title = 'Reativar condomínio e restabelecer acesso';
      tabDetailsBtnToggleStatus.onclick = () => toggleStatus(condo.id, 'ATIVO', condo.nome);
    }
  }

  // Motivo do bloqueio / suspensão
  const motivoBloqueio = condo.motivo_bloqueio ? condo.motivo_bloqueio.trim() : '';

  if (tabDetailsMotivoBannerWrapper && tabDetailsMotivoBanner) {
    if (!isAtivo && motivoBloqueio) {
      tabDetailsMotivoBanner.textContent = `Motivo: ${motivoBloqueio}`;
      tabDetailsMotivoBannerWrapper.classList.remove('hidden');
    } else {
      tabDetailsMotivoBannerWrapper.classList.add('hidden');
    }
  }

  // Alerta em destaque quando o condomínio estiver suspenso
  if (tabDetailsSuspendedAlert) {
    if (isAtivo) {
      tabDetailsSuspendedAlert.classList.add('hidden');
    } else {
      tabDetailsSuspendedAlert.classList.remove('hidden');
      if (tabDetailsBtnAlertReactivate) {
        tabDetailsBtnAlertReactivate.onclick = () => toggleStatus(condo.id, 'ATIVO', condo.nome);
      }
      if (tabDetailsMotivoBadge) {
        if (motivoBloqueio) {
          tabDetailsMotivoBadge.textContent = `Motivo: ${motivoBloqueio}`;
          tabDetailsMotivoBadge.classList.remove('hidden');
        } else {
          tabDetailsMotivoBadge.classList.add('hidden');
        }
      }
      if (tabDetailsMotivoDetail && tabDetailsMotivoText) {
        if (motivoBloqueio) {
          tabDetailsMotivoText.textContent = motivoBloqueio;
          tabDetailsMotivoDetail.classList.remove('hidden');
        } else {
          tabDetailsMotivoDetail.classList.add('hidden');
        }
      }
    }
  }

  // URL do portal
  const fullUrl = `${window.location.origin}/c/${condo.slug || ''}/`;
  if (tabDetailsUrlDisplay) tabDetailsUrlDisplay.textContent = fullUrl;
  if (tabBtnOpenCondoUrl) {
    tabBtnOpenCondoUrl.onclick = (e) => {
      if (e) e.preventDefault();
      impersonateCondo(condo.id, condo.nome, condo.slug);
    };
  }

  // Ações de cabeçalho
  if (tabDetailsBtnImpersonate) {
    tabDetailsBtnImpersonate.onclick = () => impersonateCondo(condo.id, condo.nome, condo.slug);
  }
  if (tabDetailsBtnEdit) {
    tabDetailsBtnEdit.onclick = () => openEditCondoModal(condo.id);
  }
  if (tabDetailsBtnResetPass) {
    tabDetailsBtnResetPass.onclick = () => openResetPasswordModal(condo.id, condo.nome, condo.sindico_email);
  }

  // KPIs
  const pct = condo.limite_unidades > 0 ? Math.min(100, Math.round((condo.total_unidades / condo.limite_unidades) * 100)) : 0;
  if (tabDetailsUnidadesCount) tabDetailsUnidadesCount.textContent = condo.total_unidades || 0;
  if (tabDetailsUnidadesSub) tabDetailsUnidadesSub.textContent = `de ${condo.limite_unidades} max (${pct}%)`;
  if (tabDetailsCapacityBar) {
    tabDetailsCapacityBar.style.width = `${pct}%`;
    tabDetailsCapacityBar.style.backgroundColor = pct > 90 ? 'var(--rose)' : (pct > 70 ? 'var(--amber)' : pColor);
  }
  if (tabDetailsMoradoresCount) tabDetailsMoradoresCount.textContent = `${condo.total_moradores || 0} moradores cadastrados`;

  if (tabDetailsEncomendasCount) tabDetailsEncomendasCount.textContent = condo.total_encomendas_pendentes || 0;
  if (tabDetailsPorteirosCount) tabDetailsPorteirosCount.textContent = `${condo.total_porteiros || 0} porteiros na equipe`;

  const oco = condo.total_ocorrencias_abertas || 0;
  if (tabDetailsOcorrenciasCount) tabDetailsOcorrenciasCount.textContent = oco;
  if (tabDetailsOcorrenciasStatus) {
    tabDetailsOcorrenciasStatus.textContent = oco > 0 ? `${oco} chamados pendentes de resposta` : 'Nenhum chamado aberto';
  }

  if (tabDetailsAreasCount) tabDetailsAreasCount.textContent = condo.total_areas_comuns || 0;
  if (tabDetailsReservasCount) tabDetailsReservasCount.textContent = `${condo.total_reservas || 0} reservas registradas`;

  // Síndico
  if (condo.sindico_nome) {
    if (tabDetailsSindicoAvatar) {
      tabDetailsSindicoAvatar.textContent = condo.sindico_nome.charAt(0).toUpperCase();
      tabDetailsSindicoAvatar.style.background = `linear-gradient(135deg, ${pColor}, ${sColor})`;
    }
    if (tabDetailsSindicoNome) tabDetailsSindicoNome.textContent = condo.sindico_nome;
    if (tabDetailsSindicoEmail) tabDetailsSindicoEmail.textContent = condo.sindico_email || 'Sem e-mail cadastrado';

    if (condo.sindico_telefone) {
      if (tabDetailsSindicoTelefoneBadge) {
        tabDetailsSindicoTelefoneBadge.textContent = condo.sindico_telefone;
        tabDetailsSindicoTelefoneBadge.classList.remove('hidden');
      }
      const digits = condo.sindico_telefone.replace(/\D/g, '');
      if (digits.length >= 10 && tabDetailsSindicoWhatsApp) {
        tabDetailsSindicoWhatsApp.href = `https://wa.me/55${digits}`;
        tabDetailsSindicoWhatsApp.classList.remove('hidden');
      } else if (tabDetailsSindicoWhatsApp) {
        tabDetailsSindicoWhatsApp.classList.add('hidden');
      }
    } else {
      if (tabDetailsSindicoTelefoneBadge) tabDetailsSindicoTelefoneBadge.textContent = 'Sem telefone';
      if (tabDetailsSindicoWhatsApp) tabDetailsSindicoWhatsApp.classList.add('hidden');
    }
  } else {
    if (tabDetailsSindicoAvatar) tabDetailsSindicoAvatar.textContent = '?';
    if (tabDetailsSindicoNome) tabDetailsSindicoNome.textContent = 'Nenhum síndico vinculado';
    if (tabDetailsSindicoEmail) tabDetailsSindicoEmail.textContent = 'Cadastre ou edite para vincular um síndico';
    if (tabDetailsSindicoTelefoneBadge) tabDetailsSindicoTelefoneBadge.textContent = '-';
    if (tabDetailsSindicoWhatsApp) tabDetailsSindicoWhatsApp.classList.add('hidden');
  }

  // Administradora (se Gestão Compartilhada)
  const isCompartilhada = (condo.tipo_gestao === 'COMPARTILHADA');
  if (tabDetailsAdmBox) {
    if (isCompartilhada) {
      tabDetailsAdmBox.classList.remove('hidden');
      if (tabDetailsAdmNome) tabDetailsAdmNome.textContent = condo.administradora_nome || 'Administradora Parceira';
      if (tabDetailsAdmEmail) tabDetailsAdmEmail.textContent = condo.administradora_email || 'Sem e-mail cadastrado';
      if (condo.administradora_telefone) {
        if (tabDetailsAdmTelefoneBadge) {
          tabDetailsAdmTelefoneBadge.textContent = condo.administradora_telefone;
          tabDetailsAdmTelefoneBadge.classList.remove('hidden');
        }
        const admDigits = condo.administradora_telefone.replace(/\D/g, '');
        if (admDigits.length >= 10 && tabDetailsAdmWhatsApp) {
          tabDetailsAdmWhatsApp.href = `https://wa.me/55${admDigits}`;
          tabDetailsAdmWhatsApp.classList.remove('hidden');
        } else if (tabDetailsAdmWhatsApp) {
          tabDetailsAdmWhatsApp.classList.add('hidden');
        }
      } else {
        if (tabDetailsAdmTelefoneBadge) tabDetailsAdmTelefoneBadge.classList.add('hidden');
        if (tabDetailsAdmWhatsApp) tabDetailsAdmWhatsApp.classList.add('hidden');
      }
    } else {
      tabDetailsAdmBox.classList.add('hidden');
    }
  }

  // Subsíndico(a) Responsável
  const hasSub = !!(condo.tem_subsindico && condo.subsindico_nome);
  if (hasSub) {
    if (tabDetailsSubBox) tabDetailsSubBox.classList.remove('hidden');
    if (tabDetailsNoSubBox) tabDetailsNoSubBox.classList.add('hidden');
    if (tabDetailsSubAvatar) {
      tabDetailsSubAvatar.textContent = condo.subsindico_nome.charAt(0).toUpperCase();
    }
    if (tabDetailsSubNome) tabDetailsSubNome.textContent = condo.subsindico_nome;
    if (tabDetailsSubEmail) tabDetailsSubEmail.textContent = condo.subsindico_email || 'Sem e-mail cadastrado';

    if (tabDetailsSubStatusBadge) {
      const isSubAtivo = condo.subsindico_ativo !== false;
      tabDetailsSubStatusBadge.className = `badge-status-modern ${isSubAtivo ? 'ativo' : 'bloqueado'}`;
      tabDetailsSubStatusBadge.innerHTML = `<span class="dot-status"></span> ${isSubAtivo ? 'Ativo' : 'Pendente'}`;
    }

    if (condo.subsindico_telefone) {
      if (tabDetailsSubTelefoneBadge) {
        tabDetailsSubTelefoneBadge.textContent = condo.subsindico_telefone;
        tabDetailsSubTelefoneBadge.classList.remove('hidden');
      }
      const subDigits = condo.subsindico_telefone.replace(/\D/g, '');
      if (subDigits.length >= 10 && tabDetailsSubWhatsApp) {
        tabDetailsSubWhatsApp.href = `https://wa.me/55${subDigits}`;
        tabDetailsSubWhatsApp.classList.remove('hidden');
      } else if (tabDetailsSubWhatsApp) {
        tabDetailsSubWhatsApp.classList.add('hidden');
      }
    } else {
      if (tabDetailsSubTelefoneBadge) tabDetailsSubTelefoneBadge.classList.add('hidden');
      if (tabDetailsSubWhatsApp) tabDetailsSubWhatsApp.classList.add('hidden');
    }
  } else {
    if (tabDetailsSubBox) tabDetailsSubBox.classList.add('hidden');
    if (tabDetailsNoSubBox) tabDetailsNoSubBox.classList.remove('hidden');
  }

  // Infraestrutura
  if (tabDetailsEnderecoVal) tabDetailsEnderecoVal.textContent = condo.endereco || 'Endereço não informado';
  if (tabDetailsTelefoneVal) tabDetailsTelefoneVal.textContent = condo.telefone || 'Não informado';
  if (tabDetailsEmailVal) tabDetailsEmailVal.textContent = condo.email_contato || 'Não informado';
  if (tabDetailsDotPrimaria) tabDetailsDotPrimaria.style.backgroundColor = pColor;
  if (tabDetailsDotSecundaria) tabDetailsDotSecundaria.style.backgroundColor = sColor;

  // Mostra conteúdo ativo e esconde empty state
  if (detailsEmptyState) detailsEmptyState.classList.add('hidden');
  if (detailsActiveContent) detailsActiveContent.classList.remove('hidden');

  // Carrega e renderiza todos os usuários vinculados a este condomínio
  loadCondoDetailsUsers(condo.id);
}

// Popula opções de condomínio no filtro da Central de Usuários
function populateUserCondoFilterOptions() {
  if (!selectFilterUserCondo) return;
  const currentVal = selectFilterUserCondo.value;
  selectFilterUserCondo.innerHTML = `<option value="">Todos os Condomínios</option>` +
    allCondominios.map(c => `<option value="${c.id}">${c.nome}</option>`).join('');
  if (currentVal) selectFilterUserCondo.value = currentVal;
}

// ============================================================================
// Gestão de Usuários da Rede (Super Admin - 4 Dimensões de Filtros)
// ============================================================================

let allGlobalUsers = [];

async function loadGlobalUsers() {
  if (!usersTableBody) return;
  usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4">Carregando usuários da rede...</td></tr>`;
  try {
    const q = inputSearchUser ? inputSearchUser.value.trim() : '';
    const condoId = selectFilterUserCondo ? selectFilterUserCondo.value : '';
    const unit = inputFilterUserUnit ? inputFilterUserUnit.value.trim() : '';
    const role = selectFilterUserRole ? selectFilterUserRole.value : '';
    const status = selectFilterUserStatus ? selectFilterUserStatus.value : '';

    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (condoId) params.set('condominio_id', condoId);
    if (unit) params.set('unidade', unit);
    if (role) params.set('tipo', role);
    if (status) params.set('status', status);

    const users = await fetchAdmin(`/users?${params.toString()}`);
    allGlobalUsers = users || [];
    if (tabBadgeUsers) tabBadgeUsers.textContent = allGlobalUsers.length;
    renderGlobalUsers(allGlobalUsers);
  } catch (err) {
    usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4" style="color: var(--rose);">Erro ao carregar usuários: ${err.message}</td></tr>`;
  }
}

function renderGlobalUsers(users) {
  if (!users || users.length === 0) {
    usersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Nenhum usuário encontrado com os filtros aplicados.</td></tr>`;
    return;
  }

  usersTableBody.innerHTML = users.map(u => {
    const isAtivo = u.ativo;
    const statusBadge = isAtivo
      ? `<span class="badge-status ativo">● Ativo</span>`
      : `<span class="badge-status bloqueado">● Bloqueado</span>`;

    const roleClass = u.tipo_usuario === 'SINDICO' ? 'enterprise' : (u.tipo_usuario === 'PORTARIA' ? 'pro' : '');
    const roleBadge = `<span class="badge-plan ${roleClass}">${u.tipo_usuario}</span>`;

    const toggleBtn = isAtivo
      ? `<button type="button" class="btn-action block" onclick="toggleUserStatus(${u.id}, '${escapeJsString(u.nome)}')" title="Bloquear acesso do usuário"><svg class="ico"><use href="#i-lock"/></svg> <span>Bloquear</span></button>`
      : `<button type="button" class="btn-action unblock" onclick="toggleUserStatus(${u.id}, '${escapeJsString(u.nome)}')" title="Liberar acesso do usuário"><svg class="ico"><use href="#i-unlock"/></svg> <span>Liberar</span></button>`;

    return `
      <tr>
        <td>
          <div class="sindico-card-cell">
            <div class="sindico-avatar">
              ${(u.nome || 'U').charAt(0).toUpperCase()}
            </div>
            <div class="sindico-meta">
              <strong>${u.nome}</strong>
              <small class="muted-sm">${u.email}</small>
              ${u.telefone ? `<small class="muted-sm">${u.telefone}</small>` : ''}
            </div>
          </div>
        </td>
        <td>
          <strong>${u.condominio_nome || 'Geral'}</strong>
          ${u.unidade_identificador ? `<br/><small class="muted-sm">${u.unidade_identificador}</small>` : ''}
        </td>
        <td>${roleBadge}</td>
        <td>${statusBadge}</td>
        <td class="text-right">
          <div class="table-actions">
            <button type="button" class="btn-action key" onclick="openResetUserPasswordModal(${u.id})" title="Redefinir senha de acesso deste usuário">
              <svg class="ico"><use href="#i-key"/></svg> <span>Senha</span>
            </button>
            ${toggleBtn}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// ============================================================================
// Usuários Vinculados ao Condomínio Selecionado (Aba Gestão do Condomínio)
// ============================================================================

let currentCondoDetailsUsers = [];

async function loadCondoDetailsUsers(condoId) {
  if (!tabDetailsUsersTableBody) return;
  tabDetailsUsersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4">Carregando usuários do condomínio...</td></tr>`;
  try {
    const q = inputDetailsUserSearch ? inputDetailsUserSearch.value.trim() : '';
    const role = selectDetailsUserRole ? selectDetailsUserRole.value : '';

    const params = new URLSearchParams();
    params.set('condominio_id', condoId);
    if (q) params.set('q', q);
    if (role) params.set('tipo', role);

    const users = await fetchAdmin(`/users?${params.toString()}`);
    currentCondoDetailsUsers = users || [];

    if (tabDetailsUsersBadgeCount) {
      tabDetailsUsersBadgeCount.textContent = `${currentCondoDetailsUsers.length} usuários`;
    }

    renderCondoDetailsUsers(currentCondoDetailsUsers);
  } catch (err) {
    tabDetailsUsersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4" style="color: var(--rose);">Erro ao carregar usuários: ${err.message}</td></tr>`;
  }
}

function renderCondoDetailsUsers(users) {
  if (!tabDetailsUsersTableBody) return;
  if (!users || users.length === 0) {
    tabDetailsUsersTableBody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Nenhum usuário cadastrado ou correspondente aos filtros neste condomínio.</td></tr>`;
    return;
  }

  tabDetailsUsersTableBody.innerHTML = users.map(u => {
    const isAtivo = u.ativo;
    const statusBadge = isAtivo
      ? `<span class="badge-status ativo">● Ativo</span>`
      : `<span class="badge-status bloqueado">● Bloqueado</span>`;

    const roleClass = u.tipo_usuario === 'SINDICO' ? 'enterprise' : (u.tipo_usuario === 'PORTARIA' ? 'pro' : '');
    const roleBadge = `<span class="badge-plan ${roleClass}">${u.tipo_usuario}</span>`;

    const toggleBtn = isAtivo
      ? `<button type="button" class="btn-action block" onclick="toggleUserStatus(${u.id}, '${escapeJsString(u.nome)}', true)" title="Bloquear acesso do usuário"><svg class="ico"><use href="#i-lock"/></svg> <span>Bloquear</span></button>`
      : `<button type="button" class="btn-action unblock" onclick="toggleUserStatus(${u.id}, '${escapeJsString(u.nome)}', true)" title="Liberar acesso do usuário"><svg class="ico"><use href="#i-unlock"/></svg> <span>Liberar</span></button>`;

    const unitText = u.unidade_identificador || (u.tipo_usuario === 'PORTARIA' ? 'Guarita / Portaria' : (u.tipo_usuario === 'SINDICO' ? 'Administração Predial' : 'Sem unidade vinculada'));

    return `
      <tr>
        <td>
          <div class="sindico-card-cell">
            <div class="sindico-avatar">
              ${(u.nome || 'U').charAt(0).toUpperCase()}
            </div>
            <div class="sindico-meta">
              <strong>${u.nome}</strong>
              <small class="muted-sm">${u.email}</small>
              ${u.telefone ? `<small class="muted-sm">${u.telefone}</small>` : ''}
            </div>
          </div>
        </td>
        <td>
          <strong>${unitText}</strong>
        </td>
        <td>${roleBadge}</td>
        <td>${statusBadge}</td>
        <td class="text-right">
          <div class="table-actions">
            <button type="button" class="btn-action key" onclick="openResetUserPasswordModal(${u.id})" title="Redefinir senha de acesso deste usuário">
              <svg class="ico"><use href="#i-key"/></svg> <span>Senha</span>
            </button>
            ${toggleBtn}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

window.toggleUserStatus = async function(userId, userName, fromDetails = false) {
  try {
    const res = await fetchAdmin(`/users/${userId}/toggle-status`, { method: 'PATCH' });
    showToast(res.message, 'success');
    loadGlobalUsers();
    if (fromDetails && currentDetailsCondo) {
      loadCondoDetailsUsers(currentDetailsCondo.id);
    }
  } catch (err) {
    showToast(`Erro ao alterar status: ${err.message}`, 'error');
  }
};

window.openResetUserPasswordModal = function(userId) {
  const u = (allGlobalUsers && allGlobalUsers.find(x => x.id === userId))
    || (currentCondoDetailsUsers && currentCondoDetailsUsers.find(x => x.id === userId));
  if (!u) {
    showToast('Usuário não localizado na listagem atual.', 'error');
    return;
  }

  if (resetTargetUserId) resetTargetUserId.value = u.id;
  if (resetUserNomeDisplay) resetUserNomeDisplay.textContent = u.nome || 'Usuário';
  if (resetUserEmailDisplay) resetUserEmailDisplay.textContent = u.email || '-';
  if (resetUserAvatar) resetUserAvatar.textContent = (u.nome || 'U').charAt(0).toUpperCase();

  // Badge de Perfil
  if (resetUserRoleBadge) {
    const roleClass = u.tipo_usuario === 'SINDICO' ? 'enterprise' : (u.tipo_usuario === 'PORTARIA' ? 'pro' : '');
    resetUserRoleBadge.className = `badge-plan ${roleClass}`.trim();
    resetUserRoleBadge.textContent = u.tipo_usuario || 'USUÁRIO';
  }

  // Condomínio / Unidade
  if (resetUserCondoDisplay) {
    const condoName = u.condominio_nome || 'Geral / Sem condomínio vinculado';
    const unitInfo = u.unidade_identificador ? ` • Unidade: ${u.unidade_identificador}` : '';
    resetUserCondoDisplay.textContent = `${condoName}${unitInfo}`;
  }

  // Gerar senha segura automática por conveniência
  const tempPass = generateStrongPassword();
  if (resetUserNovaSenha) {
    resetUserNovaSenha.value = tempPass;
    resetUserNovaSenha.type = 'text'; // Visível inicialmente para conferência
  }
  if (iconEyeUserPw) {
    iconEyeUserPw.innerHTML = '<use href="#i-eye"/>';
  }

  if (resetUserForceChange) {
    resetUserForceChange.checked = true;
  }

  if (modalResetUserPassword) {
    modalResetUserPassword.classList.remove('hidden');
  }

  setTimeout(() => {
    if (resetUserNovaSenha) {
      resetUserNovaSenha.focus();
      resetUserNovaSenha.select();
    }
  }, 100);
};

// Mantém compatibilidade com qualquer chamada legada
window.openResetUserPasswordPrompt = function(userId) {
  window.openResetUserPasswordModal(userId);
};

// ============================================================================
// Central de Broadcast Master
// ============================================================================

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function populateBroadcastDestinations() {
  if (!broadcastDestino) return;
  const currentVal = broadcastDestino.value;
  broadcastDestino.innerHTML = `<option value="">Todos os Condomínios Ativos da Rede (Broadcast Geral)</option>` +
    allCondominios.map(c => `<option value="${c.id}">Apenas: ${escapeHtml(c.nome)} (ID: #${c.id})</option>`).join('');
  if (currentVal) broadcastDestino.value = currentVal;
  updateBroadcastAudienceBadge();
}

function updateBroadcastAudienceBadge() {
  if (!broadcastAudienceBadge) return;
  const destinoVal = broadcastDestino ? broadcastDestino.value : '';
  if (!destinoVal) {
    broadcastAudienceBadge.textContent = 'Rede Completa';
    broadcastAudienceBadge.className = 'badge-plan pro';
  } else {
    const condo = allCondominios.find(c => String(c.id) === String(destinoVal));
    const nome = condo ? condo.nome : `Condomínio #${destinoVal}`;
    broadcastAudienceBadge.textContent = nome;
    broadcastAudienceBadge.className = 'badge-role-gold';
  }
}

function insertBroadcastBullet() {
  if (!broadcastMensagem) return;
  const el = broadcastMensagem;
  const start = el.selectionStart;
  const end = el.selectionEnd;
  const text = el.value;
  const bullet = '• ';
  el.value = text.substring(0, start) + bullet + text.substring(end);
  el.selectionStart = el.selectionEnd = start + bullet.length;
  el.focus();
  if (broadcastCharCount) {
    const len = el.value.length;
    broadcastCharCount.textContent = `${len} ${len === 1 ? 'caractere' : 'caracteres'}`;
  }
}

function resetBroadcastForm() {
  if (formBroadcastMaster) formBroadcastMaster.reset();
  if (broadcastCategoria) broadcastCategoria.value = 'GERAL';
  if (categoryChipsGroup) {
    categoryChipsGroup.querySelectorAll('.btn-category-chip').forEach(c => {
      c.classList.toggle('active', c.getAttribute('data-cat') === 'GERAL');
    });
  }
  if (broadcastCharCount) broadcastCharCount.textContent = '0 caracteres';
  updateBroadcastAudienceBadge();
}

function getBroadcastCatBadgeHtml(cat) {
  const c = (cat || 'GERAL').toUpperCase();
  if (c === 'URGENTE') {
    return `<span class="badge-role-gold" style="background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3);">URGENTE</span>`;
  }
  if (c === 'MANUTENCAO') {
    return `<span class="badge-role-gold" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">MANUTENÇÃO</span>`;
  }
  if (c === 'ASSEMBLEIA' || c === 'DIRETORIA') {
    return `<span class="badge-role-gold" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);">DIRETORIA</span>`;
  }
  return `<span class="badge-role-gold" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);">GERAL</span>`;
}

async function loadBroadcastHistory() {
  if (!broadcastHistoryTableBody) return;
  try {
    const broadcasts = await fetchAdmin('/broadcasts');
    if (badgeBroadcastHistoryCount) {
      badgeBroadcastHistoryCount.textContent = `${broadcasts.length} ${broadcasts.length === 1 ? 'disparo' : 'disparos'}`;
    }

    if (!broadcasts || broadcasts.length === 0) {
      broadcastHistoryTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center py-4" style="color: var(--text-dim);">
            Nenhum comunicado master transmitido ainda.
          </td>
        </tr>
      `;
      return;
    }

    broadcastHistoryTableBody.innerHTML = broadcasts.map(item => {
      const dataStr = item.criado_em ? new Date(item.criado_em).toLocaleString('pt-BR') : '-';
      const catBadge = getBroadcastCatBadgeHtml(item.categoria);
      const isAtivo = item.ativo !== false;

      const statusBadge = isAtivo
        ? `<span class="badge-status-on" title="Visível no mural dos moradores"><span class="dot-status"></span> No Mural</span>`
        : `<span class="badge-status-off" style="background: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.2);" title="Oculto do mural dos clientes"><span class="dot-status" style="background: #94a3b8;"></span> Oculto dos Clientes</span>`;

      const targetBadge = item.destino_tipo === 'TODOS'
        ? `<span class="badge-plan pro" style="font-size: 0.72rem;">Rede Global (${item.total_condominios} condos)</span>`
        : `<span class="badge-role-gold" style="font-size: 0.72rem;">${escapeHtml(item.destino_nome)}</span>`;

      const toggleBtn = isAtivo
        ? `<button type="button" class="btn-action hide-broadcast" onclick="toggleBroadcastVisibility('${item.group_key}', true)" title="Ocultar do mural dos clientes">
             <svg class="ico" style="width: 14px; height: 14px;"><use href="#i-eye-off"/></svg> <span>Ocultar</span>
           </button>`
        : `<button type="button" class="btn-action reexibir-broadcast" onclick="toggleBroadcastVisibility('${item.group_key}', false)" title="Reexibir no mural dos clientes">
             <svg class="ico" style="width: 14px; height: 14px;"><use href="#i-eye"/></svg> <span>Reexibir</span>
           </button>`;

      const deleteBtn = `
        <button type="button" class="btn-action delete-broadcast" onclick="deleteBroadcastItem('${item.group_key}', this)" title="Excluir comunicado definitivamente">
          <svg class="ico" style="width: 14px; height: 14px; pointer-events: none;"><use href="#i-trash" style="pointer-events: none;"/></svg>
        </button>
      `;

      return `
        <tr>
          <td style="white-space: nowrap; font-size: 0.85rem; color: var(--text-dim);">${dataStr}</td>
          <td>${catBadge}</td>
          <td>
            <div style="font-weight: 600; color: #fff; margin-bottom: 2px;">${escapeHtml(item.titulo)}</div>
            <div style="font-size: 0.8rem; color: var(--text-dim); max-width: 440px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(item.mensagem)}</div>
          </td>
          <td>${targetBadge}</td>
          <td>${statusBadge}</td>
          <td class="text-right">
            <div style="display: inline-flex; align-items: center; gap: 8px; justify-content: flex-end;">
              ${toggleBtn}
              ${deleteBtn}
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    broadcastHistoryTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="text-center py-4 text-danger">
          Erro ao carregar histórico: ${escapeHtml(err.message)}
        </td>
      </tr>
    `;
  }
}

window.toggleBroadcastVisibility = async function(groupKey, currentActive) {
  try {
    const res = await fetchAdmin(`/broadcasts/${encodeURIComponent(groupKey)}/toggle-visibility`, {
      method: 'PATCH'
    });
    showToast(res.message || 'Visibilidade alterada com sucesso!', 'success');
  } catch (err) {
    showToast(`Erro ao alterar visibilidade: ${err.message}`, 'error');
  } finally {
    await loadBroadcastHistory();
  }
};

window.deleteBroadcastItem = async function(groupKey, btnEl) {
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.style.opacity = '0.5';
  }
  try {
    const res = await fetchAdmin(`/broadcasts/${encodeURIComponent(groupKey)}`, {
      method: 'DELETE'
    });
    showToast(res.message || 'Comunicado excluído com sucesso!', 'success');
  } catch (err) {
    showToast(`Erro ao excluir: ${err.message}`, 'error');
  } finally {
    await loadBroadcastHistory();
  }
};

async function handleBroadcastSubmit(e) {
  e.preventDefault();
  const titulo = broadcastTitulo.value.trim();
  const categoria = broadcastCategoria.value;
  const destinoVal = broadcastDestino.value;
  const mensagem = broadcastMensagem.value.trim();

  if (!titulo || !mensagem) {
    showToast('Preencha título e mensagem do comunicado.', 'error');
    return;
  }

  const payload = {
    titulo,
    categoria,
    mensagem,
    condominio_id: destinoVal ? parseInt(destinoVal, 10) : null
  };

  btnSendBroadcast.disabled = true;
  btnSendBroadcast.innerHTML = '<span>Transmitindo comunicado...</span>';

  try {
    const res = await fetchAdmin('/broadcast', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    showToast(res.message || 'Comunicado transmitido com sucesso!', 'success');
    resetBroadcastForm();
    await loadBroadcastHistory();
  } catch (err) {
    showToast(`Erro ao transmitir comunicado: ${err.message}`, 'error');
  } finally {
    btnSendBroadcast.disabled = false;
    btnSendBroadcast.innerHTML = '<svg class="ico"><use href="#i-mail"/></svg> <span>Transmitir Comunicado Master</span>';
  }
}

// ============================================================================
// Modal: Dossiê Executivo do Condomínio
// ============================================================================

window.openCondoDetails = async function(condoId) {
  try {
    const condo = await fetchAdmin(`/condominios/${condoId}`);
    currentDetailsCondo = condo;

    // Banner
    const pColor = condo.cor_primaria || '#3b82f6';
    const sColor = condo.cor_secundaria || '#1d4ed8';
    detailsBannerBg.style.background = `linear-gradient(135deg, ${pColor} 0%, #0f172a 80%)`;
    detailsCondoNomeDisplay.textContent = condo.nome;
    detailsIdDisplay.textContent = `ID: #${condo.id}`;
    detailsCnpjDisplay.textContent = condo.cnpj ? `CNPJ: ${condo.cnpj}` : 'CNPJ não informado';
    detailsCreatedDisplay.textContent = condo.criado_em ? `Cadastrado em ${new Date(condo.criado_em).toLocaleDateString('pt-BR')}` : '-';

    const isAtivo = condo.status === 'ATIVO';
    detailsStatusBadge.className = `badge-status ${isAtivo ? 'ativo' : 'bloqueado'}`;
    detailsStatusBadge.textContent = isAtivo ? '● Ativo' : '● Suspenso';

    // URL
    const fullUrl = `${window.location.origin}/c/${condo.slug || ''}/`;
    detailsUrlDisplay.textContent = fullUrl;
    btnOpenCondoUrl.href = `/c/${condo.slug || ''}/`;

    // KPIs
    const pct = condo.limite_unidades > 0 ? Math.min(100, Math.round((condo.total_unidades / condo.limite_unidades) * 100)) : 0;
    detailsUnidadesCount.textContent = condo.total_unidades || 0;
    detailsUnidadesSub.textContent = `de ${condo.limite_unidades} max (${pct}%)`;
    detailsCapacityBar.style.width = `${pct}%`;
    detailsCapacityBar.style.backgroundColor = pct > 90 ? 'var(--rose)' : (pct > 70 ? 'var(--amber)' : pColor);
    detailsMoradoresCount.textContent = `${condo.total_moradores || 0} moradores cadastrados`;

    detailsEncomendasCount.textContent = condo.total_encomendas_pendentes || 0;
    detailsPorteirosCount.textContent = `${condo.total_porteiros || 0} porteiros na equipe`;

    const oco = condo.total_ocorrencias_abertas || 0;
    detailsOcorrenciasCount.textContent = oco;
    detailsOcorrenciasStatus.textContent = oco > 0 ? `${oco} chamados pendentes de resposta` : 'Nenhum chamado aberto';

    detailsAreasCount.textContent = condo.total_areas_comuns || 0;
    detailsReservasCount.textContent = `${condo.total_reservas || 0} reservas registradas`;

    // Síndico
    if (condo.sindico_nome) {
      detailsSindicoAvatar.textContent = condo.sindico_nome.charAt(0).toUpperCase();
      detailsSindicoAvatar.style.background = `linear-gradient(135deg, ${pColor}, ${sColor})`;
      detailsSindicoNome.textContent = condo.sindico_nome;
      detailsSindicoEmail.textContent = condo.sindico_email || 'Sem e-mail cadastrado';

      if (condo.sindico_telefone) {
        detailsSindicoTelefoneBadge.textContent = condo.sindico_telefone;
        detailsSindicoTelefoneBadge.classList.remove('hidden');
        const digits = condo.sindico_telefone.replace(/\D/g, '');
        if (digits.length >= 10) {
          detailsSindicoWhatsApp.href = `https://wa.me/55${digits}`;
          detailsSindicoWhatsApp.classList.remove('hidden');
        } else {
          detailsSindicoWhatsApp.classList.add('hidden');
        }
      } else {
        detailsSindicoTelefoneBadge.textContent = 'Sem telefone';
        detailsSindicoWhatsApp.classList.add('hidden');
      }
    } else {
      detailsSindicoAvatar.textContent = '?';
      detailsSindicoNome.textContent = 'Nenhum síndico vinculado';
      detailsSindicoEmail.textContent = 'Cadastre ou edite para vincular um síndico';
      detailsSindicoTelefoneBadge.textContent = '-';
      detailsSindicoWhatsApp.classList.add('hidden');
    }

    // Infraestrutura
    detailsEnderecoVal.textContent = condo.endereco || 'Endereço não informado';
    detailsTelefoneVal.textContent = condo.telefone || 'Não informado';
    detailsEmailVal.textContent = condo.email_contato || 'Não informado';
    detailsDotPrimaria.style.backgroundColor = pColor;
    detailsDotSecundaria.style.backgroundColor = sColor;

    modalCondoDetails.classList.remove('hidden');
  } catch (err) {
    showToast(`Erro ao abrir dossiê: ${err.message}`, 'error');
  }
};

function closeCondoDetailsModal() {
  modalCondoDetails.classList.add('hidden');
  currentDetailsCondo = null;
}

// ============================================================================
// Auditoria Global (LGPD)
// ============================================================================

async function loadGlobalAudit() {
  auditTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4">Carregando logs de auditoria da rede...</td></tr>`;
  try {
    const logs = await fetchAdmin('/audit?limit=100');
    if (!logs || logs.length === 0) {
      auditTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Nenhum evento registrado até o momento.</td></tr>`;
      return;
    }

    auditTableBody.innerHTML = logs.map(l => {
      const dataFormatada = l.data_hora ? new Date(l.data_hora).toLocaleString('pt-BR') : '-';
      const statusBadge = l.sucesso
        ? `<span class="badge-status ativo">● Conectado</span>`
        : `<span class="badge-status bloqueado">● Falha de Login</span>`;

      return `
        <tr>
          <td><small style="font-family: monospace;">${dataFormatada}</small></td>
          <td><strong>${l.condominio_id ? `Condomínio #${l.condominio_id}` : 'Console Geral'}</strong></td>
          <td>
            <strong>${l.email_informado || 'Não identificado'}</strong>
            ${l.tipo_usuario ? `<br/><small class="muted-sm badge-role-sub">${l.tipo_usuario}</small>` : ''}
          </td>
          <td><code>${l.ip_origem || '-'}</code></td>
          <td><small class="muted-sm" title="${l.user_agent || ''}">${(l.user_agent || 'Navegador').substring(0, 45)}...</small></td>
          <td>${statusBadge}</td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    auditTableBody.innerHTML = `<tr><td colspan="6" class="text-center py-4" style="color: var(--rose);">Erro ao carregar auditoria: ${err.message}</td></tr>`;
  }
}

// ============================================================================
// Ações de Gestão (Impersonate, Status, Senha)
// ============================================================================

window.impersonateCondo = async function(condoId, condoNome, condoSlug) {
  // Pré-abre a aba no gesto de clique direto para que navegadores não bloqueiem o pop-up
  const newTab = window.open('about:blank', '_blank');
  try {
    const data = await fetchAdmin(`/condominios/${condoId}/impersonate`, {
      method: 'POST'
    });

    // Salva o token oficial de sessão lido pelo frontend principal (app.js)
    localStorage.setItem('sgc_token', data.access_token);
    localStorage.setItem('sgc_user', JSON.stringify(data.user));
    const effectiveSlug = condoSlug || (data.user && data.user.condominio_slug) || '';
    if (effectiveSlug) {
      localStorage.setItem('sgc_condo_slug', effectiveSlug);
    }

    showToast(`Acesso concedido. Abrindo portal de "${condoNome}"...`, 'success');

    const targetUrl = `${effectiveSlug ? `/c/${effectiveSlug}/` : `/?condo=${condoId}`}?impersonate_token=${encodeURIComponent(data.access_token)}`;
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

// ============================================================================
// Modal Moderno: Suspender / Reativar Condomínio (Experiência Executiva)
// ============================================================================

window.openToggleStatusModal = function(condoId, newStatus, condoNome) {
  const isBlocking = newStatus === 'BLOQUEADO';

  // Localiza dados do condomínio
  const condo = (allCondominios && allCondominios.find(c => parseInt(c.id, 10) === parseInt(condoId, 10)))
    || (currentDetailsCondo && parseInt(currentDetailsCondo.id, 10) === parseInt(condoId, 10) ? currentDetailsCondo : null);

  const finalNome = condoNome || (condo ? condo.nome : `Condomínio #${condoId}`);
  const finalCnpj = (condo && condo.cnpj) ? `CNPJ: ${condo.cnpj}` : 'CNPJ não informado';
  const totalUnidades = (condo && condo.total_unidades !== undefined) ? `${condo.total_unidades} unidades` : 'Unidades registradas';
  const pColor = (condo && condo.cor_primaria) ? condo.cor_primaria : '#3b82f6';
  const sColor = (condo && condo.cor_secundaria) ? condo.cor_secundaria : '#1d4ed8';

  if (statusTargetCondoId) statusTargetCondoId.value = condoId;
  if (statusTargetNextAction) statusTargetNextAction.value = newStatus;
  if (statusTargetCondoNome) statusTargetCondoNome.value = finalNome;

  if (statusModalCondoNome) statusModalCondoNome.textContent = finalNome;
  if (statusModalAvatar) {
    statusModalAvatar.textContent = finalNome.charAt(0).toUpperCase();
    statusModalAvatar.style.background = `linear-gradient(135deg, ${pColor}, ${sColor})`;
  }
  if (statusModalCnpjBadge) statusModalCnpjBadge.textContent = finalCnpj;
  if (statusModalUnidadesBadge) statusModalUnidadesBadge.textContent = totalUnidades;
  if (statusModalStatusBadge) {
    const isCurrentlyAtivo = condo ? (condo.status === 'ATIVO') : !isBlocking;
    statusModalStatusBadge.className = `badge-status-modern ${isCurrentlyAtivo ? 'ativo' : 'bloqueado'}`;
    statusModalStatusBadge.innerHTML = `<span class="dot-status"></span> ${isCurrentlyAtivo ? 'Ativo' : 'Suspenso'}`;
  }

  if (isBlocking) {
    if (statusModalIconBadge) {
      statusModalIconBadge.className = 'modal-icon-badge rose';
      statusModalIconBadge.innerHTML = '<svg class="ico"><use href="#i-lock"/></svg>';
    }
    if (statusModalTitle) statusModalTitle.textContent = 'Suspender Acesso do Condomínio';
    if (statusModalSubtitle) statusModalSubtitle.textContent = '';
    if (statusSectionSuspend) statusSectionSuspend.classList.remove('hidden');
    if (statusSectionReactivate) statusSectionReactivate.classList.add('hidden');
    if (statusSuspendNotes) statusSuspendNotes.value = '';
    if (hintSupportContactsDisplay && cachedSupportSettings) {
      hintSupportContactsDisplay.textContent = `${cachedSupportSettings.suporte_email} • Central: ${cachedSupportSettings.suporte_telefone}`;
    }
    if (btnSubmitToggleStatus) {
      btnSubmitToggleStatus.className = 'btn-primary-glow btn-danger-action';
      btnSubmitToggleStatus.disabled = false;
      btnSubmitToggleStatus.style.opacity = '1';
      btnSubmitToggleStatus.innerHTML = '<svg class="ico"><use href="#i-lock"/></svg> <span>Confirmar Suspensão</span>';
    }
  } else {
    if (statusModalIconBadge) {
      statusModalIconBadge.className = 'modal-icon-badge emerald';
      statusModalIconBadge.innerHTML = '<svg class="ico"><use href="#i-unlock"/></svg>';
    }
    if (statusModalTitle) statusModalTitle.textContent = 'Reativar Condomínio';
    if (statusModalSubtitle) statusModalSubtitle.textContent = '';
    if (statusSectionSuspend) statusSectionSuspend.classList.add('hidden');
    if (statusSectionReactivate) statusSectionReactivate.classList.remove('hidden');

    const prevMotivo = condo && condo.motivo_bloqueio ? condo.motivo_bloqueio.trim() : '';
    if (reactivateMotivoBox && reactivateCurrentMotivoText) {
      if (prevMotivo) {
        reactivateCurrentMotivoText.textContent = prevMotivo;
        reactivateMotivoBox.classList.remove('hidden');
      } else {
        reactivateMotivoBox.classList.add('hidden');
      }
    }

    if (btnSubmitToggleStatus) {
      btnSubmitToggleStatus.className = 'btn-primary-glow btn-emerald-action';
      btnSubmitToggleStatus.disabled = false;
      btnSubmitToggleStatus.style.opacity = '1';
      btnSubmitToggleStatus.innerHTML = '<svg class="ico"><use href="#i-unlock"/></svg> <span>Confirmar Reativação</span>';
    }
  }

  if (modalToggleCondoStatus) modalToggleCondoStatus.classList.remove('hidden');
};

window.closeToggleStatusModal = function() {
  if (modalToggleCondoStatus) modalToggleCondoStatus.classList.add('hidden');
  if (formToggleCondoStatus) formToggleCondoStatus.reset();
};

async function handleToggleStatusSubmit(e) {
  e.preventDefault();
  const condoId = statusTargetCondoId.value;
  const newStatus = statusTargetNextAction.value;
  const condoNome = statusTargetCondoNome.value;
  const isBlocking = newStatus === 'BLOQUEADO';

  const motivo = isBlocking
    ? (statusSuspendReason ? statusSuspendReason.value : 'Suspensão Operacional')
    : 'Reativação de Acesso';

  const notes = statusSuspendNotes ? statusSuspendNotes.value.trim() : '';
  const payloadMotivo = notes ? `${motivo} - ${notes}` : motivo;

  if (btnSubmitToggleStatus) {
    btnSubmitToggleStatus.disabled = true;
    btnSubmitToggleStatus.innerHTML = '<span>Processando...</span>';
  }

  try {
    const updated = await fetchAdmin(`/condominios/${condoId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus, motivo: payloadMotivo })
    });

    closeToggleStatusModal();

    showToast(
      isBlocking
        ? `Condomínio "${condoNome}" suspenso. O acesso foi pausado com segurança (todos os dados 100% preservados).`
        : `Condomínio "${condoNome}" reativado com sucesso! Acesso normalizado para moradores e administração.`,
      'success'
    );

    await loadMetrics();
    await loadCondominios();

    if (currentDetailsCondo && parseInt(currentDetailsCondo.id, 10) === parseInt(condoId, 10)) {
      try {
        const freshCondo = await fetchAdmin(`/condominios/${condoId}`);
        renderDedicatedCondoView(freshCondo);
      } catch (_) {
        renderDedicatedCondoView(updated);
      }
    }
  } catch (err) {
    showToast(`Erro ao atualizar situação: ${err.message}`, 'error');
    if (btnSubmitToggleStatus) {
      btnSubmitToggleStatus.disabled = false;
      btnSubmitToggleStatus.innerHTML = isBlocking
        ? '<svg class="ico"><use href="#i-lock"/></svg> <span>Confirmar Suspensão do Acesso</span>'
        : '<svg class="ico"><use href="#i-unlock"/></svg> <span>Reativar Condomínio Agora</span>';
    }
  }
}

window.toggleStatus = function(condoId, newStatus, condoNome) {
  openToggleStatusModal(condoId, newStatus, condoNome);
};

// ============================================================================
// Modal: Resetar Senha do Síndico
// ============================================================================

window.openResetPasswordModal = function(condoId, condoNome, email, roleLabel = 'Síndico Responsável', papel = 'SINDICO') {
  resetCondoId.value = condoId;
  if (resetPapelRole) resetPapelRole.value = papel;
  resetCondoNomeDisplay.textContent = condoNome;
  if (resetTargetRoleLabel) resetTargetRoleLabel.textContent = `${roleLabel}:`;
  const titleEl = document.getElementById('modalResetPasswordTitle');
  if (titleEl) titleEl.textContent = `Redefinir Senha do ${roleLabel}`;
  resetSindicoEmailDisplay.textContent = email || 'Sem e-mail cadastrado';
  resetNovaSenha.value = generateStrongPassword();
  modalResetPassword.classList.remove('hidden');
};

function closeResetPasswordModal() {
  modalResetPassword.classList.add('hidden');
  formResetPassword.reset();
  if (resetPapelRole) resetPapelRole.value = 'SINDICO';
  if (resetTargetRoleLabel) resetTargetRoleLabel.textContent = 'Síndico Responsável:';
  const titleEl = document.getElementById('modalResetPasswordTitle');
  if (titleEl) titleEl.textContent = 'Redefinir Senha do Síndico';
}

btnCloseModalResetPassword.addEventListener('click', closeResetPasswordModal);
btnCancelResetPassword.addEventListener('click', closeResetPasswordModal);

formResetPassword.addEventListener('submit', async (e) => {
  e.preventDefault();
  const condoId = resetCondoId.value;
  const papel = resetPapelRole ? resetPapelRole.value : 'SINDICO';
  const novaSenha = resetNovaSenha.value.trim();

  if (!novaSenha || novaSenha.length < 6) {
    showToast('A senha deve conter no mínimo 6 caracteres.', 'error');
    return;
  }

  try {
    const res = await fetchAdmin(`/condominios/${condoId}/reset-sindico-password?papel=${papel}`, {
      method: 'POST',
      body: JSON.stringify({ nova_senha: novaSenha })
    });
    showToast(res.message || 'Senha redefinida com sucesso!', 'success');
    closeResetPasswordModal();
  } catch (err) {
    showToast(`Erro ao redefinir senha: ${err.message}`, 'error');
  }
});

// ============================================================================
// Modal: Resetar Senha de Usuário da Rede
// ============================================================================

function closeResetUserPasswordModal() {
  if (modalResetUserPassword) {
    modalResetUserPassword.classList.add('hidden');
  }
  if (formResetUserPassword) {
    formResetUserPassword.reset();
  }
}

if (btnCloseModalResetUserPassword) {
  btnCloseModalResetUserPassword.addEventListener('click', closeResetUserPasswordModal);
}
if (btnCancelResetUserPassword) {
  btnCancelResetUserPassword.addEventListener('click', closeResetUserPasswordModal);
}

if (modalResetUserPassword) {
  modalResetUserPassword.addEventListener('click', (e) => {
    if (e.target === modalResetUserPassword) closeResetUserPasswordModal();
  });
}

if (btnGenPasswordUserReset) {
  btnGenPasswordUserReset.addEventListener('click', () => {
    if (resetUserNovaSenha) {
      resetUserNovaSenha.value = generateStrongPassword();
      showToast('Nova senha gerada!', 'info');
      resetUserNovaSenha.focus();
    }
  });
}

if (btnToggleUserPwVisibility) {
  btnToggleUserPwVisibility.addEventListener('click', () => {
    if (!resetUserNovaSenha) return;
    const isPass = resetUserNovaSenha.type === 'password';
    resetUserNovaSenha.type = isPass ? 'text' : 'password';
    if (iconEyeUserPw) {
      iconEyeUserPw.innerHTML = `<use href="${isPass ? '#i-eye' : '#i-eye-off'}"/>`;
    }
  });
}

if (btnCopyPasswordUserReset) {
  btnCopyPasswordUserReset.addEventListener('click', async () => {
    const pass = resetUserNovaSenha ? resetUserNovaSenha.value : '';
    if (!pass) return;
    try {
      await navigator.clipboard.writeText(pass);
      showToast('Senha copiada para a área de transferência!', 'success');
    } catch {
      if (resetUserNovaSenha) {
        resetUserNovaSenha.select();
        document.execCommand('copy');
        showToast('Senha copiada!', 'success');
      }
    }
  });
}

if (formResetUserPassword) {
  formResetUserPassword.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userId = resetTargetUserId ? resetTargetUserId.value : null;
    const novaSenha = resetUserNovaSenha ? resetUserNovaSenha.value.trim() : '';
    const precisaTrocar = resetUserForceChange ? resetUserForceChange.checked : false;

    if (!userId) {
      showToast('Identificador de usuário inválido.', 'error');
      return;
    }

    if (!novaSenha || novaSenha.length < 6) {
      showToast('A senha deve conter no mínimo 6 caracteres.', 'error');
      return;
    }

    const submitBtn = btnSaveResetUserPassword;
    const originalText = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<svg class="ico spin"><use href="#i-refresh"/></svg> <span>Gravando...</span>';
    }

    try {
      const res = await fetchAdmin(`/users/${userId}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({
          nova_senha: novaSenha,
          precisa_trocar_senha: precisaTrocar
        })
      });

      closeResetUserPasswordModal();
      showToast(res.message || 'Senha redefinida com sucesso!', 'success');

      // Tenta copiar a nova senha para o clipboard
      try {
        await navigator.clipboard.writeText(novaSenha);
      } catch (_) {}

      // Atualiza lista de usuários se estiver na aba de usuários ou condomínio
      if (activeTab === 'users') {
        loadGlobalUsers();
      } else if (activeTab === 'condoDetails' && currentDetailsCondo) {
        loadCondoDetailsUsers(currentDetailsCondo.id);
      } else if (activeTab === 'audit') {
        loadAuditLogs();
      }
    } catch (err) {
      showToast(`Erro ao redefinir senha: ${err.message}`, 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    }
  });
}

// ============================================================================
// Modal: Novo Condomínio
// ============================================================================

btnOpenNewCondo.addEventListener('click', () => {
  formCreateCondo.reset();
  userCustomizedNewSlug = false;
  if (newCondoSlug) newCondoSlug.value = '';
  document.querySelectorAll('.url-domain-prefix').forEach(el => {
    el.textContent = `${window.location.origin}/c/`;
  });
  if (newCondoCorPrimaria) newCondoCorPrimaria.value = '#2563eb';
  if (newCondoCorSecundaria) newCondoCorSecundaria.value = '#1d4ed8';
  if (newCondoCorSidebar) newCondoCorSidebar.value = '#09090b';
  if (labelNewCondoSidebar) labelNewCondoSidebar.textContent = '#09090b';
  document.querySelectorAll('.btn-theme-chip').forEach((b, i) => {
    b.classList.toggle('active', i === 0);
  });
  document.querySelectorAll('.btn-sidebar-chip').forEach((b, i) => {
    b.classList.toggle('active', i === 0);
  });

  // Reset de Governança
  if (radioGovAutogestao) radioGovAutogestao.checked = true;
  if (cardGovAutogestao) cardGovAutogestao.classList.add('active');
  if (cardGovCompartilhada) cardGovCompartilhada.classList.remove('active');
  if (wrapperAdmFields) wrapperAdmFields.classList.add('hidden');
  if (newAdmNome) { newAdmNome.value = ''; newAdmNome.required = false; }
  if (newAdmEmail) { newAdmEmail.value = ''; newAdmEmail.required = false; }
  if (newAdmTelefone) newAdmTelefone.value = '';

  // Reset do Subsíndico
  if (toggleNewTemSubsindico) toggleNewTemSubsindico.checked = false;
  if (wrapperSubsindicoFields) wrapperSubsindicoFields.classList.add('hidden');
  if (newSubsindicoNome) { newSubsindicoNome.value = ''; newSubsindicoNome.required = false; }
  if (newSubsindicoEmail) { newSubsindicoEmail.value = ''; newSubsindicoEmail.required = false; }
  if (newSubsindicoTelefone) newSubsindicoTelefone.value = '';

  modalNewCondo.classList.remove('hidden');
});

// Eventos de seleção dos cards de governança
if (cardGovAutogestao) {
  cardGovAutogestao.addEventListener('click', () => {
    cardGovAutogestao.classList.add('active');
    if (cardGovCompartilhada) cardGovCompartilhada.classList.remove('active');
    if (radioGovAutogestao) radioGovAutogestao.checked = true;
    if (wrapperAdmFields) wrapperAdmFields.classList.add('hidden');
    if (newAdmNome) newAdmNome.required = false;
    if (newAdmEmail) newAdmEmail.required = false;
  });
}

if (cardGovCompartilhada) {
  cardGovCompartilhada.addEventListener('click', () => {
    cardGovCompartilhada.classList.add('active');
    if (cardGovAutogestao) cardGovAutogestao.classList.remove('active');
    if (radioGovCompartilhada) radioGovCompartilhada.checked = true;
    if (wrapperAdmFields) wrapperAdmFields.classList.remove('hidden');
    if (newAdmNome) newAdmNome.required = true;
    if (newAdmEmail) newAdmEmail.required = true;
  });
}

// Toggle do Subsíndico no cadastro
if (toggleNewTemSubsindico) {
  toggleNewTemSubsindico.addEventListener('change', () => {
    const isChecked = toggleNewTemSubsindico.checked;
    if (wrapperSubsindicoFields) wrapperSubsindicoFields.classList.toggle('hidden', !isChecked);
    if (newSubsindicoNome) newSubsindicoNome.required = isChecked;
    if (newSubsindicoEmail) newSubsindicoEmail.required = isChecked;
    if (isChecked && newSubsindicoNome) newSubsindicoNome.focus();
  });
}

function closeNewCondoModal() {
  modalNewCondo.classList.add('hidden');
  formCreateCondo.reset();
  if (toggleNewTemSubsindico) toggleNewTemSubsindico.checked = false;
  if (wrapperSubsindicoFields) wrapperSubsindicoFields.classList.add('hidden');
  if (newSubsindicoNome) newSubsindicoNome.required = false;
  if (newSubsindicoEmail) newSubsindicoEmail.required = false;
}

btnCloseModalNewCondo.addEventListener('click', closeNewCondoModal);
btnCancelNewCondo.addEventListener('click', closeNewCondoModal);

formCreateCondo.addEventListener('submit', async (e) => {
  e.preventDefault();
  const sindico_nome = newSindicoNome ? newSindicoNome.value.trim() : null;
  const sindico_email = newSindicoEmail ? newSindicoEmail.value.trim() : null;
  const sindico_telefone = newSindicoTelefone ? newSindicoTelefone.value.trim() : null;
  const nome = newCondoNome && newCondoNome.value.trim() ? newCondoNome.value.trim() : null;
  const limite_unidades = newCondoLimite && newCondoLimite.value ? parseInt(newCondoLimite.value, 10) : 44;
  const cor_primaria = newCondoCorPrimaria ? newCondoCorPrimaria.value : '#2563eb';
  const cor_secundaria = newCondoCorSecundaria ? newCondoCorSecundaria.value : '#1d4ed8';
  const cor_sidebar = newCondoCorSidebar ? newCondoCorSidebar.value : '#09090b';

  const isCompartilhada = radioGovCompartilhada && radioGovCompartilhada.checked;
  const tipo_gestao = isCompartilhada ? 'COMPARTILHADA' : 'AUTOGESTAO';
  let administradora_nome = null;
  let administradora_email = null;
  let administradora_telefone = null;

  if (isCompartilhada) {
    administradora_nome = newAdmNome ? newAdmNome.value.trim() : '';
    administradora_email = newAdmEmail ? newAdmEmail.value.trim() : '';
    administradora_telefone = newAdmTelefone ? newAdmTelefone.value.trim() : null;

    if (!administradora_nome) {
      showToast('Por favor, informe o nome da administradora ou gestor parceiro.', 'error');
      if (newAdmNome) newAdmNome.focus();
      return;
    }
    if (!administradora_email) {
      showToast('Por favor, informe o e-mail de ativação da administradora.', 'error');
      if (newAdmEmail) newAdmEmail.focus();
      return;
    }
    if (sindico_email && administradora_email.toLowerCase() === sindico_email.toLowerCase()) {
      showToast('O e-mail da administradora deve ser diferente do e-mail do síndico.', 'error');
      if (newAdmEmail) newAdmEmail.focus();
      return;
    }
  }

  // Validação de Subsíndico
  const tem_subsindico = toggleNewTemSubsindico ? toggleNewTemSubsindico.checked : false;
  let subsindico_nome = null;
  let subsindico_email = null;
  let subsindico_telefone = null;

  if (tem_subsindico) {
    subsindico_nome = newSubsindicoNome ? newSubsindicoNome.value.trim() : '';
    subsindico_email = newSubsindicoEmail ? newSubsindicoEmail.value.trim() : '';
    subsindico_telefone = newSubsindicoTelefone ? newSubsindicoTelefone.value.trim() : null;

    if (!subsindico_nome) {
      showToast('Por favor, informe o nome do subsíndico.', 'error');
      if (newSubsindicoNome) newSubsindicoNome.focus();
      return;
    }
    if (!subsindico_email) {
      showToast('Por favor, informe o e-mail de ativação do subsíndico.', 'error');
      if (newSubsindicoEmail) newSubsindicoEmail.focus();
      return;
    }
    if (sindico_email && subsindico_email.toLowerCase() === sindico_email.toLowerCase()) {
      showToast('O e-mail do subsíndico deve ser diferente do e-mail do síndico titular.', 'error');
      if (newSubsindicoEmail) newSubsindicoEmail.focus();
      return;
    }
    if (administradora_email && subsindico_email.toLowerCase() === administradora_email.toLowerCase()) {
      showToast('O e-mail do subsíndico deve ser diferente do e-mail da administradora.', 'error');
      if (newSubsindicoEmail) newSubsindicoEmail.focus();
      return;
    }
  }

  const submitBtn = document.getElementById('btnSaveNewCondo');
  const originalHtml = submitBtn ? submitBtn.innerHTML : '';
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="pulse-dot"></span> <span>Gerando convite(s) seguro(s)...</span>';
  }

  const payload = {
    sindico_nome,
    sindico_email,
    sindico_telefone: sindico_telefone || null,
    nome: nome || null,
    limite_unidades,
    cor_primaria,
    cor_secundaria,
    cor_sidebar,
    tipo_gestao,
    administradora_nome: administradora_nome || null,
    administradora_email: administradora_email || null,
    administradora_telefone: administradora_telefone || null,
    tem_subsindico,
    subsindico_nome: subsindico_nome || null,
    subsindico_email: subsindico_email || null,
    subsindico_telefone: subsindico_telefone || null
  };

  try {
    const created = await fetchAdmin('/condominios', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    closeNewCondoModal();
    loadMetrics();
    loadCondominios();

    // Abre o Modal com as credenciais e links de ativação
    openInviteSuccessModal(created);
  } catch (err) {
    showToast(`Erro ao cadastrar condomínio: ${err.message}`, 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalHtml;
    }
  }
});

// ============================================================================
// Modal: Sucesso do Convite de Ativação (Síndico & Administradora)
// ============================================================================

function openInviteSuccessModal(data) {
  if (!modalInviteSuccess) return;
  if (succCondoNome) succCondoNome.textContent = data.nome || 'Condomínio';
  if (succSindicoNomeDisplay) succSindicoNomeDisplay.textContent = data.sindico_nome || 'Síndico';
  if (succSindicoEmail) succSindicoEmail.textContent = data.sindico_email || 'E-mail do síndico';

  const activationUrl = data.activation_url || `${window.location.origin}/c/${data.slug || ''}/ativar?token=${data.activation_token || ''}`;
  if (succActivationUrl) succActivationUrl.value = activationUrl;
  if (succCopyHint) succCopyHint.textContent = 'O síndico usará este link seguro de uso único para cadastrar sua senha e ativar o portal.';

  const waMsg = encodeURIComponent(
    `Olá ${data.sindico_nome || 'Síndico(a)'}! Seu acesso de gestor foi cadastrado no CondoHub.\n\nPara definir sua senha de acesso e ativar seu condomínio, utilize o link seguro exclusivo de primeiro acesso:\n${activationUrl}`
  );
  if (btnShareWhatsApp) {
    btnShareWhatsApp.href = `https://api.whatsapp.com/send?text=${waMsg}`;
  }

  if (btnOpenAtivarPreview) {
    btnOpenAtivarPreview.onclick = () => {
      window.open(activationUrl, '_blank');
    };
  }

  // Se gestão compartilhada, preenche o card da Administradora
  if (data.tipo_gestao === 'COMPARTILHADA' && (data.administradora_activation_url || data.administradora_email)) {
    if (cardInviteAdm) cardInviteAdm.classList.remove('hidden');
    if (succAdmNomeDisplay) succAdmNomeDisplay.textContent = data.administradora_nome || 'Administradora';
    if (succAdmEmail) succAdmEmail.textContent = data.administradora_email || '-';

    const admActivationUrl = data.administradora_activation_url || `${window.location.origin}/c/${data.slug || ''}/ativar?token=${data.administradora_activation_token || ''}`;
    if (succAdmActivationUrl) succAdmActivationUrl.value = admActivationUrl;

    const waMsgAdm = encodeURIComponent(
      `Olá ${data.administradora_nome || 'Gestor(a)'}! Seu acesso de Administradora foi cadastrado no condomínio ${data.nome || ''} via CondoHub.\n\nPara definir sua senha de acesso e iniciar a gestão compartilhada, utilize o link seguro exclusivo:\n${admActivationUrl}`
    );
    if (btnShareWhatsAppAdm) {
      btnShareWhatsAppAdm.href = `https://api.whatsapp.com/send?text=${waMsgAdm}`;
    }

    if (btnOpenAtivarPreviewAdm) {
      btnOpenAtivarPreviewAdm.onclick = () => {
        window.open(admActivationUrl, '_blank');
      };
    }
  } else {
    if (cardInviteAdm) cardInviteAdm.classList.add('hidden');
  }

  // Se informado Subsíndico, preenche o card do Subsíndico
  if ((data.tem_subsindico || data.subsindico_activation_url) && (data.subsindico_activation_url || data.subsindico_email)) {
    if (cardInviteSubsindico) cardInviteSubsindico.classList.remove('hidden');
    if (succSubsindicoNomeDisplay) succSubsindicoNomeDisplay.textContent = data.subsindico_nome || 'Subsíndico(a)';
    if (succSubsindicoEmail) succSubsindicoEmail.textContent = data.subsindico_email || '-';

    const subActivationUrl = data.subsindico_activation_url || `${window.location.origin}/c/${data.slug || ''}/ativar?token=${data.subsindico_activation_token || ''}`;
    if (succSubActivationUrl) succSubActivationUrl.value = subActivationUrl;

    const waMsgSub = encodeURIComponent(
      `Olá ${data.subsindico_nome || 'Subsíndico(a)'}! Seu acesso de governança condominial compartilhada foi cadastrado no condomínio ${data.nome || ''} via CondoHub.\n\nPara definir sua senha de acesso e ativar o portal, utilize o link seguro exclusivo:\n${subActivationUrl}`
    );
    if (btnShareWhatsAppSub) {
      btnShareWhatsAppSub.href = `https://api.whatsapp.com/send?text=${waMsgSub}`;
    }

    if (btnOpenAtivarPreviewSub) {
      btnOpenAtivarPreviewSub.onclick = () => {
        window.open(subActivationUrl, '_blank');
      };
    }
  } else {
    if (cardInviteSubsindico) cardInviteSubsindico.classList.add('hidden');
  }

  modalInviteSuccess.classList.remove('hidden');
}

function closeInviteSuccessModal() {
  if (modalInviteSuccess) modalInviteSuccess.classList.add('hidden');
}

if (btnCloseModalInviteSuccess) btnCloseModalInviteSuccess.addEventListener('click', closeInviteSuccessModal);
if (btnDoneInviteSuccess) btnDoneInviteSuccess.addEventListener('click', closeInviteSuccessModal);
if (modalInviteSuccess) {
  modalInviteSuccess.addEventListener('click', (e) => {
    if (e.target === modalInviteSuccess) closeInviteSuccessModal();
  });
}

if (btnCopySenhaProvisoria) {
  btnCopySenhaProvisoria.addEventListener('click', () => {
    if (succSenhaProvisoria && succSenhaProvisoria.value) {
      copyToClipboard(succSenhaProvisoria.value, 'Senha provisória copiada!');
    }
  });
}

if (btnCopyActivationUrl) {
  btnCopyActivationUrl.addEventListener('click', () => {
    if (succActivationUrl && succActivationUrl.value) {
      copyToClipboard(succActivationUrl.value, 'Link de ativação do Síndico copiado!');
      if (succCopyHint) succCopyHint.textContent = 'Link copiado com sucesso! Você pode enviá-lo pelo WhatsApp ou e-mail.';
    }
  });
}

if (btnCopyAdmActivationUrl) {
  btnCopyAdmActivationUrl.addEventListener('click', () => {
    if (succAdmActivationUrl && succAdmActivationUrl.value) {
      copyToClipboard(succAdmActivationUrl.value, 'Link de ativação da Administradora copiado!');
    }
  });
}

if (btnCopySubActivationUrl) {
  btnCopySubActivationUrl.addEventListener('click', () => {
    if (succSubActivationUrl && succSubActivationUrl.value) {
      copyToClipboard(succSubActivationUrl.value, 'Link de ativação do Subsíndico copiado!');
    }
  });
}

window.resendSindicoInvite = async function(condoId, condoNome) {
  try {
    showToast(`Gerando novas credenciais para "${condoNome}"...`, 'info');
    const res = await fetchAdmin(`/condominios/${condoId}/resend-invite`, {
      method: 'POST'
    });
    showToast(res.message, 'success');
    openInviteSuccessModal({
      nome: condoNome,
      sindico_email: res.sindico_email,
      activation_url: res.activation_url,
      activation_token: res.activation_token,
      senha_provisoria: res.senha_provisoria
    });
  } catch (err) {
    showToast(`Erro ao reenviar convite: ${err.message}`, 'error');
  }
};

window.confirmDeleteCondo = async function(condoId, condoNome) {
  if (condoId === 1) {
    showToast('O condomínio matriz Residencial Bela Vista não pode ser excluído.', 'warning');
    return;
  }

  const confirmed = confirm(`Tem certeza que deseja excluir o condomínio "${condoNome}"?\n\nTodos os apartamentos, moradores, porteiros, encomendas, comunicados e histórico vinculados a ele serão permanentemente excluídos.\n\nEsta operação não pode ser desfeita.`);
  if (!confirmed) return;

  try {
    showToast(`Excluindo condomínio "${condoNome}"...`, 'info');
    const res = await fetchAdmin(`/condominios/${condoId}`, {
      method: 'DELETE'
    });
    showToast(res.message || 'Condomínio excluído com sucesso!', 'success');
    await loadMetrics();
    await loadCondominios();
    if (currentDetailsCondo && currentDetailsCondo.id === condoId) {
      switchTab('condos');
    }
  } catch (err) {
    showToast(`Erro ao excluir condomínio: ${err.message}`, 'error');
  }
};


// ============================================================================
// Modal: Editar Condomínio & Síndico
// ============================================================================

window.openEditCondoModal = async function(condoId) {
  try {
    const condo = await fetchAdmin(`/condominios/${condoId}`);
    editCondoId.value = condo.id;
    editCondoNome.value = condo.nome || '';
    if (editCondoSlug) editCondoSlug.value = condo.slug || '';
    document.querySelectorAll('.url-domain-prefix').forEach(el => {
      el.textContent = `${window.location.origin}/c/`;
    });
    if (editSlugPreview) editSlugPreview.textContent = `/c/${condo.slug || 'slug'}/`;
    editCondoCnpj.value = condo.cnpj || '';
    editCondoEndereco.value = condo.endereco || '';
    editCondoTelefone.value = condo.telefone || '';
    editCondoEmail.value = condo.email_contato || '';
    editCondoLimite.value = condo.limite_unidades || 100;

    const p = condo.cor_primaria || '#2563eb';
    const s = condo.cor_secundaria || '#1d4ed8';
    const side = condo.cor_sidebar || '#09090b';
    editCondoCorPrimaria.value = p;
    labelEditCorPrimaria.textContent = p;
    editCondoCorSecundaria.value = s;
    labelEditCorSecundaria.textContent = s;
    if (editCondoCorSidebar) {
      editCondoCorSidebar.value = side;
      if (labelEditCorSidebar) labelEditCorSidebar.textContent = side;
    }
    document.querySelectorAll('.btn-sidebar-chip-edit').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-sidebar') === side);
    });

    // Governança & Administradora
    const tipoGov = condo.tipo_gestao || 'AUTOGESTAO';
    if (typeof setEditGovernance === 'function') {
      setEditGovernance(tipoGov);
    }
    if (editAdmNome) editAdmNome.value = condo.administradora_nome || '';
    if (editAdmEmail) editAdmEmail.value = condo.administradora_email || '';
    if (editAdmTelefone) editAdmTelefone.value = condo.administradora_telefone || '';

    // Dados do Síndico
    editSindicoNome.value = condo.sindico_nome || '';
    editSindicoEmail.value = condo.sindico_email || '';
    editSindicoTelefone.value = condo.sindico_telefone || '';
    editSindicoSenha.value = '';
    editSindicoSenha.type = 'password';
    if (btnToggleEditPassword) {
      btnToggleEditPassword.innerHTML = '<svg class="ico"><use href="#i-eye"/></svg>';
    }

    // Dados do Subsíndico
    const hasSub = !!(condo.tem_subsindico && condo.subsindico_nome);
    if (editTemSubsindico) {
      editTemSubsindico.checked = hasSub;
    }
    if (labelEditTemSubsindico) {
      labelEditTemSubsindico.textContent = hasSub ? 'Subsíndico Habilitado' : 'Habilitar Subsíndico';
    }
    if (badgeEditSubStatus) {
      badgeEditSubStatus.textContent = hasSub ? (condo.subsindico_ativo ? 'Ativo' : 'Pendente') : 'Não vinculado';
      badgeEditSubStatus.style.background = hasSub ? 'rgba(124, 58, 237, 0.25)' : 'rgba(255, 255, 255, 0.08)';
    }
    if (wrapperEditSubsindicoFields) {
      wrapperEditSubsindicoFields.classList.toggle('hidden', !hasSub);
    }
    if (editSubsindicoNome) editSubsindicoNome.value = condo.subsindico_nome || '';
    if (editSubsindicoEmail) editSubsindicoEmail.value = condo.subsindico_email || '';
    if (editSubsindicoTelefone) editSubsindicoTelefone.value = condo.subsindico_telefone || '';
    if (editSubsindicoSenha) {
      editSubsindicoSenha.value = '';
      editSubsindicoSenha.type = 'password';
    }
    if (btnToggleEditSubPassword) {
      btnToggleEditSubPassword.innerHTML = '<svg class="ico"><use href="#i-eye"/></svg>';
    }

    // Ativa chip correspondente de tema se existir
    document.querySelectorAll('.btn-theme-chip-edit').forEach(btn => {
      if (btn.getAttribute('data-primary') === p) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    modalEditCondo.classList.remove('hidden');
  } catch (err) {
    showToast(`Erro ao carregar dados do condomínio: ${err.message}`, 'error');
  }
};

function closeEditCondoModal() {
  modalEditCondo.classList.add('hidden');
  formEditCondo.reset();
  if (editTemSubsindico) editTemSubsindico.checked = false;
  if (wrapperEditSubsindicoFields) wrapperEditSubsindicoFields.classList.add('hidden');
}

btnCloseModalEditCondo.addEventListener('click', closeEditCondoModal);
btnCancelEditCondo.addEventListener('click', closeEditCondoModal);

// Toggle e Ações de Subsíndico na Edição
if (editTemSubsindico) {
  editTemSubsindico.addEventListener('change', () => {
    const isChecked = editTemSubsindico.checked;
    if (wrapperEditSubsindicoFields) wrapperEditSubsindicoFields.classList.toggle('hidden', !isChecked);
    if (labelEditTemSubsindico) {
      labelEditTemSubsindico.textContent = isChecked ? 'Subsíndico Habilitado' : 'Habilitar Subsíndico';
    }
    if (isChecked && editSubsindicoNome) editSubsindicoNome.focus();
  });
}

if (btnGenPasswordEditSub && editSubsindicoSenha) {
  btnGenPasswordEditSub.addEventListener('click', () => {
    editSubsindicoSenha.value = generateStrongPassword();
    editSubsindicoSenha.type = 'text';
    if (btnToggleEditSubPassword) {
      btnToggleEditSubPassword.innerHTML = '<svg class="ico"><use href="#i-eye-off"/></svg>';
    }
    showToast('Nova senha segura para o subsíndico gerada no formulário!', 'info');
  });
}

if (btnToggleEditSubPassword && editSubsindicoSenha) {
  btnToggleEditSubPassword.addEventListener('click', () => {
    const isPass = editSubsindicoSenha.type === 'password';
    editSubsindicoSenha.type = isPass ? 'text' : 'password';
    btnToggleEditSubPassword.innerHTML = isPass
      ? '<svg class="ico"><use href="#i-eye-off"/></svg>'
      : '<svg class="ico"><use href="#i-eye"/></svg>';
  });
}

if (btnRemoveEditSubsindico) {
  btnRemoveEditSubsindico.addEventListener('click', () => {
    if (confirm('Deseja realmente desvincular o Subsíndico deste condomínio? Ele perderá acesso ao portal.')) {
      if (editTemSubsindico) {
        editTemSubsindico.checked = false;
        editTemSubsindico.dispatchEvent(new Event('change'));
      }
      if (editSubsindicoNome) editSubsindicoNome.value = '';
      if (editSubsindicoEmail) editSubsindicoEmail.value = '';
      if (editSubsindicoTelefone) editSubsindicoTelefone.value = '';
      if (editSubsindicoSenha) editSubsindicoSenha.value = '';
      showToast('Subsíndico marcado para desvinculação. Clique em "Salvar Todas as Alterações" para confirmar.', 'info');
    }
  });
}

formEditCondo.addEventListener('submit', async (e) => {
  e.preventDefault();
  const condoId = editCondoId.value;

  const customSlug = editCondoSlug && editCondoSlug.value.trim() ? slugify(editCondoSlug.value.trim()) : null;

  const isCompartilhada = radioEditGovCompartilhada && radioEditGovCompartilhada.checked;
  const tipo_gestao = isCompartilhada ? 'COMPARTILHADA' : 'AUTOGESTAO';

  let administradora_nome = null;
  let administradora_email = null;
  let administradora_telefone = null;

  if (isCompartilhada) {
    administradora_nome = editAdmNome ? editAdmNome.value.trim() : '';
    administradora_email = editAdmEmail ? editAdmEmail.value.trim() : '';
    administradora_telefone = editAdmTelefone ? editAdmTelefone.value.trim() : null;

    if (!administradora_nome) {
      showToast('Por favor, informe o Nome da Administradora parceira.', 'error');
      if (editAdmNome) editAdmNome.focus();
      return;
    }
    if (!administradora_email) {
      showToast('Por favor, informe o E-mail da Administradora parceira.', 'error');
      if (editAdmEmail) editAdmEmail.focus();
      return;
    }
    const sindicoEmailVal = editSindicoEmail ? editSindicoEmail.value.trim().toLowerCase() : '';
    if (sindicoEmailVal && administradora_email.toLowerCase() === sindicoEmailVal) {
      showToast('O e-mail da administradora deve ser diferente do e-mail do síndico.', 'error');
      if (editAdmEmail) editAdmEmail.focus();
      return;
    }
  }

  // Gestão de Subsíndico na Edição
  const tem_subsindico = editTemSubsindico ? editTemSubsindico.checked : false;
  let subsindico_nome = null;
  let subsindico_email = null;
  let subsindico_telefone = null;
  let subsindico_senha = null;
  let remover_subsindico = false;

  if (tem_subsindico) {
    subsindico_nome = editSubsindicoNome ? editSubsindicoNome.value.trim() : '';
    subsindico_email = editSubsindicoEmail ? editSubsindicoEmail.value.trim() : '';
    subsindico_telefone = editSubsindicoTelefone ? editSubsindicoTelefone.value.trim() : null;
    subsindico_senha = editSubsindicoSenha ? editSubsindicoSenha.value.trim() : null;

    if (!subsindico_nome) {
      showToast('Por favor, informe o nome do subsíndico.', 'error');
      if (editSubsindicoNome) editSubsindicoNome.focus();
      return;
    }
    if (!subsindico_email) {
      showToast('Por favor, informe o e-mail do subsíndico.', 'error');
      if (editSubsindicoEmail) editSubsindicoEmail.focus();
      return;
    }
    const sindicoEmailVal = editSindicoEmail ? editSindicoEmail.value.trim().toLowerCase() : '';
    if (sindicoEmailVal && subsindico_email.toLowerCase() === sindicoEmailVal) {
      showToast('O e-mail do subsíndico deve ser diferente do e-mail do síndico titular.', 'error');
      if (editSubsindicoEmail) editSubsindicoEmail.focus();
      return;
    }
    if (subsindico_senha && subsindico_senha.length < 6) {
      showToast('A senha do subsíndico deve ter no mínimo 6 caracteres.', 'error');
      return;
    }
  } else {
    remover_subsindico = true;
  }

  const payload = {
    nome: editCondoNome.value.trim(),
    slug: customSlug || undefined,
    cnpj: editCondoCnpj.value.trim() || null,
    endereco: editCondoEndereco.value.trim() || null,
    telefone: editCondoTelefone.value.trim() || null,
    email_contato: editCondoEmail.value.trim() || null,
    limite_unidades: parseInt(editCondoLimite.value, 10) || 100,
    cor_primaria: editCondoCorPrimaria.value,
    cor_secundaria: editCondoCorSecundaria.value,
    cor_sidebar: editCondoCorSidebar ? editCondoCorSidebar.value : '#09090b',
    tipo_gestao,
    administradora_nome,
    administradora_email,
    administradora_telefone,
    sindico_nome: editSindicoNome.value.trim() || null,
    sindico_email: editSindicoEmail.value.trim() || null,
    sindico_telefone: editSindicoTelefone.value.trim() || null,
    tem_subsindico,
    subsindico_nome: tem_subsindico ? subsindico_nome : null,
    subsindico_email: tem_subsindico ? subsindico_email : null,
    subsindico_telefone: tem_subsindico ? (subsindico_telefone || null) : null,
    remover_subsindico
  };

  if (tem_subsindico && subsindico_senha) {
    payload.subsindico_senha = subsindico_senha;
  }

  const novaSenha = editSindicoSenha.value.trim();
  if (novaSenha) {
    if (novaSenha.length < 6) {
      showToast('A senha do síndico deve ter no mínimo 6 caracteres.', 'error');
      return;
    }
    payload.sindico_senha = novaSenha;
  }

  try {
    const updated = await fetchAdmin(`/condominios/${condoId}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    });

    showToast(`Condomínio "${updated.nome}" atualizado com sucesso!`, 'success');
    closeEditCondoModal();
    loadMetrics();
    loadCondominios();
    if (currentDetailsCondo && parseInt(currentDetailsCondo.id, 10) === parseInt(updated.id, 10)) {
      renderDedicatedCondoView(updated);
    }

    // Se houve emissão de link de ativação da Administradora ou Subsíndico
    if (updated.administradora_activation_url || updated.subsindico_activation_url) {
      openInviteSuccessModal(updated);
    }
  } catch (err) {
    showToast(`Erro ao salvar alterações: ${err.message}`, 'error');
  }
});

// ============================================================================
// CANAIS DE SUPORTE & REGULARIZAÇÃO (SUPER ADMIN)
// ============================================================================

let cachedSupportSettings = null;

async function loadSupportSettings() {
  try {
    const data = await fetchAdmin('/support-settings');
    cachedSupportSettings = data;
    if (cfgSuporteEmail) cfgSuporteEmail.value = data.suporte_email || '';
    if (cfgSuporteTelefone) cfgSuporteTelefone.value = data.suporte_telefone || '';
    if (cfgSuporteHorario) cfgSuporteHorario.value = data.suporte_horario || '';
    if (cfgTituloRegularizacao) cfgTituloRegularizacao.value = data.titulo_regularizacao || 'O que fazer para regularizar?';
    if (cfgMensagemRegularizacao) cfgMensagemRegularizacao.value = data.mensagem_regularizacao || '';
    updateSupportLivePreview();
  } catch (err) {
    console.warn('[Console] Aviso ao carregar canais de suporte:', err);
  }
}

function updateSupportLivePreview() {
  const email = cfgSuporteEmail?.value?.trim() || 'suporte@corsini.inf.br';
  const phone = cfgSuporteTelefone?.value?.trim() || '(11) 98765-4321';
  const hours = cfgSuporteHorario?.value?.trim() || 'Segunda a Sexta, das 08h às 18h';
  const title = cfgTituloRegularizacao?.value?.trim() || 'O que fazer para regularizar?';
  const desc = cfgMensagemRegularizacao?.value?.trim() || 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.';

  if (previewSupportEmail) previewSupportEmail.textContent = email;
  if (previewSupportPhone) previewSupportPhone.textContent = `Central: ${phone}`;
  if (previewSupportHours) previewSupportHours.textContent = hours;
  if (previewActionTitle) previewActionTitle.textContent = title;
  if (previewActionDesc) previewActionDesc.textContent = desc;

  if (hintSupportContactsDisplay) {
    hintSupportContactsDisplay.textContent = `${email} • Central: ${phone}`;
  }
}

function resetSupportDefaults() {
  if (cfgSuporteEmail) cfgSuporteEmail.value = 'suporte@corsini.inf.br';
  if (cfgSuporteTelefone) cfgSuporteTelefone.value = '(11) 98765-4321';
  if (cfgSuporteHorario) cfgSuporteHorario.value = 'Segunda a Sexta, das 08h às 18h';
  if (cfgTituloRegularizacao) cfgTituloRegularizacao.value = 'O que fazer para regularizar?';
  if (cfgMensagemRegularizacao) {
    cfgMensagemRegularizacao.value = 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.';
  }
  updateSupportLivePreview();
  showToast('Valores padrão restaurados no formulário. Clique em "Salvar" para confirmar.', 'info');
}

async function handleSupportSettingsSubmit(e) {
  e.preventDefault();
  const payload = {
    suporte_email: cfgSuporteEmail ? cfgSuporteEmail.value.trim() : '',
    suporte_telefone: cfgSuporteTelefone ? cfgSuporteTelefone.value.trim() : '',
    suporte_horario: cfgSuporteHorario ? cfgSuporteHorario.value.trim() : '',
    titulo_regularizacao: cfgTituloRegularizacao ? cfgTituloRegularizacao.value.trim() : 'O que fazer para regularizar?',
    mensagem_regularizacao: cfgMensagemRegularizacao ? cfgMensagemRegularizacao.value.trim() : ''
  };

  if (!payload.suporte_email || !payload.suporte_telefone) {
    showToast('E-mail e telefone de suporte são obrigatórios.', 'warning');
    return;
  }

  if (btnSaveSupportSettings) {
    btnSaveSupportSettings.disabled = true;
    btnSaveSupportSettings.innerHTML = '<span>Salvando...</span>';
  }

  try {
    const updated = await fetchAdmin('/support-settings', {
      method: 'PUT',
      body: JSON.stringify(payload)
    });
    cachedSupportSettings = updated;
    updateSupportLivePreview();
    showToast('Canais de suporte atualizados com sucesso! Todos os portais foram sincronizados.', 'success');
  } catch (err) {
    showToast(`Erro ao salvar canais de suporte: ${err.message}`, 'error');
  } finally {
    if (btnSaveSupportSettings) {
      btnSaveSupportSettings.disabled = false;
      btnSaveSupportSettings.innerHTML = '<svg class="ico"><use href="#i-check"/></svg> <span>Salvar Canais de Suporte</span>';
    }
  }
}

