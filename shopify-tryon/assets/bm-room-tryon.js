/* Black Mango — Room try-on
   Custom element <bm-room-tryon>. Reads its product list from a JSON <script data-products> child.
   The customer's room photo is read in the browser and never uploaded. */
(() => {
  if (customElements.get('bm-room-tryon')) return;

  // Where each kind of piece sits, as fractions of the room picture.
  const PLACE = {
    floor: { w: 0.30, x: 0.50, y: 0.78, where: 'floor' },
    sofa:  { w: 0.09, x: 0.46, y: 0.52, where: 'sofa' },
    stand: { w: 0.09, x: 0.84, y: 0.86, where: 'floor' },
    table: { w: 0.028, x: 0.175, y: 0.626, where: 'table top' }
  };
  const SQUASH = 0.45;           // how flat a rug looks lying on the floor
  const GROUPS = { floor: 'Rugs', sofa: 'Cushions', stand: 'Objects', table: 'Glassware' };
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const depth = (y) => 0.55 + y * 0.6;  // things further down the picture are closer, so bigger

  function drawSampleRoom(ctx, W, H) {
    const r = (x, y, w, h, c, rad) => { ctx.fillStyle = c; ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x * W, y * H, w * W, h * H, rad ? rad * W : 0) : ctx.rect(x * W, y * H, w * W, h * H); ctx.fill(); };
    r(0, 0, 1, 0.57, '#3B342E'); r(0, 0.57, 1, 0.016, '#26201B'); r(0, 0.586, 1, 0.414, '#8C7764');
    r(0.09, 0.12, 0.18, 0.32, '#26201B'); r(0.098, 0.134, 0.164, 0.292, '#5C534A'); r(0.177, 0.12, 0.006, 0.32, '#26201B');
    r(0.31, 0.33, 0.45, 0.23, '#161412', 0.02); r(0.28, 0.42, 0.51, 0.15, '#201C18', 0.014);
    r(0.84, 0.40, 0.06, 0.19, '#4F5A3A', 0.02);
    r(0.10, 0.625, 0.15, 0.022, '#1A1714', 0.004); r(0.166, 0.645, 0.018, 0.17, '#1A1714');
  }

  class BMRoomTryOn extends HTMLElement {
    connectedCallback() {
      if (this._ready) return; this._ready = true;
      const data = this.querySelector('script[data-products]');
      try { this.items = JSON.parse(data.textContent).filter((i) => i && i.image); } catch (e) { this.items = []; }
      if (!this.items.length) return;
      this.items.forEach((i) => { if (!PLACE[i.placement]) i.placement = 'stand'; });
      this.modal = this.dataset.layout === 'modal';
      this.startId = Number(this.dataset.product) || this.items[0].id;
      this.t = { cartLabel: this.dataset.cartLabel || 'Add to cart', title: this.dataset.title || 'See it in your room' };
      if (this.modal) {
        this.dialog = this.querySelector('dialog');
        this.querySelectorAll('[data-bmto-open]').forEach((b) => b.addEventListener('click', () => this.open()));
      } else {
        this.build(this.querySelector('[data-bmto-mount]') || this);
      }
    }

    open() {
      if (!this.built) this.build(this.dialog.querySelector('[data-bmto-mount]'));
      this.dialog.showModal(); document.documentElement.classList.add('bmto-lock');
      this.dialog.addEventListener('close', () => document.documentElement.classList.remove('bmto-lock'), { once: true });
      requestAnimationFrame(() => this.drawBg());
    }

    build(mount) {
      this.built = true;
      const groups = [...new Set(this.items.map((i) => i.placement))];
      mount.innerHTML = `
        <div class="bmto">
          <div class="bmto-stage-wrap">
            <div class="bmto-stage" tabindex="0" role="application" aria-label="Room preview. Tap to place the piece, drag to move it. Arrow keys move, plus and minus resize.">
              <canvas class="bmto-bg" aria-hidden="true"></canvas>
              <img class="bmto-item" alt="" draggable="false">
              <span class="bmto-hint"></span>
            </div>
            <p class="bmto-note">A visual guide. Check the product dimensions before ordering.</p>
          </div>
          <div class="bmto-panel">
            <div class="bmto-step">
              <span class="bmto-label">1. Your room</span>
              <div class="bmto-row">
                <label class="bmto-btn bmto-btn--solid">Upload a photo<input type="file" accept="image/*" class="bmto-file"></label>
                <button type="button" class="bmto-btn" data-sample>Use sample room</button>
              </div>
              <span class="bmto-small">Your photo stays on your device.</span>
            </div>
            <div class="bmto-step">
              <span class="bmto-label">2. Choose a piece</span>
              ${groups.length > 1 ? `<div class="bmto-tabs" role="group" aria-label="Category">${groups.map((g) => `<button type="button" class="bmto-chip" data-group="${g}">${GROUPS[g]}</button>`).join('')}</div>` : ''}
              <div class="bmto-thumbs" role="group" aria-label="Products"></div>
            </div>
            <div class="bmto-step">
              <span class="bmto-label">3. Adjust</span>
              <label class="bmto-range">Size <input type="range" min="40" max="220" step="5" value="100" data-scale></label>
              <label class="bmto-range" data-rot-wrap>Rotate <input type="range" min="0" max="180" step="5" value="90" data-rot></label>
              <button type="button" class="bmto-chip" data-flip hidden>Flip left / right</button>
            </div>
            <div class="bmto-buy">
              <div class="bmto-buy-info"><a class="bmto-name" href="#"></a><span class="bmto-price"></span></div>
              <button type="button" class="bmto-btn bmto-btn--solid" data-add></button>
              <button type="button" class="bmto-btn" data-save>Save or share this view</button>
              <span class="bmto-small" data-status role="status" aria-live="polite"></span>
            </div>
          </div>
        </div>`;
      const $ = (s) => mount.querySelector(s);
      this.el = { stage: $('.bmto-stage'), bg: $('.bmto-bg'), item: $('.bmto-item'), hint: $('.bmto-hint'), thumbs: $('.bmto-thumbs'),
        scale: $('[data-scale]'), rot: $('[data-rot]'), rotWrap: $('[data-rot-wrap]'), flip: $('[data-flip]'), name: $('.bmto-name'),
        price: $('.bmto-price'), add: $('[data-add]'), status: $('[data-status]'), mount };
      this.s = { room: null, x: 0.5, y: 0.78, scale: 1, rot: 90, flip: false, item: null };

      $('.bmto-file').addEventListener('change', (e) => this.loadRoom(e.target.files[0]));
      $('[data-sample]').addEventListener('click', () => { this.s.room = null; this.setAspect(4 / 3); this.reset(); });
      mount.querySelectorAll('[data-group]').forEach((b) => b.addEventListener('click', () => this.showGroup(b.dataset.group, true)));
      this.el.scale.addEventListener('input', () => { this.s.scale = this.el.scale.value / 100; this.layout(); });
      this.el.rot.addEventListener('input', () => { this.s.rot = Number(this.el.rot.value); this.layout(); });
      this.el.flip.addEventListener('click', () => { this.s.flip = !this.s.flip; this.layout(); });
      this.el.add.addEventListener('click', () => this.addToCart());
      $('[data-save]').addEventListener('click', () => this.save());
      this.bindStage();
      new ResizeObserver(() => this.drawBg()).observe(this.el.stage);

      this.setAspect(4 / 3);
      const start = this.items.find((i) => i.id === this.startId) || this.items[0];
      this.showGroup(start.placement, false);
      this.select(start);
    }

    showGroup(g, pickFirst) {
      this.el.mount.querySelectorAll('[data-group]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.group === g));
      const list = this.items.filter((i) => i.placement === g);
      this.el.thumbs.innerHTML = list.map((i) => `<button type="button" class="bmto-thumb" data-id="${i.id}" aria-label="${esc(i.title)}"><img src="${esc(i.thumb || i.image)}" alt="" loading="lazy"></button>`).join('');
      this.el.thumbs.querySelectorAll('[data-id]').forEach((b) => {
        const it = this.items.find((i) => i.id === Number(b.dataset.id)), im = b.querySelector('img');
        im.onerror = () => { if (it.fallback && im.src !== it.fallback) im.src = it.fallback; };
        b.addEventListener('click', () => this.select(it));
      });
      if (pickFirst) this.select(list.find((i) => i.available) || list[0]);
      else this.markThumbs();
    }

    select(item) {
      const moved = !this.s.item || this.s.item.placement !== item.placement;
      this.s.item = item;
      if (moved) { const p = PLACE[item.placement]; this.s.x = p.x; this.s.y = p.y; }
      const img = this.el.item;
      img.onerror = () => { if (item.fallback && img.src !== item.fallback) { img.src = item.fallback; item.image = item.fallback; } };
      img.onload = () => { this.ar = img.naturalWidth / img.naturalHeight || 1; this.layout(); };
      img.crossOrigin = 'anonymous';   // lets "Save this view" draw the product onto the picture
      img.src = item.image; img.alt = item.title + ' placed in the room';
      this.el.name.textContent = item.title; this.el.name.href = item.url || '#';
      this.el.price.textContent = item.available ? item.price : 'Sold out';
      this.el.add.textContent = item.available ? this.t.cartLabel : 'Sold out';
      this.el.add.disabled = !item.available;
      const floor = item.placement === 'floor';
      this.el.rotWrap.hidden = !floor; this.el.flip.hidden = floor;
      this.el.status.textContent = '';
      this.markThumbs(); this.layout();
    }

    markThumbs() { this.el.thumbs.querySelectorAll('[data-id]').forEach((b) => b.setAttribute('aria-pressed', Number(b.dataset.id) === this.s.item?.id)); }

    reset() { const p = PLACE[this.s.item.placement]; this.s.x = p.x; this.s.y = p.y; this.drawBg(); this.layout(); }

    setAspect(ar) { this.roomAr = Math.min(16 / 9, Math.max(3 / 4, ar)); this.el.stage.style.aspectRatio = String(this.roomAr); }

    loadRoom(file) {
      if (!file) return;
      const url = URL.createObjectURL(file), img = new Image();
      img.onload = () => { if (this.s.room) URL.revokeObjectURL(this.s.room.src); this.s.room = img; this.setAspect(img.naturalWidth / img.naturalHeight); this.reset(); };
      img.onerror = () => { this.el.status.textContent = 'That file could not be opened. Try a JPG or PNG photo.'; };
      img.src = url;
    }

    drawBg() {
      const c = this.el?.bg; if (!c) return;
      const r = this.el.stage.getBoundingClientRect(); if (!r.width) return;
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      c.width = Math.round(r.width * dpr); c.height = Math.round(r.height * dpr);
      const ctx = c.getContext('2d');
      this.paintRoom(ctx, c.width, c.height);
    }

    paintRoom(ctx, W, H) {
      if (this.s.room) {
        const im = this.s.room, s = Math.max(W / im.naturalWidth, H / im.naturalHeight);
        const w = im.naturalWidth * s, h = im.naturalHeight * s;
        ctx.drawImage(im, (W - w) / 2, (H - h) / 2, w, h);
      } else drawSampleRoom(ctx, W, H);
    }

    widthFrac() { return PLACE[this.s.item.placement].w * this.s.scale * depth(this.s.y); }

    layout() {
      const it = this.s.item; if (!it || !this.el) return;
      const floor = it.placement === 'floor', el = this.el.item;
      el.style.left = this.s.x * 100 + '%'; el.style.top = this.s.y * 100 + '%';
      el.style.width = this.widthFrac() * 100 + '%';
      el.style.transform = floor ? `translate(-50%,-50%) scale(1,${SQUASH}) rotate(${this.s.rot}deg)` : `translate(-50%,-100%) scaleX(${this.s.flip ? -1 : 1})`;
      el.classList.toggle('is-floor', floor);
      this.el.hint.textContent = `${this.s.room ? 'Your room' : 'Sample room'} · tap the ${PLACE[it.placement].where} to place, drag to move`;
    }

    bindStage() {
      const st = this.el.stage, pts = new Map();
      let pinch0 = 0, scale0 = 1, grab = null;
      const frac = (e) => { const r = st.getBoundingClientRect(); return { x: Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)), y: Math.min(1, Math.max(0, (e.clientY - r.top) / r.height)) }; };
      st.addEventListener('pointerdown', (e) => {
        st.setPointerCapture(e.pointerId); pts.set(e.pointerId, e);
        if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch0 = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY); scale0 = this.s.scale; grab = null; return; }
        const f = frac(e);
        grab = e.target === this.el.item ? { dx: this.s.x - f.x, dy: this.s.y - f.y } : { dx: 0, dy: 0 };
        if (e.target !== this.el.item) { this.s.x = f.x; this.s.y = f.y; this.layout(); }
      });
      st.addEventListener('pointermove', (e) => {
        if (!pts.has(e.pointerId)) return; pts.set(e.pointerId, e);
        if (pts.size === 2 && pinch0) {
          const [a, b] = [...pts.values()]; const d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
          this.s.scale = Math.min(2.2, Math.max(0.4, scale0 * d / pinch0)); this.el.scale.value = Math.round(this.s.scale * 100); this.layout(); return;
        }
        if (grab) { const f = frac(e); this.s.x = Math.min(1, Math.max(0, f.x + grab.dx)); this.s.y = Math.min(1, Math.max(0, f.y + grab.dy)); this.layout(); }
      });
      const up = (e) => { pts.delete(e.pointerId); if (pts.size < 2) pinch0 = 0; if (!pts.size) grab = null; };
      st.addEventListener('pointerup', up); st.addEventListener('pointercancel', up);
      st.addEventListener('keydown', (e) => {
        const k = { ArrowLeft: [-0.02, 0], ArrowRight: [0.02, 0], ArrowUp: [0, -0.02], ArrowDown: [0, 0.02] }[e.key];
        if (k) { this.s.x = Math.min(1, Math.max(0, this.s.x + k[0])); this.s.y = Math.min(1, Math.max(0, this.s.y + k[1])); }
        else if (e.key === '+' || e.key === '=') this.s.scale = Math.min(2.2, this.s.scale + 0.05);
        else if (e.key === '-') this.s.scale = Math.max(0.4, this.s.scale - 0.05);
        else return;
        e.preventDefault(); this.el.scale.value = Math.round(this.s.scale * 100); this.layout();
      });
    }

    async addToCart() {
      const it = this.s.item, btn = this.el.add; if (!it.available || !it.variant) return;
      btn.disabled = true; this.el.status.textContent = 'Adding…';
      const root = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || '/';
      try {
        if (this.dataset.demo) { await new Promise((r) => setTimeout(r, 400)); }
        else {
          const res = await fetch(root + 'cart/add.js', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ items: [{ id: it.variant, quantity: 1 }] }) });
          if (!res.ok) throw new Error((await res.json()).description || 'Could not add to cart');
          document.dispatchEvent(new CustomEvent('cart:refresh', { bubbles: true }));
        }
        this.el.status.innerHTML = `Added. <a href="${root}cart">View cart</a>`;
      } catch (e) { this.el.status.textContent = e.message || 'Could not add to cart. Please try again.'; }
      btn.disabled = false;
    }

    async save() {
      const it = this.s.item, im = this.el.item; if (!im.complete) return;
      const W = this.s.room ? Math.min(2000, this.s.room.naturalWidth) : 1600, H = Math.round(W / this.roomAr);
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      const ctx = c.getContext('2d'); this.paintRoom(ctx, W, H);
      const w = this.widthFrac() * W, h = w / (this.ar || 1), x = this.s.x * W, y = this.s.y * H;
      ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.38)';
      try {
        if (it.placement === 'floor') { ctx.shadowBlur = 18; ctx.shadowOffsetY = 14; ctx.translate(x, y); ctx.scale(1, SQUASH); ctx.rotate(this.s.rot * Math.PI / 180); ctx.drawImage(im, -w / 2, -h / 2, w, h); }
        else { ctx.shadowBlur = 8; ctx.shadowOffsetX = 8; ctx.shadowOffsetY = 6; ctx.translate(x, y - h / 2); ctx.scale(this.s.flip ? -1 : 1, 1); ctx.drawImage(im, -w / 2, -h / 2, w, h); }
      } catch (e) {}
      ctx.restore();
      let blob;
      try { blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', 0.9)); } catch (e) { blob = null; }
      if (!blob) { this.el.status.textContent = 'Saving is not available for this image.'; return; }
      const file = new File([blob], 'black-mango-' + (it.handle || 'room') + '.jpg', { type: 'image/jpeg' });
      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try { await navigator.share({ files: [file], title: it.title, text: it.title + ' in my room' }); return; } catch (e) { if (e.name === 'AbortError') return; }
      }
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = file.name; document.body.appendChild(a); a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    }
  }
  customElements.define('bm-room-tryon', BMRoomTryOn);
  // A button anywhere on the page with data-bmto-trigger opens the product-page try-on.
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-bmto-trigger]'); if (!t) return;
    const el = document.querySelector('bm-room-tryon[data-layout="modal"]');
    if (el && el.open) { e.preventDefault(); el.open(); }
  });
})();
