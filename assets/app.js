'use strict';
const $ = (selector, scope=document) => scope.querySelector(selector);
const $$ = (selector, scope=document) => [...scope.querySelectorAll(selector)];
const AIRBNB = 'https://www.airbnb.fr/rooms/926532409861049580';
const BOOKING = 'https://www.booking.com/hotel/fr/paris-auriol.fr.html';
$$('[data-airbnb]').forEach(link => link.href = AIRBNB);
$$('[data-booking]').forEach(link => link.href = BOOKING);

const toggle = $('.mobile-toggle');
const menu = $('#main-menu');
if (toggle && menu) {
  toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) {
      menu.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

const pad = value => String(value).padStart(2, '0');
const localISO = date => `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}`;
const parseISODate = value => {
  const [y,m,d] = String(value).split('-').map(Number);
  return new Date(y, m-1, d);
};
const formatDateTime = value => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat('fr-FR', {dateStyle:'medium', timeStyle:'short', timeZone:'Europe/Paris'}).format(date);
};

async function renderCalendar() {
  const container = $('#calendar');
  if (!container) return;
  const status = $('#calendar-status');
  let payload = {status:'pending', busy:[], updated_at:null};
  try {
    const response = await fetch(`data/calendar.json?v=${Date.now()}`, {cache:'no-store'});
    if (!response.ok) throw new Error('calendar');
    payload = await response.json();
  } catch (error) {
    if (status) status.innerHTML = '<b>Calendrier indisponible.</b> Vérifiez directement les dates sur Airbnb ou Booking.com.';
  }
  const busy = Array.isArray(payload.busy) ? payload.busy : [];
  const now = new Date(); now.setHours(0,0,0,0);
  const weekdays = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
  const monthFormatter = new Intl.DateTimeFormat('fr-FR', {month:'long', year:'numeric'});
  const fragments = [];
  for (let offset=0; offset<3; offset++) {
    const first = new Date(now.getFullYear(), now.getMonth()+offset, 1);
    const last = new Date(first.getFullYear(), first.getMonth()+1, 0);
    const startBlank = (first.getDay()+6)%7;
    let html = `<section class="calendar-month"><h2>${monthFormatter.format(first)}</h2><div class="calendar-grid">`;
    weekdays.forEach(day => html += `<div class="weekday">${day}</div>`);
    for (let i=0; i<startBlank; i++) html += '<div class="day empty" aria-hidden="true"></div>';
    for (let day=1; day<=last.getDate(); day++) {
      const date = new Date(first.getFullYear(), first.getMonth(), day);
      const iso = localISO(date);
      const isPast = date < now;
      const isBusy = !isPast && busy.some(range => iso >= range.start && iso < range.end);
      const state = isPast ? 'past' : (isBusy ? 'busy' : 'free');
      const label = isPast ? 'Passé' : (isBusy ? 'Occupé' : 'Libre');
      const todayClass = date.getTime() === now.getTime() ? ' today' : '';
      html += `<div class="day ${state}${todayClass}" aria-label="${day} ${monthFormatter.format(first)}, ${label}"><b>${day}</b><small>${label}</small></div>`;
    }
    html += '</div></section>';
    fragments.push(html);
  }
  container.innerHTML = fragments.join('');
  if (status && payload.status === 'active') {
    const updated = formatDateTime(payload.updated_at);
    status.innerHTML = `<b>Synchronisation Airbnb + Booking active.</b>${updated ? ` Dernière modification des périodes : ${updated}.` : ''}`;
  } else if (status) {
    status.innerHTML = '<b>Synchronisation en attente d’activation.</b> Les disponibilités affichées sont indicatives : vérifiez les dates sur Airbnb ou Booking.com.';
  }
}

function safeURL(value) {
  try {
    const url = new URL(value);
    return ['http:','https:'].includes(url.protocol) ? url.href : null;
  } catch { return null; }
}
async function renderEvents() {
  const container = $('#events');
  if (!container) return;
  const api = new URL('https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/que-faire-a-paris-/records');
  api.searchParams.set('limit','20');
  api.searchParams.set('where','address_zipcode="75013" and date_end >= now()');
  api.searchParams.set('order_by','date_start asc');
  api.searchParams.set('timezone','Europe/Paris');
  try {
    const response = await fetch(api.toString());
    if (!response.ok) throw new Error('events');
    const data = await response.json();
    const events = (data.results || []).slice(0,12);
    if (!events.length) throw new Error('empty');
    container.textContent = '';
    events.forEach(item => {
      const article = document.createElement('article'); article.className = 'event';
      const time = document.createElement('time');
      const start = item.date_start ? new Date(item.date_start) : null;
      time.textContent = start && !Number.isNaN(start.getTime()) ? new Intl.DateTimeFormat('fr-FR',{day:'2-digit',month:'short'}).format(start) : 'À venir';
      const content = document.createElement('div');
      const title = document.createElement('h3'); title.textContent = item.title || 'Événement à Paris 13e';
      const meta = document.createElement('div'); meta.className = 'event-meta'; meta.textContent = [item.address_name, item.address_street, item.address_zipcode].filter(Boolean).join(' · ');
      const description = document.createElement('p');
      const raw = item.lead_text || item.description || '';
      description.textContent = raw.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim().slice(0,360);
      content.append(title);
      if (meta.textContent) content.append(meta);
      if (description.textContent) content.append(description);
      const url = safeURL(item.url);
      if (url) { const link = document.createElement('a'); link.className='btn light'; link.href=url; link.target='_blank'; link.rel='noopener'; link.textContent='Voir l’événement'; content.append(link); }
      article.append(time, content); container.append(article);
    });
  } catch (error) {
    container.innerHTML = '<div class="notice"><b>Agenda momentanément indisponible.</b> Consultez l’agenda officiel de la Ville de Paris grâce au bouton ci-dessous.</div>';
  }
}
renderCalendar();
renderEvents();
