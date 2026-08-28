'use strict';

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const AIRBNB = 'https://www.airbnb.fr/rooms/926532409861049580';
const BOOKING = 'https://www.booking.com/hotel/fr/paris-auriol.fr.html';
const SUPPORTED_LANGUAGES = ['fr', 'en', 'de', 'es'];
const FALLBACK_LANGUAGE = 'fr';

let catalogue = {
  languages: {
    fr: {label: 'Français', short: 'FR', locale: 'fr-FR'},
    en: {label: 'English', short: 'EN', locale: 'en-GB'},
    de: {label: 'Deutsch', short: 'DE', locale: 'de-DE'},
    es: {label: 'Español', short: 'ES', locale: 'es-ES'},
  },
  messages: {
    'Langue': {en: 'Language', de: 'Sprache', es: 'Idioma'},
    'Ouvrir le menu': {en: 'Open menu', de: 'Menü öffnen', es: 'Abrir el menú'},
    'Fermer le menu': {en: 'Close menu', de: 'Menü schließen', es: 'Cerrar el menú'},
  },
};
let currentLanguage = FALLBACK_LANGUAGE;
let calendarPayload = null;
let eventsPayload = null;
let lightboxState = null;

function normalize(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function languageConfig(language = currentLanguage) {
  return catalogue.languages?.[language] || catalogue.languages.fr;
}

function translated(source, language = currentLanguage) {
  const key = normalize(source);
  if (!key || language === 'fr') return key;
  return catalogue.messages?.[key]?.[language] || key;
}

function pageKey() {
  const file = location.pathname.split('/').filter(Boolean).pop();
  return file && file.includes('.') ? file : 'index.html';
}

function languageFromPath() {
  const firstSegment = location.pathname.split('/').filter(Boolean)[0]?.toLowerCase();
  return SUPPORTED_LANGUAGES.includes(firstSegment) ? firstSegment : FALLBACK_LANGUAGE;
}

function localizedURL(language) {
  const selected = SUPPORTED_LANGUAGES.includes(language) ? language : FALLBACK_LANGUAGE;
  const file = pageKey();
  const suffix = file === 'index.html' ? '' : file;
  const pathname = selected === 'fr' ? `/${suffix}` : `/${selected}/${suffix}`;
  return `${pathname}${location.hash || ''}`;
}

function redirectLegacyLanguageQuery() {
  const requested = new URLSearchParams(location.search).get('lang')?.toLowerCase();
  if (!SUPPORTED_LANGUAGES.includes(requested) || requested === languageFromPath()) return false;
  location.replace(localizedURL(requested));
  return true;
}

function setupMenu() {
  const toggle = $('.mobile-toggle');
  const menu = $('#main-menu');
  if (!toggle || !menu) return;
  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', translated(open ? 'Fermer le menu' : 'Ouvrir le menu'));
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) {
      menu.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', translated('Ouvrir le menu'));
    }
  });
}

function injectLanguagePicker() {
  const menu = $('#main-menu');
  if (!menu || $('.language-picker', menu)) return;
  const picker = document.createElement('label');
  picker.className = 'language-picker';
  picker.innerHTML = `
    <span class="sr-only">${translated('Langue')}</span>
    <span class="language-icon" aria-hidden="true">🌐</span>
    <select id="language-select" aria-label="${translated('Langue')}">
      ${SUPPORTED_LANGUAGES.map(language => {
        const config = languageConfig(language);
        return `<option value="${language}">${config.short} · ${config.label}</option>`;
      }).join('')}
    </select>`;
  const bookingButton = $('.nav-book', menu);
  menu.insertBefore(picker, bookingButton || null);
  const select = $('#language-select');
  select.value = currentLanguage;
  select.addEventListener('change', event => {
    const language = event.target.value;
    try { localStorage.setItem('parisauriol-language', language); } catch (_) {}
    location.assign(localizedURL(language));
  });
}

function galleryCaption(item, language = currentLanguage) {
  const suffix = language.charAt(0).toUpperCase() + language.slice(1);
  return item.dataset[`caption${suffix}`] || item.dataset.captionFr || '';
}

function updateGalleryCaptions() {
  $$('[data-lightbox]').forEach(item => {
    const caption = galleryCaption(item);
    const visibleCaption = $('.gallery-caption', item);
    const image = $('img', item);
    if (visibleCaption) visibleCaption.textContent = caption;
    if (image) image.alt = caption;
  });
}

const pad = value => String(value).padStart(2, '0');
const localISO = date => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;

function formatDateTime(value) {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(languageConfig().locale, {
    dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Paris',
  }).format(date);
}

function weekdayLabels() {
  return {
    fr: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
    en: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    de: ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
    es: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
  }[currentLanguage];
}

async function loadCalendar() {
  if (!$('#calendar')) return;
  try {
    const response = await fetch(`/data/calendar.json?v=${Date.now()}`, {cache: 'no-store'});
    if (!response.ok) throw new Error('calendar');
    calendarPayload = await response.json();
  } catch (_) {
    calendarPayload = {status: 'error', busy: [], updated_at: null};
  }
  renderCalendar();
}

function renderCalendar() {
  const container = $('#calendar');
  if (!container) return;
  const status = $('#calendar-status');
  const payload = calendarPayload || {status: 'pending', busy: [], updated_at: null};
  const busy = Array.isArray(payload.busy) ? payload.busy : [];
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const monthFormatter = new Intl.DateTimeFormat(languageConfig().locale, {month: 'long', year: 'numeric'});
  const fragments = [];

  for (let offset = 0; offset < 3; offset += 1) {
    const first = new Date(now.getFullYear(), now.getMonth() + offset, 1);
    const last = new Date(first.getFullYear(), first.getMonth() + 1, 0);
    const startBlank = (first.getDay() + 6) % 7;
    let markup = `<section class="calendar-month"><h2>${monthFormatter.format(first)}</h2><div class="calendar-grid">`;
    weekdayLabels().forEach(day => { markup += `<div class="weekday">${day}</div>`; });
    for (let blank = 0; blank < startBlank; blank += 1) markup += '<div class="day empty" aria-hidden="true"></div>';
    for (let day = 1; day <= last.getDate(); day += 1) {
      const date = new Date(first.getFullYear(), first.getMonth(), day);
      const iso = localISO(date);
      const isPast = date < now;
      const isBusy = !isPast && busy.some(range => iso >= range.start && iso < range.end);
      const state = isPast ? 'past' : (isBusy ? 'busy' : 'free');
      const sourceLabel = isPast ? 'Passé' : (isBusy ? 'Occupé' : 'Libre');
      const label = translated(sourceLabel);
      const todayClass = date.getTime() === now.getTime() ? ' today' : '';
      markup += `<div class="day ${state}${todayClass}" aria-label="${day} ${monthFormatter.format(first)}, ${label}"><b>${day}</b><small>${label}</small></div>`;
    }
    markup += '</div></section>';
    fragments.push(markup);
  }
  container.innerHTML = fragments.join('');

  if (!status) return;
  if (payload.status === 'active') {
    const updated = formatDateTime(payload.updated_at);
    status.innerHTML = `<b>${translated('Synchronisation Airbnb + Booking active.')}</b>${updated ? ` ${translated('Dernière modification des périodes :')} ${updated}.` : ''}`;
  } else if (payload.status === 'error') {
    status.innerHTML = `<b>${translated('Calendrier indisponible.')}</b> ${translated('Vérifiez directement les dates sur Airbnb ou Booking.com.')}`;
  } else {
    status.innerHTML = `<b>${translated('Synchronisation en attente d’activation.')}</b> ${translated('Les disponibilités affichées sont indicatives : vérifiez les dates sur Airbnb ou Booking.com.')}`;
  }
}

function safeURL(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch (_) {
    return null;
  }
}

async function loadEvents() {
  if (!$('#events')) return;
  const api = new URL('https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records');
  api.searchParams.set('limit', '20');
  api.searchParams.set('where', 'address_zipcode="75013" and date_end >= now()');
  api.searchParams.set('order_by', 'date_start asc');
  api.searchParams.set('timezone', 'Europe/Paris');
  try {
    const response = await fetch(api.toString());
    if (!response.ok) throw new Error('events');
    const data = await response.json();
    eventsPayload = (data.results || []).slice(0, 12);
    if (!eventsPayload.length) throw new Error('empty');
  } catch (_) {
    eventsPayload = false;
  }
  renderEvents();
}

function renderEvents() {
  const container = $('#events');
  if (!container) return;
  if (!Array.isArray(eventsPayload)) {
    container.innerHTML = `<div class="notice"><b>${translated('Agenda momentanément indisponible.')}</b> ${translated('Consultez l’agenda officiel de la Ville de Paris grâce au bouton ci-dessous.')}</div>`;
    return;
  }
  container.textContent = '';
  eventsPayload.forEach(item => {
    const article = document.createElement('article');
    article.className = 'event';
    const time = document.createElement('time');
    const start = item.date_start ? new Date(item.date_start) : null;
    time.textContent = start && !Number.isNaN(start.getTime())
      ? new Intl.DateTimeFormat(languageConfig().locale, {day: '2-digit', month: 'short'}).format(start)
      : translated('À venir');
    const content = document.createElement('div');
    const title = document.createElement('h3');
    title.textContent = item.title || translated('Événement à Paris 13e');
    const meta = document.createElement('div');
    meta.className = 'event-meta';
    meta.textContent = [item.address_name, item.address_street, item.address_zipcode].filter(Boolean).join(' · ');
    const description = document.createElement('p');
    const raw = item.lead_text || item.description || '';
    description.textContent = raw.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 360);
    content.append(title);
    if (meta.textContent) content.append(meta);
    if (description.textContent) content.append(description);
    const url = safeURL(item.url);
    if (url) {
      const link = document.createElement('a');
      link.className = 'btn light';
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = translated('Voir l’événement');
      content.append(link);
    }
    article.append(time, content);
    container.append(article);
  });
}

function createLightbox() {
  const items = $$('[data-lightbox]');
  if (!items.length) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'photo-lightbox';
  dialog.innerHTML = `
    <button class="lightbox-close" type="button">×</button>
    <button class="lightbox-nav lightbox-prev" type="button">‹</button>
    <figure><img alt=""><figcaption></figcaption></figure>
    <button class="lightbox-nav lightbox-next" type="button">›</button>`;
  document.body.append(dialog);
  lightboxState = {
    dialog,
    items,
    index: 0,
    image: $('img', dialog),
    caption: $('figcaption', dialog),
    close: $('.lightbox-close', dialog),
    previous: $('.lightbox-prev', dialog),
    next: $('.lightbox-next', dialog),
  };
  items.forEach((item, index) => {
    item.addEventListener('click', event => {
      event.preventDefault();
      lightboxState.index = index;
      renderLightbox(index);
      dialog.showModal();
      document.body.classList.add('lightbox-open');
    });
  });
  lightboxState.close.addEventListener('click', () => dialog.close());
  lightboxState.previous.addEventListener('click', () => renderLightbox(lightboxState.index - 1));
  lightboxState.next.addEventListener('click', () => renderLightbox(lightboxState.index + 1));
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => document.body.classList.remove('lightbox-open'));
  document.addEventListener('keydown', event => {
    if (!dialog.open) return;
    if (event.key === 'ArrowLeft') renderLightbox(lightboxState.index - 1);
    if (event.key === 'ArrowRight') renderLightbox(lightboxState.index + 1);
  });
  updateLightboxControls();
}

function renderLightbox(index) {
  if (!lightboxState) return;
  const length = lightboxState.items.length;
  lightboxState.index = (index + length) % length;
  const item = lightboxState.items[lightboxState.index];
  const caption = galleryCaption(item);
  lightboxState.image.src = item.getAttribute('href');
  lightboxState.image.alt = caption;
  lightboxState.caption.textContent = `${lightboxState.index + 1} / ${length} · ${caption}`;
}

function updateLightboxControls() {
  if (!lightboxState) return;
  lightboxState.close.setAttribute('aria-label', translated('Fermer la galerie'));
  lightboxState.previous.setAttribute('aria-label', translated('Photo précédente'));
  lightboxState.next.setAttribute('aria-label', translated('Photo suivante'));
}

async function init() {
  if (redirectLegacyLanguageQuery()) return;
  currentLanguage = languageFromPath();
  document.documentElement.lang = currentLanguage;
  $$('[data-airbnb]').forEach(link => { link.href = AIRBNB; });
  $$('[data-booking]').forEach(link => { link.href = BOOKING; });
  const needsDynamicTranslations = Boolean($('#calendar') || $('#events') || $('[data-lightbox]'));
  if (needsDynamicTranslations) {
    try {
      const response = await fetch('/assets/translations.json', {cache: 'force-cache'});
      if (response.ok) catalogue = await response.json();
    } catch (error) {
      console.warn('Traductions dynamiques indisponibles.', error);
    }
  }
  injectLanguagePicker();
  setupMenu();
  updateGalleryCaptions();
  createLightbox();
  await Promise.allSettled([loadCalendar(), loadEvents()]);
}

init();
