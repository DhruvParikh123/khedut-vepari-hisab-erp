// Antigravity / Django Khedut & Vepari Billing App JS

const $ = id => document.getElementById(id);
const $$ = s => [...document.querySelectorAll(s)];
const money = n => (Number(n) || 0).toFixed(2);
const today = () => new Date().toISOString().slice(0, 10);

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');

function toast(msg, type = 'success') {
  let t = $('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = type;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 3200);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// Tab Switching
const tabTitles = {
  'farmer': '🌾 ખેડૂત ખરીદી બિલ',
  'trader': '🏪 વેપારી વેચાણ બિલ',
  'gst': '🧾 GST પાકું ઇન્વોઇસ',
  'ledger': '📖 ખતાવહી & બાકી હિસાબ',
  'daily': '📅 રોજનો હિસાબ (રોજમેળ)',
  'expense': '💸 ખર્ચ નોંધણી',
  'settings': '⚙️ પેઢી સેટિંગ્સ & માસ્ટર'
};

function tab(id, btn) {
  $$('.tab').forEach(x => x.classList.remove('active'));
  const target = $(id);
  if (target) {
    target.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  $$('.sidebar-nav button, nav button, .nav-item').forEach(x => {
    if (x.getAttribute('data-tab') === id || x === btn) {
      x.classList.add('active');
    } else {
      x.classList.remove('active');
    }
  });

  const titleEl = $('activeModuleTitle');
  if (titleEl && tabTitles[id]) {
    titleEl.textContent = tabTitles[id];
  }

  if (id === 'trader') loadPicks();
  if (id === 'daily') renderDaily();
  if (id === 'ledger') renderLedger();

  closeMobileSidebar();
}

function toggleSidebar() {
  const sidebar = $('appSidebar');
  const backdrop = $('sidebarBackdrop');

  if (window.innerWidth <= 768) {
    if (sidebar) sidebar.classList.toggle('open');
    if (backdrop) backdrop.classList.toggle('active');
  } else {
    toggleSidebarCollapse();
  }
}

function closeMobileSidebar() {
  const sidebar = $('appSidebar');
  const backdrop = $('sidebarBackdrop');
  if (sidebar) sidebar.classList.remove('open');
  if (backdrop) backdrop.classList.remove('active');
}

function toggleSidebarCollapse() {
  const appLayout = document.querySelector('.app-layout');
  if (appLayout) {
    appLayout.classList.toggle('sidebar-collapsed');
    const isCollapsed = appLayout.classList.contains('sidebar-collapsed');
    localStorage.setItem('sidebar_collapsed', isCollapsed ? '1' : '0');

    const collapseBtns = document.querySelectorAll('.sidebar-collapse-btn');
    collapseBtns.forEach(btn => {
      btn.innerHTML = isCollapsed ? '›' : '‹';
      btn.title = isCollapsed ? 'Sidebar ખોલો (Expand)' : 'Sidebar સંકોચો (Collapse)';
    });
  }
}

// PRO: Real-time Live History Search Filter
function filterList(containerId, query) {
  const container = $(containerId);
  if (!container) return;
  const q = String(query || '').toLowerCase().trim();
  const items = container.querySelectorAll('.rowitem, .billrow');
  items.forEach(el => {
    const text = el.textContent.toLowerCase();
    const matches = !q || text.includes(q);
    el.style.display = matches ? '' : 'none';
  });
}

// PRO: Global ERP Function Key Shortcuts (F2 - F9)
document.addEventListener('keydown', (e) => {
  const keyMap = {
    'F2': 'farmer',
    'F3': 'trader',
    'F4': 'gst',
    'F6': 'ledger',
    'F7': 'daily',
    'F8': 'expense',
    'F9': 'settings'
  };
  if (keyMap[e.key]) {
    e.preventDefault();
    tab(keyMap[e.key]);
  }
});

// ------------------- FARMER BILL -------------------
function addFRow(x = {}) {
  let tr = document.createElement('tr');
  let traderOptions = window.traderNamesList.map(n => `<option ${n === (x.trader || '') ? 'selected' : ''}>${esc(n)}</option>`).join('');
  tr.innerHTML = `
    <td><input class="ft" value="${esc(x.type || 'તમાકુ')}"></td>
    <td><select class="fx"><option value="">-- પસંદ કરો --</option>${traderOptions}</select></td>
    <td><input class="fb" type="number" min="0" step="any" value="${x.bags || 0}" oninput="calcF()"></td>
    <td><input class="fw" type="number" min="0" step=".01" value="${x.weight || 0}" oninput="calcF()"></td>
    <td><input class="fr" type="number" min="0" step=".01" value="${x.rate || 0}" oninput="calcF()"></td>
    <td class="fa">0.00</td>
    <td><button type="button" class="btn red smallbtn" onclick="this.closest('tr').remove();calcF()">×</button></td>
  `;
  $('fRows').appendChild(tr);
  calcF();
}

function fItems() {
  return [...$('fRows').rows].map(r => {
    let bags = +r.querySelector('.fb').value || 0;
    let w = +r.querySelector('.fw').value || 0;
    let rate = +r.querySelector('.fr').value || 0;
    let amount = (w * rate) / 20;
    r.querySelector('.fa').textContent = money(amount);
    return {
      type: r.querySelector('.ft').value,
      trader: r.querySelector('.fx').value,
      bags,
      weight: w,
      rate,
      amount
    };
  });
}

function calcF() {
  let items = fItems();
  let bardanRate = Number(window.appSettings.bard || 15);
  let bags = items.reduce((v, x) => v + x.bags, 0);
  let base = items.reduce((v, x) => v + x.amount, 0);
  let bard = bags * bardanRate;
  let lab = +$('fLab').value || 0;
  let ded = +$('fDed').value || 0;
  let sub = base + bard + lab - ded;
  let gstRate = +$('fVat').value || 0;
  let tax = $('fKind').value === 'GST' ? (sub * gstRate) / 100 : 0;
  let total = sub + tax;

  $('fBard').value = money(bard);
  $('fBase').textContent = money(base);
  $('fTax').textContent = money(tax);
  $('fTotal').textContent = money(total);

  if ($('fPayStatus').value === 'paid' && document.activeElement !== $('fPaid')) {
    $('fPaid').value = money(total);
  }
  calcFarmerDue();
}

function toggleGST() {
  $$('.gstfield').forEach(x => {
    const isFarmerGst = $('fKind').value === 'GST' && x.querySelector('#fVat');
    const isTraderGst = $('tKind').value === 'GST' && x.querySelector('#tVat');
    x.classList.toggle('hide', !(isFarmerGst || isTraderGst));
  });
  calcF();
  calcT();
}

function syncFarmerPaid() {
  let total = +$('fTotal').textContent || 0;
  if ($('fPayStatus').value === 'paid') {
    $('fPaid').value = money(total);
  } else {
    $('fPaid').value = '0.00';
  }
}

function calcFarmerDue() {
  let total = +$('fTotal').textContent || 0;
  let paid = Math.min(total, +$('fPaid').value || 0);
  // Keep paid value updated
}

async function saveF() {
  let name = $('fName').value.trim();
  if (!name) return toast('ખેડૂતનું નામ દાખલ કરો.', 'error');
  let items = fItems();
  if (!items.length) return toast('ઓછામાં ઓછી એક માલની વિગત આપો.', 'error');

  let payload = {
    no: $('fNo').value.trim(),
    date: $('fDate').value,
    firm: $('fFirm').value.trim(),
    name: name,
    mobile: $('fMobile').value.trim(),
    village: $('fVillage').value.trim(),
    plot: $('fPlot').value.trim(),
    kind: $('fKind').value,
    items: items,
    bard: +$('fBard').value || 0,
    lab: +$('fLab').value || 0,
    ded: +$('fDed').value || 0,
    vat: +$('fVat').value || 0,
    paid: +$('fPaid').value || 0,
    status: $('fPayStatus').value,
    mode: $('fPayMode') ? $('fPayMode').value : 'cash'
  };

  try {
    let res = await fetch('/api/farmer-bill/save/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(payload)
    });
    let d = await res.json();
    if (d.success) {
      toast('ખેડૂત બિલ સેવ થયું!');
      setTimeout(() => window.location.reload(), 800);
    } else {
      toast(d.error || 'ભૂલ આવી.', 'error');
    }
  } catch (err) {
    toast('સર્વર કનેક્શનમાં ભૂલ આવી.', 'error');
  }
}

function newF() {
  ['fName', 'fMobile', 'fVillage', 'fPlot'].forEach(id => $(id).value = '');
  $('fLab').value = 0;
  $('fDed').value = 0;
  $('fPayStatus').value = 'due';
  $('fPaid').value = 0;
  $('fRows').innerHTML = '';
  addFRow();
  calcF();
}

async function delF(id) {
  if (!confirm('આ ખેડૂત બિલ ડિલીટ કરવું છે?')) return;
  let res = await fetch(`/api/farmer-bill/delete/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('બિલ ડિલીટ થયું.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// ------------------- TRADER BILL -------------------
async function loadPicks() {
  let trader = $('tName').value;
  if ($('tMode').value === 'manual') {
    toggleTraderMode();
    return;
  }
  if (!trader) {
    $('picks').innerHTML = 'પહેલા વેપારી પસંદ કરો.';
    $('tRows').innerHTML = '';
    calcT();
    return;
  }

  $('picks').innerHTML = 'લોડ થઈ રહ્યું છે...';
  try {
    let res = await fetch(`/api/trader-bill/unbilled-items/?trader=${encodeURIComponent(trader)}`);
    let d = await res.json();
    window.currentTraderPicks = d.items || [];
    if (!d.items.length) {
      $('picks').innerHTML = 'આ વેપારી માટે ખેડૂત બિલમાં કોઈ માલ નથી.';
    } else {
      $('picks').innerHTML = d.items.map((it, idx) => `
        <label class="rowitem">
          <span>
            <input type="checkbox" class="pick-item" data-idx="${idx}" checked onchange="calcT()">
            બિલ #${esc(it.bill_no)} · ખેડૂત: ${esc(it.farmer_name)} (${esc(it.village || '')}) · ${it.bags} બેગ · ${it.weight} કિ.ગ્રા. · ₹${money(it.amount)}
          </span>
        </label>
      `).join('');
    }
    calcT();
  } catch (err) {
    $('picks').innerHTML = 'માલ લોડ કરવામાં ભૂલ આવી.';
  }
}

function toggleTraderMode() {
  let manual = $('tMode').value === 'manual';
  $('autoTraderCard').classList.toggle('hide', manual);
  $('manualTraderActions').classList.toggle('hide', !manual);
  if (manual) {
    $('tRows').innerHTML = '';
    addTRow();
  } else {
    $('tRows').innerHTML = '';
    loadPicks();
  }
  calcT();
}

function addTRow(x = {}) {
  let tr = document.createElement('tr');
  tr.innerHTML = `
    <td><input class="tt" value="${esc(x.type || 'તમાકુ')}"></td>
    <td><input class="tf" value="${esc(x.farmer || '')}" placeholder="ખેડૂતનું નામ"></td>
    <td><input class="tb" type="number" min="0" step="any" value="${x.bags || 0}" oninput="calcT()"></td>
    <td><input class="tw" type="number" min="0" step=".01" value="${x.weight || 0}" oninput="calcT()"></td>
    <td><input class="tr" type="number" min="0" step=".01" value="${x.rate || 0}" oninput="calcT()"></td>
    <td class="ta">0.00</td>
    <td><button type="button" class="btn red smallbtn" onclick="this.closest('tr').remove();calcT()">×</button></td>
  `;
  $('tRows').appendChild(tr);
  calcT();
}

function manualTraderItems() {
  return [...$('tRows').querySelectorAll('tr')].map(r => {
    let bags = +r.querySelector('.tb').value || 0;
    let w = +r.querySelector('.tw').value || 0;
    let rate = +r.querySelector('.tr').value || 0;
    let amount = (w * rate) / 20;
    r.querySelector('.ta').textContent = money(amount);
    return {
      type: r.querySelector('.tt').value,
      farmer_name: r.querySelector('.tf').value,
      bags,
      weight: w,
      rate,
      amount
    };
  });
}

function calcT() {
  let items = [];
  if ($('tMode').value === 'manual') {
    items = manualTraderItems();
  } else {
    let picks = window.currentTraderPicks || [];
    let checkedIndices = $$('.pick-item:checked').map(el => +el.dataset.idx);
    items = checkedIndices.map(i => picks[i]).filter(Boolean);
    $('tRows').innerHTML = items.map(x => `
      <tr>
        <td>${esc(x.item_type || x.type)}</td>
        <td>${esc(x.farmer_name || '')}</td>
        <td>${x.bags}</td>
        <td>${x.weight}</td>
        <td>${x.rate}</td>
        <td>${money(x.amount)}</td>
        <td></td>
      </tr>
    `).join('');
  }

  let base = items.reduce((s, x) => s + (x.amount || 0), 0);
  let bags = items.reduce((s, x) => s + (x.bags || 0), 0);

  let commRate = Number(window.appSettings.comm || 1.5);
  let marketRate = Number(window.appSettings.market || 3);
  let bardanRate = Number(window.appSettings.bard || 15);

  let comm = (base * commRate) / 100;
  let market = bags * marketRate;
  let bard = bags * bardanRate;
  let lab = +$('tLab').value || 0;
  let rent = +$('tRent').value || 0;
  let sub = base + comm + market + bard + lab + rent;
  let gstRate = +$('tVat').value || 0;
  let tax = $('tKind').value === 'GST' ? (sub * gstRate) / 100 : 0;
  let total = sub + tax;

  $('tBase').textContent = money(base);
  $('tComm').value = money(comm);
  $('tMarket').value = money(market);
  $('tBard').value = money(bard);
  $('tTax').textContent = money(tax);
  $('tTotal').textContent = money(total);
}

async function saveT() {
  let trader = $('tName').value;
  if (!trader) return toast('વેપારી પસંદ કરો.', 'error');

  let items = [];
  if ($('tMode').value === 'manual') {
    items = manualTraderItems();
  } else {
    let picks = window.currentTraderPicks || [];
    let checkedIndices = $$('.pick-item:checked').map(el => +el.dataset.idx);
    items = checkedIndices.map(i => picks[i]).filter(Boolean);
  }

  if (!items.length) return toast('માલની વિગતો આપો.', 'error');

  let payload = {
    no: $('tNo').value.trim(),
    date: $('tDate').value,
    firm: $('tFirm').value.trim(),
    trader: trader,
    kind: $('tKind').value,
    mode: $('tMode').value,
    items: items,
    lab: +$('tLab').value || 0,
    rent: +$('tRent').value || 0,
    vat: +$('tVat').value || 0
  };

  try {
    let res = await fetch('/api/trader-bill/save/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(payload)
    });
    let d = await res.json();
    if (d.success) {
      toast('વેપારી બિલ સેવ થયું!');
      setTimeout(() => window.location.reload(), 800);
    } else {
      toast(d.error || 'ભૂલ આવી.', 'error');
    }
  } catch (err) {
    toast('સર્વર કનેક્શનમાં ભૂલ આવી.', 'error');
  }
}

function newT() {
  ['tLab', 'tRent'].forEach(id => $(id).value = 0);
  $('tMode').value = 'auto';
  $('tRows').innerHTML = '';
  toggleTraderMode();
}

async function delT(id) {
  if (!confirm('આ વેપારી બિલ ડિલીટ કરવું છે?')) return;
  let res = await fetch(`/api/trader-bill/delete/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('બિલ ડિલીટ થયું.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// ------------------- GST BILL -------------------
function calcG() {
  let w = +$('gWeight').value || 0;
  let p = +$('gPrice').value || 0;
  let base = (w * p) / 20;
  let rate = +$('gRate').value || 0;
  let tax = (base * rate) / 100;
  let cgst = 0, igst = 0;
  if ($('gTaxType').value === 'igst') {
    igst = tax;
  } else {
    cgst = tax / 2;
  }

  $('gBase').textContent = money(base);
  $('gTax').textContent = money(tax);
  $('gCGST').textContent = money(cgst);
  $('gIGST').textContent = money(igst);
  $('gTotal').textContent = money(base + tax);
}

async function saveG() {
  let party = $('gParty').value.trim();
  if (!party) return toast('વેપારી / ગ્રાહકનું નામ દાખલ કરો.', 'error');

  let payload = {
    no: $('gNo').value.trim(),
    date: $('gDate').value,
    firm: $('gFirm').value.trim(),
    firmAddress: $('gFirmAddress').value.trim(),
    firmGST: $('gFirmGST').value.trim(),
    party: party,
    partyAddress: $('gPartyAddress').value.trim(),
    partyGST: $('gPartyGST').value.trim(),
    desc: $('gDesc').value.trim(),
    bags: +$('gBags').value || 0,
    weight: +$('gWeight').value || 0,
    price: +$('gPrice').value || 0,
    rate: +$('gRate').value || 0,
    taxType: $('gTaxType').value
  };

  try {
    let res = await fetch('/api/gst-bill/save/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(payload)
    });
    let d = await res.json();
    if (d.success) {
      toast('GST બિલ સેવ થયું!');
      setTimeout(() => window.location.reload(), 800);
    } else {
      toast(d.error || 'ભૂલ આવી.', 'error');
    }
  } catch (err) {
    toast('સર્વર કનેક્શનમાં ભૂલ આવી.', 'error');
  }
}

function newG() {
  ['gParty', 'gPartyAddress', 'gPartyGST'].forEach(id => $(id).value = '');
  ['gBags', 'gWeight', 'gPrice', 'gRate'].forEach(id => $(id).value = 0);
  $('gTaxType').value = 'cgst';
  calcG();
}

async function delG(id) {
  if (!confirm('આ GST બિલ ડિલીટ કરવું છે?')) return;
  let res = await fetch(`/api/gst-bill/delete/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('બિલ ડિલીટ થયું.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// ------------------- LEDGER & PAYMENTS -------------------
async function renderLedger() {
  let from = $('lFrom').value;
  let to = $('lTo').value;
  let type = $('ledgerFilterType').value;

  $('ledgerRows').innerHTML = 'લોડ થઈ રહ્યું છે...';
  try {
    let res = await fetch(`/api/ledger/summary/?from=${from}&to=${to}&type=${type}`);
    let d = await res.json();
    let rows = [];

    if (d.farmers && d.farmers.length) {
      d.farmers.forEach(f => {
        rows.push(`<div class="billrow">🌾 <b>ખેડૂત:</b> ${esc(f.name)} | બિલ કુલ: ₹${money(f.bill_total)} | ચૂકવેલ: ₹${money(f.paid_total)} | <b class="redText">બાકી: ₹${money(f.due)}</b></div>`);
      });
    }

    if (d.traders && d.traders.length) {
      d.traders.forEach(t => {
        rows.push(`<div class="billrow">🏪 <b>વેપારી:</b> ${esc(t.name)} | બિલ કુલ: ₹${money(t.bill_total)} | આવેલ: ₹${money(t.received_total)} | <b class="redText">બાકી: ₹${money(t.due)}</b></div>`);
      });
    }

    if (d.payments && d.payments.length) {
      d.payments.forEach(p => {
        let label = p.party_type === 'farmer' ? 'ખેડૂતને ચૂકવણી' : 'વેપારી પાસેથી આવેલ';
        rows.push(`<div class="billrow">💳 ${p.date} · ${label} · <b>${esc(p.party_name)}</b> · ₹${money(p.amount)} (${p.mode === 'cash' ? 'રોકડ' : 'બેંક'}) ${p.note ? '· ' + esc(p.note) : ''}</div>`);
      });
    }

    $('ledgerRows').innerHTML = rows.join('') || '<div class="hint">આ ફિલ્ટરમાં કોઈ રેકોર્ડ નથી.</div>';
  } catch (e) {
    $('ledgerRows').innerHTML = '<div class="hint">ડેટા લોડ કરવામાં ભૂલ આવી.</div>';
  }
}

async function loadFarmerDue() {
  let name = $('lpFarmer').value;
  if (!name) {
    $('lpDue').textContent = '0.00';
    return;
  }
  let res = await fetch(`/api/ledger/party-due/?type=farmer&name=${encodeURIComponent(name)}`);
  let d = await res.json();
  $('lpDue').textContent = money(d.due);
}

async function loadTraderDue() {
  let name = $('tpTrader').value;
  if (!name) {
    $('tpDue').textContent = '0.00';
    return;
  }
  let res = await fetch(`/api/ledger/party-due/?type=trader&name=${encodeURIComponent(name)}`);
  let d = await res.json();
  $('tpDue').textContent = money(d.due);
}

async function saveFarmerPayment() {
  let name = $('lpFarmer').value;
  let amt = +$('lpAmount').value || 0;
  if (!name || amt <= 0) return toast('ખેડૂત અને રકમ દાખલ કરો.', 'error');

  let res = await fetch('/api/ledger/save-payment/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({
      type: 'farmer',
      name: name,
      date: $('lpDate').value,
      amount: amt,
      mode: $('lpMode').value
    })
  });
  let d = await res.json();
  if (d.success) {
    toast('ખેડૂત ચુકવણી સેવ થઈ!');
    $('lpAmount').value = '';
    loadFarmerDue();
    renderLedger();
  }
}

async function saveTraderPayment() {
  let name = $('tpTrader').value;
  let amt = +$('tpAmount').value || 0;
  if (!name || amt <= 0) return toast('વેપારી અને રકમ દાખલ કરો.', 'error');

  let res = await fetch('/api/ledger/save-payment/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({
      type: 'trader',
      name: name,
      date: $('tpDate').value,
      amount: amt,
      mode: $('tpMode').value
    })
  });
  let d = await res.json();
  if (d.success) {
    toast('વેપારી ચુકવણી સેવ થઈ!');
    $('tpAmount').value = '';
    loadTraderDue();
    renderLedger();
  }
}

async function saveL() {
  let amt = +$('lAmount').value || 0;
  if (!amt) return toast('માન્ય રકમ દાખલ કરો.', 'error');

  let res = await fetch('/api/ledger/save-entry/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({
      date: $('lDate').value,
      party: $('lParty').value.trim(),
      desc: $('lDesc').value.trim(),
      type: $('lType').value,
      amount: amt,
      account: $('lAccount').value
    })
  });
  let d = await res.json();
  if (d.success) {
    toast('ખાતાવહી નોંધ સેવ થઈ!');
    $('lAmount').value = '';
    setTimeout(() => window.location.reload(), 600);
  }
}

async function delL(id) {
  if (!confirm('આ નોંધ ડિલીટ કરવી છે?')) return;
  let res = await fetch(`/api/ledger/delete-entry/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('નોંધ ડિલીટ થઈ.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// ------------------- DAILY HISAB -------------------
async function renderDaily() {
  let dVal = $('dDate').value || today();
  try {
    let res = await fetch(`/api/daily/summary/?date=${dVal}`);
    let d = await res.json();

    $('dailyStats').innerHTML = `
      <div class="stat"><span>આજની જમા (આવક)</span><b class="greenText">₹${money(d.income)}</b></div>
      <div class="stat"><span>આજની ઉધાર (ચુકવણી)</span><b class="redText">₹${money(d.payout)}</b></div>
      <div class="stat"><span>આજનો ખર્ચ</span><b class="redText">₹${money(d.expense)}</b></div>
      <div class="stat"><span>ચોખ્ખો ફેરફાર</span><b class="${d.net_change >= 0 ? 'greenText' : 'redText'}">₹${money(d.net_change)}</b></div>
    `;

    $('dailyList').innerHTML = (d.transactions || []).map(x => `
      <div class="rowitem">
        <span>${esc(x.label)} · <small>(${x.kind} - ${x.mode === 'cash' ? 'રોકડ' : 'બેંક'})</small></span>
        <b class="${x.kind === 'જમા' ? 'greenText' : 'redText'}">₹${money(x.amount)}</b>
      </div>
    `).join('') || '<div class="hint">આ તારીખે કોઈ વ્યવહાર નથી.</div>';

    $('balances').innerHTML = `
      <div class="stat"><span>રોકડ બેલેન્સ (Cash)</span><b>₹${money(d.cash_balance)}</b></div>
      <div class="stat"><span>બેંક બેલેન્સ (Bank)</span><b>₹${money(d.bank_balance)}</b></div>
    `;
  } catch (err) {
    console.error(err);
  }
}

// ------------------- EXPENSES -------------------
async function saveE() {
  let name = $('eName').value.trim();
  let amt = +$('eAmount').value || 0;
  if (!name || amt <= 0) return toast('ખર્ચનું નામ અને રકમ આપો.', 'error');

  let res = await fetch('/api/expense/save/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({
      date: $('eDate').value,
      name: name,
      desc: $('eDesc').value.trim(),
      amount: amt,
      account: $('eAccount').value
    })
  });
  let d = await res.json();
  if (d.success) {
    toast('ખર્ચ સેવ થયો!');
    $('eName').value = '';
    $('eDesc').value = '';
    $('eAmount').value = '';
    setTimeout(() => window.location.reload(), 600);
  }
}

async function delE(id) {
  if (!confirm('આ ખર્ચ ડિલીટ કરવો છે?')) return;
  let res = await fetch(`/api/expense/delete/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('ખર્ચ ડિલીટ થયો.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// ------------------- SETTINGS & TRADER MASTER -------------------
async function saveSettings() {
  let payload = {
    firm: $('sFirm').value.trim(),
    bard: +$('sBard').value || 15,
    market: +$('sMarket').value || 3,
    comm: +$('sComm').value || 1.5,
    cash: +$('sCash').value || 0,
    bank: +$('sBank').value || 0,
    firmAddress: $('sFirmAddress').value.trim(),
    firmGST: $('sFirmGST').value.trim(),
    bankName: $('sBankName').value.trim(),
    bankAccount: $('sBankAccount').value.trim(),
    signName: $('sSignName').value.trim(),
    signGST: $('sSignGST').value.trim()
  };

  let res = await fetch('/api/settings/save/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify(payload)
  });
  let d = await res.json();
  if (d.success) {
    toast('સેટિંગ સેવ થયું!');
    setTimeout(() => window.location.reload(), 600);
  }
}

async function addTrader() {
  let name = $('newName').value.trim();
  if (!name) return toast('વેપારીનું નામ લખો.', 'error');

  let res = await fetch('/api/trader/add/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({ name: name })
  });
  let d = await res.json();
  if (d.success) {
    toast('વેપારી ઉમેરાયો!');
    $('newName').value = '';
    setTimeout(() => window.location.reload(), 600);
  }
}

async function delTrader(id) {
  if (!confirm('આ વેપારીને માસ્ટરમાંથી ડિલીટ કરવો છે?')) return;
  let res = await fetch(`/api/trader/delete/${id}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrftoken }
  });
  let d = await res.json();
  if (d.success) {
    toast('વેપારી ડિલીટ થયો.');
    setTimeout(() => window.location.reload(), 600);
  }
}

// Global Print helper
function openPrint(url) {
  window.open(url, '_blank', 'width=900,height=800');
}

// Initial setup
document.addEventListener('DOMContentLoaded', () => {
  const appLayout = document.querySelector('.app-layout');
  const collapseBtns = document.querySelectorAll('.sidebar-collapse-btn');

  // Default is open. Only collapse if user explicitly stored '1' on wide screens
  if (localStorage.getItem('sidebar_collapsed') === '1' && window.innerWidth > 1024) {
    if (appLayout) appLayout.classList.add('sidebar-collapsed');
    collapseBtns.forEach(btn => {
      btn.innerHTML = '›';
      btn.title = 'Sidebar ખોલો (Expand)';
    });
  } else {
    if (appLayout) appLayout.classList.remove('sidebar-collapsed');
    localStorage.setItem('sidebar_collapsed', '0');
    collapseBtns.forEach(btn => {
      btn.innerHTML = '‹';
      btn.title = 'Sidebar સંકોચો (Collapse)';
    });
  }

  if ($('fRows') && !$('fRows').children.length) {
    addFRow();
  }
  renderDaily();
  renderLedger();
  initTheme();
});

// ==========================================
// Dark Mode & Light Mode Theme Controller
// ==========================================

function initTheme() {
  const savedTheme = localStorage.getItem('app_theme') || 
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(savedTheme, false);
}

function applyTheme(theme, showToast = true) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('app_theme', theme);

  const isDark = theme === 'dark';
  const icon = isDark ? '☀️' : '🌙';
  const label = isDark ? 'Light' : 'Dark';
  const title = isDark ? 'લાઈટ મોડ પર સ્વિચ કરો (Switch to Light Mode)' : 'ડાર્ક મોડ પર સ્વિચ કરો (Switch to Dark Mode)';

  document.querySelectorAll('.theme-icon, #themeIcon').forEach(el => el.textContent = icon);
  document.querySelectorAll('.theme-label, #themeLabel').forEach(el => el.textContent = label);
  document.querySelectorAll('.theme-toggle-btn, #themeToggleBtn').forEach(el => el.title = title);
  if (sidebarThemeIcon) sidebarThemeIcon.textContent = icon;
  if (sidebarThemeBtn) sidebarThemeBtn.title = title;

  if (showToast && typeof toast === 'function') {
    toast(isDark ? '🌙 ડાર્ક મોડ સક્રિય કર્યો (Dark Mode)' : '☀️ લાઈટ મોડ સક્રિય કર્યો (Light Mode)', 'info');
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next, true);
}
