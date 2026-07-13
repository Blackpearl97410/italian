const STORAGE_KEY = "lpp_web_state_v1";
const ACCOUNTS_KEY = "lpp_accounts_v1";

const appState = {
  seedData: null,
  data: null,
  backend: "local",
  supabase: null,
  session: null,
  currentSituation: null,
  currentExerciseIndex: 0,
  correctCount: 0,
  selectedLevel: "all",
  store: loadAccountStore(),
  user: null,
  local: defaultLocalState(),
};

const REQUIRED_SOURCE_FIELDS = [
  "name",
  "url",
  "source_type",
  "license",
  "retrieved_at",
  "reliability_score",
  "notes",
];
const REQUIRED_SITUATION_FIELDS = ["slug", "title", "level", "objective", "phrases", "exercises"];
const REQUIRED_PHRASE_FIELDS = ["fr_text", "en_text", "it_text", "explanation", "common_trap"];
const REQUIRED_EXERCISE_FIELDS = [
  "type",
  "question",
  "correct_answer",
  "explanation_correct",
  "explanation_wrong",
  "difficulty",
];

const views = [...document.querySelectorAll(".view")];

function defaultLocalState() {
  return {
    importedPayloads: [],
    progress: {},
    answers: [],
    reviews: {},
    lastSituationSlug: null,
  };
}

function loadAccountStore() {
  const empty = { currentUserId: null, users: [] };
  try {
    const stored = JSON.parse(localStorage.getItem(ACCOUNTS_KEY) || "null");
    if (stored?.users) return stored;
  } catch {
    // Ignore malformed account storage and try the legacy migration below.
  }
  const legacy = loadLegacyLocalState();
  if (hasLegacyData(legacy)) {
    const user = {
      id: crypto.randomUUID(),
      name: "Utilisateur local",
      passwordHash: "",
      createdAt: new Date().toISOString(),
      data: legacy,
    };
    const migrated = { currentUserId: user.id, users: [user] };
    localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(migrated));
    return migrated;
  }
  return empty;
}

function loadLegacyLocalState() {
  try {
    return { ...defaultLocalState(), ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
  } catch {
    return defaultLocalState();
  }
}

function hasLegacyData(data) {
  return (
    data.importedPayloads.length > 0 ||
    Object.keys(data.progress).length > 0 ||
    data.answers.length > 0 ||
    Object.keys(data.reviews).length > 0
  );
}

function saveAccountStore() {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(appState.store));
}

function saveLocalState() {
  if (!appState.user) return;
  if (appState.backend === "supabase") {
    syncRemoteState();
    return;
  }
  appState.user.data = appState.local;
  appState.store.currentUserId = appState.user.id;
  saveAccountStore();
}

function setActiveUser(user) {
  appState.user = user;
  appState.local = { ...defaultLocalState(), ...user.data };
  appState.store.currentUserId = user.id;
  saveAccountStore();
}

async function hashPassword(password) {
  if (!password) return "";
  const bytes = new TextEncoder().encode(password);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function getSupabaseConfig() {
  const config = window.LPP_SUPABASE;
  if (!config?.url || !config?.anonKey) return null;
  if (config.anonKey.includes("COLLE_ICI")) return null;
  return config;
}

function initSupabaseClient() {
  const config = getSupabaseConfig();
  if (!config || !window.supabase?.createClient) {
    appState.backend = "local";
    return;
  }
  appState.supabase = window.supabase.createClient(config.url, config.anonKey);
  appState.backend = "supabase";
}

async function loadRemoteSession() {
  if (appState.backend !== "supabase") return null;
  const { data, error } = await appState.supabase.auth.getSession();
  if (error) {
    console.warn("Supabase session error", error);
    return null;
  }
  appState.session = data.session;
  return data.session;
}

async function loadRemoteUserState(session) {
  if (!session?.user) return false;
  const userId = session.user.id;
  const email = session.user.email || "";
  const { data: profile } = await appState.supabase
    .from("profiles")
    .select("id, display_name, created_at")
    .eq("id", userId)
    .maybeSingle();
  const displayName = profile?.display_name || email.split("@")[0] || "Utilisateur";
  let { data: stateRow, error } = await appState.supabase
    .from("user_state")
    .select("imported_payloads, progress, answers, reviews, last_situation_slug")
    .eq("user_id", userId)
    .maybeSingle();
  if (error) console.warn("Supabase state read error", error);
  if (!stateRow) {
    const { data } = await appState.supabase
      .from("user_state")
      .insert({ user_id: userId })
      .select("imported_payloads, progress, answers, reviews, last_situation_slug")
      .single();
    stateRow = data;
  }
  appState.user = {
    id: userId,
    email,
    name: displayName,
    createdAt: profile?.created_at || session.user.created_at || new Date().toISOString(),
    remote: true,
  };
  appState.local = {
    importedPayloads: stateRow?.imported_payloads || [],
    progress: stateRow?.progress || {},
    answers: stateRow?.answers || [],
    reviews: stateRow?.reviews || {},
    lastSituationSlug: stateRow?.last_situation_slug || null,
  };
  return true;
}

let syncTimer = null;

function syncRemoteState() {
  if (appState.backend !== "supabase" || !appState.user) return;
  clearTimeout(syncTimer);
  syncTimer = setTimeout(async () => {
    const payload = {
      user_id: appState.user.id,
      imported_payloads: appState.local.importedPayloads,
      progress: appState.local.progress,
      answers: appState.local.answers,
      reviews: appState.local.reviews,
      last_situation_slug: appState.local.lastSituationSlug,
    };
    const { error } = await appState.supabase.from("user_state").upsert(payload, {
      onConflict: "user_id",
    });
    if (error) console.warn("Supabase sync error", error);
  }, 250);
}

async function upsertRemoteProfile(userId, displayName) {
  const { error } = await appState.supabase.from("profiles").upsert(
    {
      id: userId,
      display_name: displayName,
    },
    { onConflict: "id" }
  );
  if (error) throw error;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function normalize(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[.?!,;:'"`]/g, "")
    .replace(/\s+/g, " ");
}

function mergePayloads(seedPayload, importedPayloads) {
  const merged = {
    source: seedPayload.source,
    sources: seedPayload.sources ? [...seedPayload.sources] : [seedPayload.source],
    situations: [...seedPayload.situations],
  };
  const slugSet = new Set(merged.situations.map((situation) => situation.slug));
  const sourceUrls = new Set(merged.sources.map((source) => source.url));
  importedPayloads.forEach((payload) => {
    if (!sourceUrls.has(payload.source.url)) {
      merged.sources.push(payload.source);
      sourceUrls.add(payload.source.url);
    }
    payload.situations.forEach((situation) => {
      if (!slugSet.has(situation.slug)) {
        merged.situations.push(situation);
        slugSet.add(situation.slug);
      }
    });
  });
  merged.situations.sort((a, b) => (a.order_index ?? 999) - (b.order_index ?? 999));
  return merged;
}

async function boot() {
  initSupabaseClient();
  const response = await fetch("../data/seed/situations_seed.json");
  const seedPayload = await response.json();
  appState.seedData = seedPayload;
  let hasActiveUser = false;
  if (appState.backend === "supabase") {
    const session = await loadRemoteSession();
    hasActiveUser = await loadRemoteUserState(session);
  } else {
    const activeUser = appState.store.users.find((user) => user.id === appState.store.currentUserId);
    if (activeUser) setActiveUser(activeUser);
    hasActiveUser = Boolean(activeUser);
  }
  rebuildDataForCurrentUser();
  bindNavigation();
  bindAuthActions();
  bindImportActions();
  renderLogin();
  renderAccountStrip();
  renderSituations();
  renderSources();
  showView(hasActiveUser ? "home" : "login");
}

function rebuildDataForCurrentUser() {
  appState.data = mergePayloads(appState.seedData, appState.local.importedPayloads);
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!appState.user && button.dataset.view !== "login") {
        showView("login");
        return;
      }
      showView(button.dataset.view);
    });
  });
  document.querySelector("[data-action='continue']").addEventListener("click", () => {
    if (!appState.user) {
      showView("login");
      return;
    }
    const slug = appState.local.lastSituationSlug || appState.data.situations[0]?.slug;
    if (slug) openLesson(slug);
  });
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      appState.selectedLevel = button.dataset.filter;
      document
        .querySelectorAll("[data-filter]")
        .forEach((filter) => filter.classList.toggle("active", filter === button));
      renderSituations();
    });
  });
}

function bindAuthActions() {
  document.querySelector("#login-button").addEventListener("click", loginSelectedProfile);
  document.querySelector("#create-profile-button").addEventListener("click", createProfile);
  document.querySelector("#profile-password").addEventListener("keydown", (event) => {
    if (event.key === "Enter") loginSelectedProfile();
  });
}

function bindImportActions() {
  document.querySelector("#validate-import").addEventListener("click", () => handleImport(false));
  document.querySelector("#run-import").addEventListener("click", () => handleImport(true));
  document.querySelector("#export-data").addEventListener("click", exportLocalData);
  document.querySelector("#reset-local-data").addEventListener("click", resetLocalData);
}

function renderLogin(message = "") {
  const select = document.querySelector("#profile-select");
  const localProfileRow = document.querySelector("#local-profile-row");
  const modeCopy = document.querySelector("#auth-mode-copy");
  const isSupabase = appState.backend === "supabase";
  localProfileRow.hidden = isSupabase;
  localProfileRow.style.display = isSupabase ? "none" : "";
  modeCopy.textContent =
    isSupabase
      ? "Connexion Supabase: tes progres et ton tableau de bord sont synchronises en ligne."
      : "Mode local: renseigne supabase-config.js pour activer la base de donnees en ligne.";
  select.innerHTML = "";
  if (!appState.store.users.length) {
    select.innerHTML = `<option value="">Aucun profil local</option>`;
  } else {
    appState.store.users.forEach((user) => {
      const option = document.createElement("option");
      option.value = user.id;
      option.textContent = user.name;
      option.selected = user.id === appState.store.currentUserId;
      select.appendChild(option);
    });
  }
  document.querySelector("#login-message").textContent = message;
}

async function createProfile() {
  if (appState.backend === "supabase") {
    await createRemoteProfile();
    return;
  }
  const nameInput = document.querySelector("#profile-name");
  const passwordInput = document.querySelector("#profile-password");
  const name = nameInput.value.trim();
  const password = passwordInput.value;
  if (name.length < 2) {
    renderLogin("Le nom du profil doit contenir au moins 2 caracteres.");
    return;
  }
  if (password.length < 4) {
    renderLogin("Le mot de passe local doit contenir au moins 4 caracteres.");
    return;
  }
  const exists = appState.store.users.some((user) => normalize(user.name) === normalize(name));
  if (exists) {
    renderLogin("Ce nom de profil existe deja.");
    return;
  }
  const user = {
    id: crypto.randomUUID(),
    name,
    passwordHash: await hashPassword(password),
    createdAt: new Date().toISOString(),
    data: defaultLocalState(),
  };
  appState.store.users.push(user);
  setActiveUser(user);
  nameInput.value = "";
  passwordInput.value = "";
  rebuildDataForCurrentUser();
  renderLogin();
  renderAccountStrip();
  renderSituations();
  renderSources();
  showView("home");
}

async function loginSelectedProfile() {
  if (appState.backend === "supabase") {
    await loginRemoteProfile();
    return;
  }
  const userId = document.querySelector("#profile-select").value;
  const password = document.querySelector("#profile-password").value;
  const user = appState.store.users.find((item) => item.id === userId);
  if (!user) {
    renderLogin("Selectionnez ou creez un profil.");
    return;
  }
  const passwordHash = await hashPassword(password);
  if (user.passwordHash && user.passwordHash !== passwordHash) {
    renderLogin("Mot de passe local incorrect.");
    return;
  }
  setActiveUser(user);
  document.querySelector("#profile-password").value = "";
  rebuildDataForCurrentUser();
  renderLogin();
  renderAccountStrip();
  renderSituations();
  renderSources();
  showView("home");
}

async function createRemoteProfile() {
  const email = document.querySelector("#profile-email").value.trim();
  const displayName = document.querySelector("#profile-name").value.trim();
  const password = document.querySelector("#profile-password").value;
  if (!email.includes("@")) {
    renderLogin("Renseigne un email valide.");
    return;
  }
  if (displayName.length < 2) {
    renderLogin("Le nom du profil doit contenir au moins 2 caracteres.");
    return;
  }
  if (password.length < 6) {
    renderLogin("Le mot de passe doit contenir au moins 6 caracteres.");
    return;
  }
  const { data, error } = await appState.supabase.auth.signUp({
    email,
    password,
    options: { data: { display_name: displayName } },
  });
  if (error) {
    renderLogin(error.message);
    return;
  }
  if (!data.session) {
    renderLogin("Compte cree. Verifie ton email si la confirmation est activee, puis connecte-toi.");
    return;
  }
  await upsertRemoteProfile(data.user.id, displayName);
  await loadRemoteUserState(data.session);
  rebuildDataForCurrentUser();
  clearAuthInputs();
  renderAccountStrip();
  renderSituations();
  renderSources();
  showView("home");
}

async function loginRemoteProfile() {
  const email = document.querySelector("#profile-email").value.trim();
  const password = document.querySelector("#profile-password").value;
  const displayName = document.querySelector("#profile-name").value.trim();
  if (!email.includes("@") || !password) {
    renderLogin("Renseigne ton email et ton mot de passe.");
    return;
  }
  const { data, error } = await appState.supabase.auth.signInWithPassword({ email, password });
  if (error) {
    renderLogin(error.message);
    return;
  }
  if (displayName) await upsertRemoteProfile(data.user.id, displayName);
  await loadRemoteUserState(data.session);
  rebuildDataForCurrentUser();
  clearAuthInputs();
  renderAccountStrip();
  renderSituations();
  renderSources();
  showView("home");
}

function clearAuthInputs() {
  document.querySelector("#profile-email").value = "";
  document.querySelector("#profile-name").value = "";
  document.querySelector("#profile-password").value = "";
  renderLogin();
}

async function logout() {
  saveLocalState();
  if (appState.backend === "supabase") {
    await appState.supabase.auth.signOut();
  }
  appState.user = null;
  appState.local = defaultLocalState();
  if (appState.backend === "local") {
    appState.store.currentUserId = null;
    saveAccountStore();
  }
  renderLogin();
  renderAccountStrip();
  showView("login");
}

function deleteCurrentProfile() {
  if (appState.backend === "supabase") {
    alert("La suppression complete d'un compte Supabase doit se faire via une fonction serveur ou le dashboard Supabase.");
    return;
  }
  if (!appState.user) return;
  if (!confirm(`Supprimer le profil "${appState.user.name}" et toutes ses donnees locales ?`)) return;
  appState.store.users = appState.store.users.filter((user) => user.id !== appState.user.id);
  appState.store.currentUserId = null;
  appState.user = null;
  appState.local = defaultLocalState();
  saveAccountStore();
  renderLogin();
  renderAccountStrip();
  showView("login");
}

function renderAccountStrip() {
  const strip = document.querySelector("#account-strip");
  if (!appState.user) {
    strip.innerHTML = "";
    return;
  }
  strip.innerHTML = `
    <span><strong>${escapeHtml(appState.user.name)}</strong> · ${appState.backend === "supabase" ? "espace synchronise Supabase" : "espace personnel local"}</span>
    <div class="actions">
      <button data-view="account">Compte</button>
      <button id="logout-button">Deconnexion</button>
    </div>
  `;
  strip.querySelector("[data-view='account']").addEventListener("click", () => showView("account"));
  strip.querySelector("#logout-button").addEventListener("click", logout);
}

function renderAccount() {
  const content = document.querySelector("#account-content");
  if (!appState.user) {
    content.innerHTML = "<p>Aucun profil connecte.</p>";
    return;
  }
  if (appState.backend === "supabase") {
    content.innerHTML = `
      <p>Profil connecte: <strong>${escapeHtml(appState.user.name)}</strong></p>
      <p class="meta">${escapeHtml(appState.user.email || "")}</p>
      <div class="actions">
        <button id="account-logout">Deconnexion</button>
        <button id="export-remote-data">Exporter mes donnees</button>
      </div>
      <p>Les progres, reponses, revisions et imports sont enregistres dans Supabase avec Row Level Security.</p>
    `;
    content.querySelector("#account-logout").addEventListener("click", logout);
    content.querySelector("#export-remote-data").addEventListener("click", exportLocalData);
    return;
  }
  const users = appState.store.users
    .map(
      (user) => `
        <div class="profile-row">
          <div>
            <strong>${escapeHtml(user.name)}</strong><br>
            <span class="meta">Cree le ${formatDate(user.createdAt)} · ${Object.keys(user.data.progress || {}).length} situation(s) commencee(s)</span>
          </div>
          <button ${user.id === appState.user.id ? "disabled" : ""} data-switch-profile="${escapeHtml(user.id)}">Basculer</button>
        </div>
      `
    )
    .join("");
  content.innerHTML = `
    <p>Profil connecte: <strong>${escapeHtml(appState.user.name)}</strong></p>
    <div class="actions">
      <button id="account-logout">Deconnexion</button>
      <button class="danger" id="delete-profile">Supprimer ce profil</button>
    </div>
    <h3>Profils locaux</h3>
    ${users}
  `;
  content.querySelector("#account-logout").addEventListener("click", logout);
  content.querySelector("#delete-profile").addEventListener("click", deleteCurrentProfile);
  content.querySelectorAll("[data-switch-profile]").forEach((button) => {
    button.addEventListener("click", () => {
      saveLocalState();
      const user = appState.store.users.find((item) => item.id === button.dataset.switchProfile);
      if (user) {
        setActiveUser(user);
        rebuildDataForCurrentUser();
        renderLogin();
        renderAccountStrip();
        renderSituations();
        renderSources();
        renderAccount();
      }
    });
  });
}

function showView(id) {
  if (!appState.user && id !== "login") {
    id = "login";
  }
  views.forEach((view) => view.classList.toggle("active", view.id === id));
  if (id === "situations") renderSituations();
  if (id === "dashboard") renderDashboard();
  if (id === "sources") renderSources();
  if (id === "account") renderAccount();
}

function renderSituations() {
  const list = document.querySelector("#situation-list");
  list.innerHTML = "";
  const situations = appState.data.situations.filter(
    (situation) => appState.selectedLevel === "all" || situation.level === appState.selectedLevel
  );
  situations.forEach((situation) => {
    const progress = appState.local.progress[situation.slug];
    const score = progress ? `${progress.score}%` : "0%";
    const completed = progress?.completed ? "terminee" : "en cours";
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <span class="meta">${escapeHtml(situation.level)} · progression ${score} · ${completed}</span>
      <h3>${escapeHtml(situation.title)}</h3>
      <p>${escapeHtml(situation.objective)}</p>
      <div class="actions">
        <button class="primary">Ouvrir</button>
        <button>Exercices</button>
      </div>
    `;
    const [openButton, exerciseButton] = card.querySelectorAll("button");
    openButton.addEventListener("click", () => openLesson(situation.slug));
    exerciseButton.addEventListener("click", () => openExercises(situation.slug));
    list.appendChild(card);
  });
  if (!situations.length) {
    list.innerHTML = `<article class="panel">Aucune situation pour ce filtre.</article>`;
  }
}

function openLesson(slug) {
  appState.currentSituation = appState.data.situations.find((item) => item.slug === slug);
  appState.currentExerciseIndex = 0;
  appState.correctCount = 0;
  markSituationOpened(slug);
  renderLesson();
  showView("lesson");
}

function openExercises(slug) {
  appState.currentSituation = appState.data.situations.find((item) => item.slug === slug);
  appState.currentExerciseIndex = 0;
  appState.correctCount = 0;
  markSituationOpened(slug);
  renderExercise();
  showView("exercise");
}

function markSituationOpened(slug) {
  if (!appState.local.progress[slug]) {
    appState.local.progress[slug] = { opened: true, completed: false, score: 0, lastOpenedAt: null };
  }
  appState.local.progress[slug].opened = true;
  appState.local.progress[slug].lastOpenedAt = new Date().toISOString();
  appState.local.lastSituationSlug = slug;
  saveLocalState();
}

function renderLesson() {
  const situation = appState.currentSituation;
  const content = document.querySelector("#lesson-content");
  const phrases = situation.phrases
    .map(
      (phrase) => `
      <article class="phrase-card">
        <div class="phrase-grid">
          <div><span class="lang-label">FR</span><span class="phrase-value">${escapeHtml(phrase.fr_text)}</span></div>
          <div><span class="lang-label">EN</span><span class="phrase-value">${escapeHtml(phrase.en_text)}</span></div>
          <div><span class="lang-label">IT</span><span class="phrase-value">${escapeHtml(phrase.it_text)}</span></div>
        </div>
        <p>${escapeHtml(phrase.explanation)}</p>
        <p class="trap"><strong>Piege frequent:</strong> ${escapeHtml(phrase.common_trap)}</p>
      </article>
    `
    )
    .join("");
  const grammar = (situation.grammar_points || [])
    .map(
      (point) => `
        <div class="grammar-item">
          <strong>${escapeHtml(point.title)}</strong>
          <p>${escapeHtml(point.explanation)}</p>
          <span class="meta">FR: ${escapeHtml(point.example_fr)} · EN: ${escapeHtml(point.example_en)} · IT: ${escapeHtml(point.example_it)}</span>
        </div>
      `
    )
    .join("");
  content.innerHTML = `
    <h2>${escapeHtml(situation.title)} <span class="meta">${escapeHtml(situation.level)}</span></h2>
    <p>${escapeHtml(situation.objective)}</p>
    <div class="phrase-list">${phrases}</div>
    ${grammar ? `<h3>Points grammaticaux</h3><div class="grammar-list">${grammar}</div>` : ""}
    <div class="actions">
      <button class="primary" id="start-exercises">Faire les exercices</button>
    </div>
  `;
  document.querySelector("#start-exercises").addEventListener("click", () => openExercises(situation.slug));
  document.querySelector("#back-to-lesson").onclick = () => showView("lesson");
}

function renderExercise() {
  const exercise = appState.currentSituation.exercises[appState.currentExerciseIndex];
  const content = document.querySelector("#exercise-content");
  const options = exercise.options || [];
  const answerUi = options.length
    ? `<div class="option-list">${options
        .map(
          (option) => `
            <label>
              <input type="radio" name="answer" value="${escapeHtml(option)}" />
              ${escapeHtml(option)}
            </label>
          `
        )
        .join("")}</div>`
    : `<input id="free-answer" type="text" placeholder="Votre reponse" autocomplete="off" />`;
  content.innerHTML = `
    <span class="meta">Exercice ${appState.currentExerciseIndex + 1}/${appState.currentSituation.exercises.length} · ${escapeHtml(exercise.type)} · difficulte ${escapeHtml(exercise.difficulty)}</span>
    <h2>${escapeHtml(exercise.question)}</h2>
    ${answerUi}
    <div class="actions">
      <button class="primary" id="validate-answer">Valider</button>
      <button id="next-exercise" disabled>Suivant</button>
    </div>
    <div id="feedback"></div>
  `;
  document.querySelector("#validate-answer").addEventListener("click", validateAnswer);
  document.querySelector("#next-exercise").addEventListener("click", nextExercise);
  document.querySelector("#free-answer")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") validateAnswer();
  });
}

function readAnswer() {
  const selected = document.querySelector("input[name='answer']:checked");
  if (selected) return selected.value;
  return document.querySelector("#free-answer")?.value || "";
}

function validateAnswer() {
  const exercise = appState.currentSituation.exercises[appState.currentExerciseIndex];
  const answer = readAnswer();
  const feedback = document.querySelector("#feedback");
  if (!answer.trim()) {
    feedback.innerHTML = `<p class="feedback wrong">Saisissez ou selectionnez une reponse.</p>`;
    return;
  }
  const isCorrect = normalize(answer) === normalize(exercise.correct_answer);
  if (isCorrect) appState.correctCount += 1;
  const message = isCorrect
    ? `Correct. ${exercise.explanation_correct}`
    : `Pas exactement. Reponse attendue: ${exercise.correct_answer}. ${exercise.explanation_wrong}`;
  feedback.innerHTML = `<p class="feedback ${isCorrect ? "ok" : "wrong"}">${escapeHtml(message)}</p>`;
  recordAnswer(exercise, answer, isCorrect, message);
  document.querySelector("#validate-answer").disabled = true;
  document.querySelector("#next-exercise").disabled = false;
}

function recordAnswer(exercise, answer, isCorrect, feedback) {
  const phraseKey = exercise.phrase_fr || exercise.question;
  appState.local.answers.unshift({
    situationSlug: appState.currentSituation.slug,
    exerciseQuestion: exercise.question,
    userAnswer: answer,
    correctAnswer: exercise.correct_answer,
    isCorrect,
    feedback,
    createdAt: new Date().toISOString(),
  });
  appState.local.answers = appState.local.answers.slice(0, 200);
  const review = appState.local.reviews[phraseKey] || {
    phrase: phraseKey,
    strength: 1,
    mistakeCount: 0,
    nextReviewAt: new Date().toISOString(),
  };
  if (isCorrect) {
    review.strength = Math.min(review.strength + 1, 5);
    review.nextReviewAt = addDays(review.strength * 2).toISOString();
  } else {
    review.strength = Math.max(review.strength - 1, 1);
    review.mistakeCount += 1;
    review.nextReviewAt = addHours(12).toISOString();
  }
  appState.local.reviews[phraseKey] = review;
  saveLocalState();
}

function nextExercise() {
  const total = appState.currentSituation.exercises.length;
  if (appState.currentExerciseIndex + 1 < total) {
    appState.currentExerciseIndex += 1;
    renderExercise();
    return;
  }
  const score = Math.round((appState.correctCount / total) * 100);
  appState.local.progress[appState.currentSituation.slug] = {
    opened: true,
    completed: score === 100,
    score,
    lastOpenedAt: new Date().toISOString(),
    completedAt: score === 100 ? new Date().toISOString() : null,
  };
  saveLocalState();
  renderSituations();
  document.querySelector("#exercise-content").innerHTML = `
    <h2>Serie terminee</h2>
    <p>Score: ${appState.correctCount}/${total} (${score}%).</p>
    <div class="actions">
      <button class="primary" data-view="situations">Retour aux situations</button>
      <button data-view="dashboard">Voir le dashboard</button>
    </div>
  `;
  document.querySelectorAll("#exercise-content [data-view]").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
}

function renderDashboard() {
  const progressValues = Object.values(appState.local.progress);
  const started = progressValues.filter((item) => item.opened).length;
  const completed = progressValues.filter((item) => item.completed).length;
  const average = progressValues.length
    ? Math.round(progressValues.reduce((sum, item) => sum + Number(item.score || 0), 0) / progressValues.length)
    : 0;
  const due = Object.values(appState.local.reviews).filter(
    (item) => new Date(item.nextReviewAt) <= new Date()
  ).length;
  document.querySelector("#dashboard-content").innerHTML = `
    <article class="metric">Situations commencees<strong>${started}</strong></article>
    <article class="metric">Situations terminees<strong>${completed}</strong></article>
    <article class="metric">Score moyen<strong>${average}%</strong></article>
    <article class="metric">Elements a reviser<strong>${due}</strong></article>
    <article class="metric">Reponses enregistrees<strong>${appState.local.answers.length}</strong></article>
    <article class="metric">Situations disponibles<strong>${appState.data.situations.length}</strong></article>
  `;
  const mistakes = Object.values(appState.local.reviews)
    .filter((item) => item.mistakeCount > 0)
    .sort((a, b) => b.mistakeCount - a.mistakeCount)
    .slice(0, 6);
  document.querySelector("#mistake-content").innerHTML = `
    <h3>Erreurs frequentes</h3>
    ${
      mistakes.length
        ? mistakes
            .map(
              (item) =>
                `<p><strong>${escapeHtml(item.phrase)}</strong><br><span class="meta">${item.mistakeCount} erreur(s) · force ${item.strength} · revision ${formatDate(item.nextReviewAt)}</span></p>`
            )
            .join("")
        : "<p>Aucune erreur enregistree pour le moment.</p>"
    }
  `;
}

function renderSources() {
  const list = document.querySelector("#source-list");
  list.innerHTML = "";
  appState.data.sources.forEach((source) => {
    const item = document.createElement("article");
    item.className = "card";
    item.innerHTML = `
      <span class="meta">${escapeHtml(source.source_type)} · fiabilite ${escapeHtml(source.reliability_score)}/5 · ${escapeHtml(source.license)}</span>
      <h3>${escapeHtml(source.name)}</h3>
      <a class="source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${escapeHtml(source.url)}</a>
      <p>${escapeHtml(source.notes)}</p>
      <span class="meta">Consulte le ${escapeHtml(source.retrieved_at)}</span>
    `;
    list.appendChild(item);
  });
}

async function handleImport(shouldImport) {
  const file = document.querySelector("#import-file").files[0];
  const output = document.querySelector("#import-result");
  if (!file) {
    output.textContent = "Selectionnez un fichier JSON ou CSV.";
    return;
  }
  try {
    const text = await file.text();
    const payload = file.name.toLowerCase().endsWith(".csv") ? parseCsvPayload(text) : JSON.parse(text);
    const validation = validatePayload(payload);
    if (!validation.valid) {
      output.textContent = "Contenu invalide:\n" + validation.errors.map((error) => `- ${error}`).join("\n");
      return;
    }
    if (!shouldImport) {
      output.textContent = `Validation OK. ${payload.situations.length} situation(s) prete(s) a importer.`;
      return;
    }
    const existingSlugs = new Set(appState.data.situations.map((situation) => situation.slug));
    const newSituations = payload.situations.filter((situation) => !existingSlugs.has(situation.slug));
    if (!newSituations.length) {
      output.textContent = "Import OK, mais aucune nouvelle situation: les slugs existent deja.";
      return;
    }
    const cleanPayload = { ...payload, situations: newSituations };
    appState.local.importedPayloads.push(cleanPayload);
    saveLocalState();
    rebuildDataForCurrentUser();
    renderSituations();
    renderSources();
    output.textContent = `Import termine. ${newSituations.length} situation(s) ajoutee(s).`;
  } catch (error) {
    output.textContent = `Erreur import: ${error.message}`;
  }
}

function validatePayload(payload) {
  const errors = [];
  if (!payload || typeof payload !== "object") errors.push("Le contenu doit etre un objet.");
  const source = payload?.source;
  if (!source || typeof source !== "object") {
    errors.push("Le bloc source est obligatoire.");
  } else {
    REQUIRED_SOURCE_FIELDS.forEach((field) => {
      if (!source[field]) errors.push(`source.${field} est obligatoire.`);
    });
    if (source.retrieved_at && Number.isNaN(Date.parse(source.retrieved_at))) {
      errors.push("source.retrieved_at doit etre une date ISO.");
    }
  }
  if (!Array.isArray(payload?.situations) || payload.situations.length === 0) {
    errors.push("situations doit contenir au moins une situation.");
  } else {
    payload.situations.forEach((situation, index) => {
      const prefix = `situations[${index}]`;
      REQUIRED_SITUATION_FIELDS.forEach((field) => {
        if (!situation[field]) errors.push(`${prefix}.${field} est obligatoire.`);
      });
      if (situation.level && !["A1", "A2", "B1"].includes(situation.level)) {
        errors.push(`${prefix}.level doit etre A1, A2 ou B1.`);
      }
      if (!Array.isArray(situation.phrases) || situation.phrases.length === 0) {
        errors.push(`${prefix}.phrases doit contenir au moins une phrase.`);
      } else {
        situation.phrases.forEach((phrase, phraseIndex) => {
          REQUIRED_PHRASE_FIELDS.forEach((field) => {
            if (!phrase[field]) errors.push(`${prefix}.phrases[${phraseIndex}].${field} est obligatoire.`);
          });
        });
      }
      if (!Array.isArray(situation.exercises) || situation.exercises.length === 0) {
        errors.push(`${prefix}.exercises doit contenir au moins un exercice.`);
      } else {
        situation.exercises.forEach((exercise, exerciseIndex) => {
          REQUIRED_EXERCISE_FIELDS.forEach((field) => {
            if (!exercise[field]) errors.push(`${prefix}.exercises[${exerciseIndex}].${field} est obligatoire.`);
          });
        });
      }
    });
  }
  return { valid: errors.length === 0, errors };
}

function parseCsvPayload(text) {
  const rows = parseCsv(text);
  if (!rows.length) throw new Error("CSV vide.");
  const first = rows[0];
  const source = {
    name: first.source_name || "Import CSV manuel",
    url: first.source_url || "manual://csv-import",
    source_type: first.source_type || "manual",
    license: first.license || "manual",
    retrieved_at: first.retrieved_at || new Date().toISOString().slice(0, 10),
    reliability_score: Number(first.reliability_score || 3),
    notes: first.source_notes || "Import CSV valide manuellement.",
  };
  const situations = {};
  rows.forEach((row) => {
    if (!row.slug) return;
    situations[row.slug] ||= {
      slug: row.slug,
      title: row.title,
      level: row.level,
      objective: row.objective,
      phrases: [],
      exercises: [],
    };
    situations[row.slug].phrases.push({
      fr_text: row.fr_text,
      en_text: row.en_text,
      it_text: row.it_text,
      explanation: row.explanation,
      common_trap: row.common_trap,
    });
    if (row.question) {
      situations[row.slug].exercises.push({
        type: row.exercise_type || "fill_blank",
        question: row.question,
        correct_answer: row.correct_answer,
        options: row.options ? row.options.split("|").filter(Boolean) : [],
        explanation_correct: row.explanation_correct || "Bonne reponse.",
        explanation_wrong: row.explanation_wrong || "Relisez la comparaison.",
        difficulty: Number(row.difficulty || 1),
        phrase_fr: row.phrase_fr || row.fr_text,
      });
    }
  });
  return { source, situations: Object.values(situations) };
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = splitCsvLine(lines.shift()).map((header) => header.trim());
  return lines.map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] || ""]));
  });
}

function splitCsvLine(line) {
  const values = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

function exportLocalData() {
  const exportPayload = {
    user: appState.user ? { id: appState.user.id, name: appState.user.name } : null,
    exportedAt: new Date().toISOString(),
    data: appState.local,
  };
  const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `langues-pas-a-pas-${appState.user?.name || "profil"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

function resetLocalData() {
  if (!confirm("Reinitialiser progression, imports et revisions de ce profil ?")) return;
  appState.local = defaultLocalState();
  saveLocalState();
  rebuildDataForCurrentUser();
  renderSituations();
  renderSources();
  renderDashboard();
  const output = document.querySelector("#import-result");
  if (output) output.textContent = "Donnees du profil reinitialisees.";
}

function addHours(hours) {
  const date = new Date();
  date.setHours(date.getHours() + hours);
  return date;
}

function addDays(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

boot();
