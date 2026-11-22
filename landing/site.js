/* ============================================================
 * Vietlott Auto Flow — landing logic
 * Chỉ sửa CONFIG khi có thông tin thật. Kết quả tự động lấy từ
 * draws.js (sinh bởi landing/sync_results.py).
 * ============================================================ */
const CONFIG = {
  brand: 'Vietlott Auto Flow',
  price: '999.000đ',
  fomoPrice: '999.000đ',
  jackpot: '42,89 tỷ',
  cutoffHour: 17,
  drawHour: 18,

  schedule: {
    '645': { name: 'Mega 6/45', days: [0, 3, 5], label: 'Thứ 4 · Thứ 6 · Chủ nhật', code: '645' },
    '655': { name: 'Power 6/55', days: [2, 4, 6], label: 'Thứ 3 · Thứ 5 · Thứ 7', code: '655' }
  },

  heroTicket: {
    '645': [3, 12, 18, 27, 33, 41],
    '655': [8, 15, 22, 31, 44, 52]
  },

  draws: {
    images: [],
    imageCaptions: [],
    latest: {
      game: '655',
      name: 'Power 6/55',
      id: '01426',
      date: '19/11/2026',
      numbers: [3, 13, 21, 23, 38, 43],
      special: 16,
      jackpot: 42887095500,
      jackpotText: '42,89 tỷ'
    },
    history: [
      { game: '645', name: 'Mega 6/45', id: '01590', date: '18/11/2026', numbers: [6, 18, 20, 27, 29, 32], special: null },
      { game: '655', name: 'Power 6/55', id: '01425', date: '17/11/2026', numbers: [6, 20, 36, 41, 49, 52], special: 34 },
      { game: '645', name: 'Mega 6/45', id: '01589', date: '15/11/2026', numbers: [6, 22, 24, 26, 40, 44], special: null },
      { game: '655', name: 'Power 6/55', id: '01424', date: '14/11/2026', numbers: [5, 28, 36, 42, 45, 47], special: 51 },
      { game: '645', name: 'Mega 6/45', id: '01588', date: '13/11/2026', numbers: [1, 7, 15, 19, 31, 33], special: null },
      { game: '655', name: 'Power 6/55', id: '01423', date: '12/11/2026', numbers: [17, 25, 33, 34, 35, 36], special: 48 }
    ]
  },

  supportZalo: 'https://zalo.me/0906919053',
  demoVideoUrl: '', // video MP4/WebM hoặc link YouTube; ảnh PNG/JPG cũng được
  zaloPrefill: {
    trial: 'Xin chào, tôi muốn dùng thử 7 ngày 0đ gói Vietlott Auto Flow. Tôi dùng: iPhone/Android. SĐT đăng ký Vietlott SMS của tôi là: ...',
    ios: 'Xin chào, tôi muốn nhận link Phím tắt iPhone và được cài hộ gói Vietlott Auto Flow. SĐT Vietlott SMS của tôi là: ...',
    android: 'Xin chào, tôi muốn nhận link cài đặt Android và được hỗ trợ bật tự động gửi SMS. SĐT Vietlott SMS của tôi là: ...'
  },
  contact: 'Liên hệ/Zalo dự phòng: https://zalo.me/0899963938',
  shortcutUrl: '',
  androidUrl: '',
  sepayQr: '',

  bank: {
    name: 'Vietcombank',
    account: '0721000544340',
    owner: 'Nguyễn Nhật Trường',
    branch: 'PGD Phú Thọ, TP.HCM',
    content: 'AUTOFLOW'
  },

  steps: [
    { t: 'Cài hộ qua Zalo (5 phút)', d: 'Bạn nhắn Zalo, chúng tôi kiểm tra điều kiện Vietlott SMS của bạn và cài đặt/bật tự động giúp trên chính điện thoại của bạn.' },
    { t: 'Bật tự động — máy tự gửi 9969', d: 'Đến kỳ quay, điện thoại tự gửi SMS đúng cú pháp (645/655) tới 9969 từ đúng số Vietlott SMS của bạn. Không cần bấm mỗi lần.' },
    { t: 'Bạn tạm dừng/bật lại anytime', d: 'Tắt tự động là ngừng gửi lệnh ngay. Bạn chủ động số lượng vé và có thể đổi cấu hình qua Zalo.' }
  ],

  benefits: [
    { icon: 'i-spark', t: 'AI tính toán bộ số tối ưu', d: 'Hệ thống AI phân tích và gợi ý bộ số theo thuật toán tối ưu của dự án, cá nhân hóa cho riêng bạn — tiết kiệm thời gian chọn số và giúp bạn yên tâm tham gia đều đặn.' },
    { icon: 'i-bolt', t: 'Tự động 24/7, không cần thao tác', d: 'Cài đặt một lần, sau đó điện thoại tự gửi SMS đúng lịch trên Android & iPhone mọi lúc — không cần bấm gửi, không cần nhớ từng kỳ quay.' },
    { icon: 'i-infinity', t: 'Vé không giới hạn, không bỏ lỡ kỳ', d: 'Đặt bao nhiêu vé tùy ý mỗi kỳ (miễn tài khoản Vietlott SMS đủ số dư/hạn mức). Tự động đúng lịch giúp bạn không quên, không lỡ cơ hội tham gia nào.' },
    { icon: 'i-pause', t: 'Bạn toàn quyền kiểm soát', d: 'Tạm dừng/bật tắt tự động bất cứ lúc nào (Phím tắt/ứng dụng/cài đặt hoặc nhờ hỗ trợ) để ngừng gửi lệnh và tránh phát sinh tiền vé ngoài ý muốn.' }
  ],

  priceList: [
    'Dùng thử 7 ngày 0đ — hỗ trợ cài hộ qua Zalo',
    'AI gợi ý bộ số riêng cho từng khách (hoặc bạn tự chọn)',
    'Tự động gửi SMS 24/7 trên Android & iPhone — cài một lần',
    'Không quên kỳ, không sai cú pháp; số vé tùy ý (tùy số dư)',
    '1 gói = 1 khách / 1 SĐT Vietlott SMS / 1 thiết bị',
    'Vận hành & cập nhật 36 tháng; đổi máy 150.000đ/lần'
  ],

  faq: [
    { q: 'Công cụ này là gì? Có bán vé số không?', a: 'Không. Đây là công cụ hỗ trợ soạn và gửi SMS tới 9969 từ chính số bạn đã đăng ký Vietlott SMS. Chúng tôi không bán vé, không mua hộ, không giữ tiền. Tiền vé (nếu gửi thành công) do Vietlott trừ từ tài khoản của bạn.' },
    { q: 'Tôi không rành công nghệ thì cài được không?', a: 'Có. Bạn chỉ cần nhắn Zalo — chúng tôi kiểm tra điều kiện và cài hộ trong khoảng 5 phút trên điện thoại của bạn. Sau đó máy tự chạy, bạn không cần thao tác hằng ngày.' },
    { q: 'Có đảm bảo trúng thưởng không?', a: 'Không. Xổ số là ngẫu nhiên. Lợi ích của công cụ là AI gợi ý bộ số, tự động gửi đúng lịch, không quên/không sai cú pháp — giúp bạn tham gia đều đặn theo lựa chọn của mình. Không cam kết trúng hay lợi nhuận.' },
    { q: 'Mỗi gói dùng mấy máy? Có chia sẻ được không?', a: 'Mỗi gói áp dụng cho 1 khách / 1 SĐT Vietlott SMS / 1 thiết bị đang hoạt động. Không dùng chung hay chuyển nhượng. Đổi máy: 150.000đ/lần, xác minh + mã GD, thu hồi máy cũ, có thời gian chờ giữa các lần.' },
    { q: 'Tôi cần chuẩn bị gì trước khi dùng?', a: 'Số điện thoại đã đăng ký Vietlott SMS, tài khoản/thẻ thanh toán mặc định, đủ số dư/hạn mức và gửi trong giờ nhận lệnh. Thiếu điều kiện thì Vietlott có thể không nhận lệnh.' },
    { q: 'Dùng thử 7 ngày 0đ và "trọn đời" nghĩa là sao?', a: 'Dùng thử 7 ngày miễn phí, chưa cần thanh toán. Gói Trọn đời 999.000đ thanh toán một lần, không phí định kỳ, kèm vận hành/cập nhật 36 tháng (giá có thể tăng; khách cũ giữ quyền lợi).' }
  ]
};


const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pad = (n) => String(n).padStart(2, '0');
const icon = (id, cls = '') => `<svg class="icon ${cls}" aria-hidden="true"><use href="#${id}"/></svg>`;

/* Kết quả thật do landing/sync_results.py sinh ra. */
function applyRemoteDraws() {
  const remote = window.VIETLOTT_DRAWS;
  if (!remote) return;
  if (remote.latest) CONFIG.draws.latest = remote.latest;
  if (Array.isArray(remote.history) && remote.history.length) CONFIG.draws.history = remote.history;
  if (remote.schedule) {
    for (const code of Object.keys(remote.schedule)) {
      CONFIG.schedule[code] = { ...(CONFIG.schedule[code] || {}), ...remote.schedule[code], code };
    }
  }
  if (remote.latest?.jackpotText) CONFIG.jackpot = remote.latest.jackpotText;
}

function weekdayVN(date) {
  return ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'][date.getDay()];
}

function sameDate(a, b) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function nextDrawInfo(now = new Date()) {
  let best = null;
  for (const code of Object.keys(CONFIG.schedule)) {
    const game = CONFIG.schedule[code];
    if (!game?.days?.length) continue;
    for (let i = 0; i < 15; i += 1) {
      const date = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i, CONFIG.cutoffHour, 0, 0, 0);
      if (date <= now) continue;
      if (game.days.includes(date.getDay())) {
        if (!best || date < best.date) best = { code, game, date };
        break;
      }
    }
  }
  return best;
}

function render() {
  const setText = (sel, val) => { const el = $(sel); if (el) el.textContent = val; };
  setText('#price', CONFIG.price);
  setText('#fomo-price', CONFIG.fomoPrice);
  setText('#jackpot', CONFIG.jackpot);
  setText('#year', String(new Date().getFullYear()));

  const latest = CONFIG.draws.latest;
  setText('#jackpot-label', `Jackpot ${latest?.name || CONFIG.schedule['655'].name}`);
  setText('#result-jackpot-label', latest?.game === '645' ? 'Jackpot' : 'Jackpot 1');

  const zalo = CONFIG.supportZalo || 'https://zalo.me/';
  const zaloUrl = (text) => {
    if (!text) return zalo;
    return zalo.includes('?') ? `${zalo}&text=${encodeURIComponent(text)}` : `${zalo}?text=${encodeURIComponent(text)}`;
  };
  const trialLink = zaloUrl(CONFIG.zaloPrefill?.trial || '');
  ['#support-link', '#support-link-2', '#support-link-3', '#mobile-zalo', '#zalo-contact'].forEach((sel) => {
    const a = $(sel);
    if (a && !a.dataset.dynamic) a.href = trialLink;
  });
  $$('.js-zalo').forEach((a) => { a.href = trialLink; });

  // Slot video/ảnh hướng dẫn cài hộ: chỉ hiện khi có nội dung thật
  const media = $('#install-media');
  if (media) {
    const url = (CONFIG.demoVideoUrl || '').trim();
    const body = $('#install-media-body');
    if (url && body) {
      const low = url.toLowerCase();
      if (/\.(png|jpe?g|webp|gif)$/.test(low)) {
        body.innerHTML = `<img src="${esc(url)}" alt="Hướng dẫn cài hộ" loading="lazy">`;
      } else if (/youtube\.com|youtu\.be/.test(low)) {
        body.innerHTML = `<div class="video-wrap"><iframe src="${esc(url)}" title="Video hướng dẫn cài hộ" allowfullscreen loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe></div>`;
      } else {
        body.innerHTML = `<video src="${esc(url)}" controls preload="none" playsinline></video>`;
      }
      media.hidden = false;
    } else {
      media.hidden = true;
    }
  }

  // Ẩn khối thanh toán khi vẫn là placeholder (không public số TK giả)
  const payPanel = $('#payment-panel');
  if (payPanel && /sẽ cập nhật/i.test(CONFIG.bank.name || '') && !CONFIG.sepayQr) payPanel.hidden = true;

  const contact = $('#contact-line');
  if (contact) {
    if (CONFIG.contact) contact.textContent = CONFIG.contact;
    else contact.hidden = true;
  }

  const qr = $('#qr-wrap');
  if (qr) {
    qr.innerHTML = CONFIG.sepayQr
      ? `<img src="${esc(CONFIG.sepayQr)}" alt="QR thanh toán SePay">`
      : `<div class="qr-empty">${icon('i-qr')}<strong>Chuyển khoản theo thông tin bên dưới</strong><span>Mã QR sẽ được cập nhật khi có; hiện vui lòng chuyển khoản trực tiếp.</span></div>`;
  }

  const bank = $('#bank-box');
  if (bank) {
    const rows = [
      ['Ngân hàng', CONFIG.bank.name],
      ['Chi nhánh', CONFIG.bank.branch || ''],
      ['Số tài khoản', CONFIG.bank.account],
      ['Chủ tài khoản', CONFIG.bank.owner],
      ['Nội dung', `${CONFIG.bank.content} SĐT`]
    ];
    bank.innerHTML = rows.map(([k, v]) => `<div class="bank-row"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join('');
  }

  const setLink = (sel, url, fallback) => {
    const a = $(sel);
    if (!a) return;
    a.href = url || zalo;
    a.textContent = url ? 'Mở link cá nhân' : fallback;
    a.dataset.dynamic = '1';
  };
  if (CONFIG.shortcutUrl) {
    setLink('#shortcut-link', CONFIG.shortcutUrl, 'Nhận link iPhone trên Zalo');
  } else {
    const a = $('#shortcut-link');
    if (a) { a.href = zaloUrl(CONFIG.zaloPrefill?.ios || ''); a.dataset.dynamic = '1'; }
  }
  if (CONFIG.androidUrl) {
    setLink('#android-link', CONFIG.androidUrl, 'Nhận link Android trên Zalo');
  } else {
    const a = $('#android-link');
    if (a) { a.href = zaloUrl(CONFIG.zaloPrefill?.android || ''); a.dataset.dynamic = '1'; }
  }

  const steps = $('#steps');
  if (steps) {
    steps.innerHTML = CONFIG.steps.map((s, i) => `
      <article class="step-card reveal ${i ? `delay-${Math.min(i, 2)}` : ''}">
        <div class="step-num">${i + 1}</div>
        <h3>${esc(s.t)}</h3>
        <p>${esc(s.d)}</p>
      </article>`).join('');
  }

  const benefits = $('#benefits');
  if (benefits) {
    benefits.innerHTML = CONFIG.benefits.map((b, i) => `
      <article class="benefit-card reveal ${i % 2 ? 'delay-1' : ''}">
        <div class="benefit-icon">${icon(b.icon)}</div>
        <div><h3>${esc(b.t)}</h3><p>${esc(b.d)}</p></div>
      </article>`).join('');
  }

  const priceList = $('#price-list');
  if (priceList) {
    priceList.innerHTML = CONFIG.priceList.map((t) => `<div class="price-feat">${icon('i-check')}<span>${esc(t)}</span></div>`).join('');
  }

  const faq = $('#faq-list');
  if (faq) {
    faq.innerHTML = CONFIG.faq.map((f) => `
      <details class="reveal"${f === CONFIG.faq[0] ? ' open' : ''}>
        <summary>${esc(f.q)}</summary>
        <p>${esc(f.a)}</p>
      </details>`).join('');
  }

  renderHero();
  renderTicker();
  renderDraws();
}

function renderHero() {
  const next = nextDrawInfo();
  const game = next?.game || CONFIG.schedule['655'];
  const isToday = next ? sameDate(next.date, new Date()) : false;
  const title = `${game.name.toUpperCase()} · ${isToday ? 'KỲ HÔM NAY' : 'KỲ TIẾP THEO'}`;
  const numbers = CONFIG.heroTicket[game.code] || CONFIG.heroTicket['655'];

  const titleEl = $('#ticket-game');
  if (titleEl) titleEl.textContent = title;
  const heroBalls = $('#hero-balls');
  if (heroBalls) heroBalls.innerHTML = numbers.map((n) => `<span class="ball">${pad(n)}</span>`).join('');
  const cmd = $('#ticket-cmd');
  if (cmd) cmd.textContent = `${game.code} K1 S ${numbers.map(pad).join(' ')}`;
}

function renderTicker() {
  const track = $('#ticker-track');
  if (!track) return;
  const latest = CONFIG.draws?.latest;
  const nums = latest
    ? latest.numbers.map(pad).join(' ') + (latest.special != null ? ' · ' + pad(latest.special) : '')
    : '';
  const items = [
    'AI tính toán & gợi ý bộ số tối ưu — tự động gửi SMS tới 9969, không bán vé',
    `Jackpot ${latest?.name || 'Power 6/55'} (công khai): ${CONFIG.jackpot} — đừng bỏ lỡ kỳ quay tới`,
    nums ? `Kết quả ${latest.name} kỳ ${latest.id} (tham khảo): ${nums}` : null,
    'Tự động 24/7, không cần thao tác — không quên, không sai cú pháp',
    'Số lượng vé không giới hạn (tùy số dư Vietlott SMS) — bạn toàn quyền tạm dừng',
    'Giá Founder 999.000đ trọn đời — có thể tăng bất cứ lúc nào · Dùng thử 7 ngày 0đ'
  ].filter(Boolean);
  const row = items.map((t) => `<span class="ticker-item">${esc(t)}</span><span class="ticker-sep" aria-hidden="true"></span>`).join('');
  track.innerHTML = row + row;
}

function renderDraws() {
  const d = CONFIG.draws || {};
  const latest = d.latest || { name: '', id: '', date: '', numbers: [], special: null, game: '655' };
  const setText = (sel, val) => { const el = $(sel); if (el) el.textContent = val; };

  setText('#draw-name', latest.name);
  setText('#draw-id', latest.id);
  setText('#draw-date', latest.date);
  setText('#result-jackpot', latest.jackpotText || CONFIG.jackpot);

  const logo = $('#draw-logo');
  if (logo) {
    logo.src = latest.game === '645' ? 'assets/mega645.png' : 'assets/power655.png';
    logo.alt = latest.name;
  }

  const drawBalls = $('#draw-balls');
  if (drawBalls) {
    drawBalls.innerHTML = (latest.numbers || []).map((n) => `<span class="ball">${pad(n)}</span>`).join('');
  }

  const special = $('#draw-special');
  const specialRow = $('#special-row');
  if (latest.special != null) {
    if (special) special.textContent = pad(latest.special);
    if (specialRow) specialRow.hidden = false;
  } else if (specialRow) {
    specialRow.hidden = true;
  }

  const winnersData = (window.VIETLOTT_WINNERS && Array.isArray(window.VIETLOTT_WINNERS.items))
    ? window.VIETLOTT_WINNERS.items
    : [];
  let images = Array.isArray(d.images) ? d.images.filter(Boolean) : [];
  let captions = Array.isArray(d.imageCaptions) ? d.imageCaptions.slice() : [];
  if (!images.length && winnersData.length) {
    const mega = winnersData.filter((w) => w.game === 'Mega 6/45').slice(0, 3);
    const power = winnersData.filter((w) => w.game === 'Power 6/55').slice(0, 3);
    const pick = [...mega, ...power].slice(0, 6);
    images = pick.map((w) => w.url);
    captions = pick.map((w) => `${w.game} · ${w.name} trúng ${w.amount} ${w.currency || 'VNĐ'} — ảnh: Vietlott (Chủ nhân Jackpot)`);
  }

  const gallery = $('#result-gallery');
  const winnersHead = $('#winners-head');
  if (gallery) {
    if (images.length) {
      gallery.hidden = false;
      if (winnersHead) winnersHead.hidden = false;
      gallery.innerHTML = images.map((src, i) => {
        const caption = captions[i] || 'Khoảnh khắc trúng thưởng — ảnh: Vietlott';
        return `<figure><img src="${esc(src)}" alt="${esc(caption)}" loading="lazy" decoding="async"><figcaption>${esc(caption)}</figcaption></figure>`;
      }).join('');
    } else {
      gallery.hidden = true;
      if (winnersHead) winnersHead.hidden = true;
      gallery.innerHTML = '';
    }
  }

  const hist = $('#result-history');
  if (hist) {
    hist.innerHTML = (d.history || []).map((h) => `
      <div class="history-row">
        <div class="history-game">
          <span class="game-tag">${esc(h.name)}</span>
          <span class="history-date">${esc(h.date)}</span>
        </div>
        <div class="history-meta">Kỳ <strong>${esc(h.id)}</strong></div>
        <div class="mini-balls">
          ${(h.numbers || []).map((n) => `<span class="ball">${pad(n)}</span>`).join('')}
          ${h.special != null ? `<span class="ball ball--special">${pad(h.special)}</span>` : ''}
        </div>
      </div>`).join('');
  }
}

function bindCountdown() {
  const el = $('#countdown');
  if (!el) return;

  const tick = () => {
    const now = new Date();
    const info = nextDrawInfo(now);
    if (!info) {
      el.textContent = '--:--:--';
      return;
    }

    const isToday = sameDate(info.date, now);
    const label = $('#countdown-label');
    if (label) label.textContent = `${info.game.name} · ${isToday ? 'hôm nay' : weekdayVN(info.date)}`;

    const note = $('#countdown-note');
    if (note) {
      note.textContent = isToday
        ? `Chốt lệnh hôm nay lúc ${pad(CONFIG.cutoffHour)}:00`
        : `Chốt lệnh ${weekdayVN(info.date)} ${pad(info.date.getDate())}/${pad(info.date.getMonth() + 1)} lúc ${pad(CONFIG.cutoffHour)}:00`;
    }

    const ms = Math.max(0, info.date - now);
    const h = Math.floor(ms / 3600000);
    const m = Math.floor((ms % 3600000) / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    el.textContent = [h, m, s].map((n) => String(n).padStart(2, '0')).join(':');
  };

  tick();
  setInterval(tick, 1000);
}

function bindTabs() {
  const tabs = $$('.tab-btn');
  if (!tabs.length) return;

  const activate = (id) => {
    tabs.forEach((tab) => {
      const on = tab.id === id;
      tab.classList.toggle('is-active', on);
      tab.setAttribute('aria-selected', String(on));
      tab.tabIndex = on ? 0 : -1;
    });
    $$('.tab-panel').forEach((panel) => {
      const on = panel.id === id.replace('tab-', 'panel-');
      panel.hidden = !on;
      panel.classList.toggle('is-active', on);
    });
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => activate(tab.id));
    tab.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      const dir = e.key === 'ArrowRight' ? 1 : -1;
      const next = tabs[(index + dir + tabs.length) % tabs.length];
      next.focus();
      activate(next.id);
    });
  });
}

function bindFontToggle() {
  const btn = $('#font-toggle');
  if (!btn) return;

  const apply = (on) => {
    document.documentElement.classList.toggle('big-text', on);
    btn.setAttribute('aria-pressed', String(on));
    btn.innerHTML = on
      ? '<span class="ft-icon">A−</span><span class="ft-text">Chữ vừa</span>'
      : '<span class="ft-icon">A+</span><span class="ft-text">Chữ to</span>';
  };

  let saved = false;
  try { saved = localStorage.getItem('avf-big-text') === '1'; } catch (e) {}
  apply(saved);

  btn.addEventListener('click', () => {
    const on = btn.getAttribute('aria-pressed') !== 'true';
    apply(on);
    try { localStorage.setItem('avf-big-text', on ? '1' : '0'); } catch (e) {}
  });
}

function bindForm() {
  const form = $('#buy-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = ($('#f-name')?.value || '').trim();
    const phone = ($('#f-phone')?.value || '').trim();
    const msg = $('#form-msg');
    if (!name || !/^0\d{9}$/.test(phone)) {
      if (msg) msg.textContent = 'Vui lòng nhập họ tên và số điện thoại 10 số, bắt đầu bằng số 0.';
      return;
    }
    if (msg) msg.textContent = '';
    const code = `${CONFIG.bank.content} ${phone}`;
    const rc = $('#result-content');
    if (rc) rc.textContent = code;
    const res = $('#result');
    if (res) {
      res.hidden = false;
      res.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  const copyBtn = $('#copy-content');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const text = $('#result-content')?.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        copyBtn.textContent = 'Đã copy';
      } catch (e) {
        copyBtn.textContent = 'Hãy tự copy';
      }
      setTimeout(() => {
        copyBtn.innerHTML = `${icon('i-copy')} Copy`;
      }, 2200);
    });
  }

  const zaloBtn = $('#zalo-contact');
  if (zaloBtn) {
    zaloBtn.addEventListener('click', (e) => {
      const name = ($('#f-name')?.value || '').trim();
      const phone = ($('#f-phone')?.value || '').trim();
      const code = $('#result-content')?.textContent || `${CONFIG.bank.content} ${phone}`;
      const text = `Xin chào, tôi ${name} (SĐT ${phone}) muốn kích hoạt gói ${CONFIG.price}. Nội dung chuyển khoản: ${code}`;
      const base = CONFIG.supportZalo || 'https://zalo.me/';
      zaloBtn.href = base.includes('?') ? `${base}&text=${encodeURIComponent(text)}` : `${base}?text=${encodeURIComponent(text)}`;
      window.open(zaloBtn.href, '_blank', 'noopener');
      e.preventDefault();
    });
  }
}

function bindReveal() {
  const els = $$('.reveal');
  if (!els.length) return;
  if (!('IntersectionObserver' in window)) {
    els.forEach((el) => el.classList.add('visible'));
    return;
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
  els.forEach((el) => io.observe(el));
}

function bindHeader() {
  const header = $('#site-header');
  if (!header) return;
  const update = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
  update();
  window.addEventListener('scroll', update, { passive: true });
}

document.addEventListener('DOMContentLoaded', () => {
  applyRemoteDraws();
  render();
  bindCountdown();
  bindTabs();
  bindFontToggle();
  bindForm();
  bindReveal();
  bindHeader();
});
