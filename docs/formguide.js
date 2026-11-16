/* The Sporting Almanac — Form Guide
   Loads results from the form guide database on Cloudflare and fills each page.
   Pages: form-guide.html, meeting.html, race.html, horse.html, comparison.html, blackbook.html */
(function () {
  "use strict";
  const API = window.FG_API || "https://formguide.thesportingalmanac.workers.dev";
  const SPELL_DAYS = 84;                        // 12 weeks between runs = a spell (first-up next time)

  // ------------------------------------------------------------ small helpers
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const qs = (k) => new URLSearchParams(location.search).get(k) || "";
  const DAY = 86400000;
  const toDate = (iso) => new Date(iso + "T12:00:00");
  const days = (a, b) => Math.round((toDate(b) - toDate(a)) / DAY);
  const todayISO = () => new Date(Date.now() + 10 * 3600000).toISOString().slice(0, 10);
  const fmtDate = (iso, long) => !iso ? "" : toDate(iso).toLocaleDateString("en-AU",
    long ? { weekday: "long", day: "numeric", month: "long", year: "numeric" } : { day: "2-digit", month: "short", year: "2-digit" });
  const num = (v) => { const n = parseFloat(String(v ?? "").replace(/[^0-9.\-]/g, "")); return isNaN(n) ? null : n; };
  const money = (v) => { const n = num(v); return n ? "$" + Math.round(n).toLocaleString("en-AU") : "—"; };
  const dash = (v) => (v === null || v === undefined || v === "" ? "—" : v);

  // some names arrive with HTML codes in them ("&amp;", "&#8217;"): turn them back into characters
  const unent = (v) => typeof v !== "string" || v.indexOf("&") < 0 ? v : v.replace(/&#(\d+);/g, (m, n) => String.fromCharCode(Number(n)))
    .replace(/&#x([0-9a-f]+);/gi, (m, n) => String.fromCharCode(parseInt(n, 16))).replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  async function get(path) {
    const r = await fetch(API + path);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || "HTTP " + r.status);
    return JSON.parse(await r.text(), (k, v) => unent(v));
  }

  // ------------------------------------------------------------ tracks, horses, races
  const TRACKS = window.TRACKS || {};
  const AU = new Set(["NSW", "VIC", "QLD", "WA", "SA", "TAS", "NT", "ACT"]);
  function track(code, extra) {
    const t = TRACKS[code] || TRACKS[(code || "").toUpperCase()];
    if (t) return { code, name: t[0], state: t[1], type: t[2], aus: AU.has(t[1]) };
    const x = extra || {};
    const intl = x.venue_country && !/^AU/i.test(x.venue_country);
    return { code, name: x.venue_name || code, state: intl ? x.venue_country : (x.venue_state || ""), type: intl ? "International" : "", aus: !intl };
  }
  const fmtTime = (iso) => !iso ? "" : new Date(iso).toLocaleTimeString("en-AU", { timeZone: "Australia/Melbourne", hour: "numeric", minute: "2-digit" });
  const isScr = (r) => Number(r.scratched) === 1;
  const wt = (r) => r.weight ? r.weight + (r.claim && r.claim !== "0" ? ` <span class="mini">(a${esc(r.claim)})</span>` : "") : "—";
  const horseKey = (n) => String(n || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase().trim()
    .replace(/\s*\([a-z]{2,4}\)\s*$/, "").replace(/[^a-z0-9]/g, "");
  const pos = (r) => { const n = parseInt(r.position, 10); return isNaN(n) ? null : n; };
  const posLabel = (r) => { const p = pos(r); if (!p) return dash(r.position); const s = ["th", "st", "nd", "rd"], v = p % 100; return p + (s[(v - 20) % 10] || s[v] || s[0]); };
  const going = (r) => { const t = String(r.track_condition || "").toLowerCase();
    return t.startsWith("good") ? "Good" : t.startsWith("soft") ? "Soft" : t.startsWith("heavy") ? "Heavy" : t.startsWith("synth") ? "Synthetic" : t.startsWith("firm") ? "Firm" : (r.track_condition || ""); };
  const goingLabel = (r) => [going(r), r.track_condition_numeric && r.track_condition_numeric !== "0" ? r.track_condition_numeric : ""].filter(Boolean).join(" ");
  const grade = (r) => r.race_grade || "";
  function classLabel(r) {
    if (r.race_grade) return r.race_grade;
    const c = String(r.class || "").split(",").map((x) => x.trim()).filter(Boolean);
    const main = c.find((x) => /^(BM|Class|Group|Listed|Maiden|Rating|Restricted|CL|F&M|Open|Hcp|Handicap)/i.test(x) && !/^Handicap$/i.test(x)) || c[0] || "";
    return main.replace(/^Group (\d)$/i, "G$1").replace(/^Listed$/i, "LR");
  }
  const dist = (r) => num(r.distance);
  const raceURL = (r) => `race.html?track=${encodeURIComponent(r.track)}&date=${r.date}&race=${r.race}`;
  const meetingURL = (t, d) => `meeting.html?track=${encodeURIComponent(t)}&date=${d}`;
  const horseURL = (n) => `horse.html?horse=${encodeURIComponent(n)}`;
  const silk = (r, big) => r && r.silk ? `<img class="silk${big ? " big" : ""}" src="${esc(r.silk)}" alt="" loading="lazy">` : `<span class="silk none${big ? " big" : ""}"></span>`;
  const horseCell = (r) => `<span class="horsecell">${silk(r)}<a href="${horseURL(r.horse)}">${esc(r.horse)}</a></span>`;

  // records like "24: 5-3-4"
  function record(runs) {
    let w = 0, s = 0, t = 0, n = 0;
    for (const r of runs) { const p = pos(r); if (p === null && !r.position) continue; n++; if (p === 1) w++; else if (p === 2) s++; else if (p === 3) t++; }
    return { n, w, s, t, text: n ? `${n}: ${w}-${s}-${t}` : "—", win: n ? (100 * w / n) : 0, place: n ? (100 * (w + s + t) / n) : 0 };
  }
  // last-N figure, newest last: "x21x3", 0 = 10th or worse, x = spell
  function figure(desc, n = 10) {
    const runs = desc.slice(0, n).reverse();
    let out = "";
    runs.forEach((r, i) => {
      if (i > 0 && days(runs[i - 1].date, r.date) >= SPELL_DAYS) out += "x";
      const p = pos(r); out += p === null ? "-" : p >= 10 ? "0" : String(p);
    });
    return out || "—";
  }
  // tag each run (oldest first) as first-up / second-up
  function upTags(desc) {
    const asc = [...desc].reverse(), tag = new Map();
    asc.forEach((r, i) => {
      if (i === 0 || days(asc[i - 1].date, r.date) >= SPELL_DAYS) tag.set(r, 1);
      else if (tag.get(asc[i - 1]) === 1) tag.set(r, 2);
    });
    return tag;
  }
  const near = (a, b, tol = 50) => a !== null && b !== null && Math.abs(a - b) <= tol;

  // a horse's stats from earlier runs (newest first), relative to a run "at"
  function horseStats(prior, at) {
    const tags = upTags(prior.concat(at ? [] : []));
    const last = prior[0];
    const d = at ? dist(at) : null;
    return {
      career: record(prior),
      last10: figure(prior, 10), last5: figure(prior, 5),
      dist: at ? record(prior.filter((r) => near(dist(r), d))) : null,
      going: at ? record(prior.filter((r) => going(r) === going(at))) : null,
      track: at ? record(prior.filter((r) => r.track === at.track)) : null,
      trackDist: at ? record(prior.filter((r) => r.track === at.track && near(dist(r), d))) : null,
      jockey: at ? record(prior.filter((r) => r.jockey && r.jockey === at.jockey)) : null,
      firstUp: record(prior.filter((r) => tags.get(r) === 1)),
      secondUp: record(prior.filter((r) => tags.get(r) === 2)),
      daysSince: at && last ? days(last.date, at.date) : null,
      last,
    };
  }

  // ------------------------------------------------------------ blackbook (saved in this browser)
  const BOOK = "tsa-blackbook";
  function book() { try { return JSON.parse(localStorage.getItem(BOOK) || "{}"); } catch (e) { return {}; } }
  function saveBook(b) { try { localStorage.setItem(BOOK, JSON.stringify(b)); } catch (e) { /* storage blocked */ } }
  function toggleBook(name) { const b = book(); if (b[name]) delete b[name]; else b[name] = { note: "", added: todayISO() }; saveBook(b); return !!b[name]; }

  // ------------------------------------------------------------ shared UI
  function tabs(container) {
    const root = typeof container === "string" ? $(container) : container;
    if (!root) return;
    $$("button", root).forEach((b) => b.onclick = () => {
      $$("button", root).forEach((x) => x.classList.toggle("active", x === b));
      $$("[data-tabcontent]").forEach((p) => p.classList.toggle("hidden", p.dataset.tabcontent !== b.dataset.panel));
    });
  }
  const loading = (el) => { if (el) el.innerHTML = `<div class="loading">Loading…</div>`; };
  const fail = (el, e) => { if (el) el.innerHTML = `<div class="error">Couldn't load the data (${esc(e.message || e)}). Try refreshing.</div>`; };
  const groupBy = (arr, f) => arr.reduce((m, x) => { const k = f(x); (m[k] ||= []).push(x); return m; }, {});

  // speed map from settling positions (800m, else 400m)
  function speedMap(runs) {
    const settle = (r) => num(r.pos_800) ?? num(r.pos_400);
    const has = runs.filter((r) => settle(r) !== null);
    if (!has.length) return `<div class="pad note">No settling positions recorded for this race.</div>`;
    const n = runs.length, cut = [0, Math.ceil(n * .2), Math.ceil(n * .45), Math.ceil(n * .75), 99];
    const cols = ["Leaders", "On pace", "Midfield", "Back"];
    const sorted = [...has].sort((a, b) => settle(a) - settle(b));
    return `<div class="speedmap">${cols.map((c, i) => `<div><h4>${c}</h4>${sorted.filter((r) => settle(r) > cut[i] && settle(r) <= cut[i + 1])
      .map((r) => `<div class="runner">${silk(r)}<span>${esc(r.horse)} <span class="mini">(${settle(r)}${pos(r) ? " → " + posLabel(r) : ""})</span></span></div>`).join("") || '<span class="mini">—</span>'}</div>`).join("")}</div>
      <p class="pad note" style="padding-top:0">Positions in running at the 800m (or 400m), and where each finished.</p>`;
  }

  // predicted map for an upcoming race: average settling position (as a share of the field) over the last 5 runs
  function predictedMap(runs, history) {
    const est = runs.filter((r) => !isScr(r)).map((r) => {
      const prior = (history[r.horse_key] || []).slice(0, 5)
        .map((h) => { const p = num(h.pos_800) ?? num(h.pos_400), n = num(h.starters); return p && n ? (p - 1) / Math.max(1, n - 1) : null; })
        .filter((x) => x !== null);
      return { r, v: prior.length ? prior.reduce((a, b) => a + b, 0) / prior.length : null };
    });
    const known = est.filter((e) => e.v !== null).sort((a, b) => a.v - b.v);
    const cols = [["Leaders", 0, .2], ["On pace", .2, .45], ["Midfield", .45, .75], ["Back", .75, 1.01]];
    const unk = est.filter((e) => e.v === null);
    return `<div class="speedmap">${cols.map(([c, lo, hi]) => `<div><h4>${c}</h4>${known.filter((e) => e.v >= lo && e.v < hi)
      .map((e) => `<div class="runner">${silk(e.r)}<span>${esc(e.r.number ? e.r.number + ". " : "")}${esc(e.r.horse)} <span class="mini">(b${dash(e.r.barrier)})</span></span></div>`).join("") || '<span class="mini">—</span>'}</div>`).join("")}</div>
      <p class="pad note" style="padding-top:0">Predicted from where each horse settled in its last 5 runs.${unk.length ? " No settling data for: " + unk.map((e) => esc(e.r.horse)).join(", ") + "." : ""}</p>`;
  }
  // upcoming field table (shared by meeting and race pages)
  const FIELD_HEAD = `<tr><th>No.</th><th class="name">Horse</th><th>Barrier</th><th>Weight</th><th>Jockey</th><th>Trainer</th><th>Last 10</th><th>Career</th><th>At Dist</th><th>On Going</th><th>Days</th><th>Blackbook</th></tr>`;
  function fieldRows(runs, history) {
    const b = book();
    return runs.map((r) => {
      const s = horseStats(history[r.horse_key] || [], r), scr = isScr(r);
      return `<tr style="${scr ? "opacity:.45;text-decoration:line-through" : ""}"><td><b>${dash(r.number)}</b>${Number(r.emergency) === 1 ? ' <span class="pill">EM</span>' : ""}</td>
        <td class="name">${horseCell(r)}${r.gear ? `<div class="mini">Gear: ${esc(r.gear)}</div>` : ""}</td><td>${dash(r.barrier)}</td><td>${wt(r)}</td>
        <td>${dash(r.jockey)}</td><td>${dash(r.trainer)}</td><td>${s.last10}</td><td>${s.career.text}</td><td>${s.dist.text}</td><td>${s.going.text}</td>
        <td>${s.daysSince ?? "1st"}</td><td><button class="star ${b[r.horse] ? "on" : ""}" data-h="${esc(r.horse)}" title="Blackbook">${b[r.horse] ? "★" : "☆"}</button></td></tr>`;
    }).join("");
  }
  function fieldStats(runs, history) {
    const live = runs.filter((r) => !isScr(r)).map((r) => ({ r, s: horseStats(history[r.horse_key] || [], r) }));
    const top = (label, f, fmt) => { const x = [...live].filter((e) => f(e) !== null).sort((a, b) => f(b) - f(a))[0];
      return `<div class="stat"><small>${label}</small><b style="font-size:16px">${x ? esc(x.r.horse) : "—"}</b><div class="mini">${x ? fmt(x) : ""}</div></div>`; };
    return `<div class="grid pad" style="margin:0">
      ${top("Most career wins", (e) => e.s.career.w, (e) => e.s.career.text)}
      ${top("Best win % (3+ starts)", (e) => e.s.career.n >= 3 ? e.s.career.win : null, (e) => e.s.career.win.toFixed(0) + "% · " + e.s.career.text)}
      ${top("Best at this distance", (e) => e.s.dist.n ? e.s.dist.w * 10 + e.s.dist.s * 3 + e.s.dist.t : null, (e) => e.s.dist.text)}
      ${top("Best on this going", (e) => e.s.going.n ? e.s.going.w * 10 + e.s.going.s * 3 + e.s.going.t : null, (e) => e.s.going.text)}
      ${top("Best at this track", (e) => e.s.track.n ? e.s.track.w * 10 + e.s.track.s * 3 + e.s.track.t : null, (e) => e.s.track.text)}
      ${top("Freshest (fewest days since run)", (e) => e.s.daysSince !== null ? -e.s.daysSince : null, (e) => e.s.daysSince + " days")}
    </div>`;
  }
  function bindStars(root, rerender) { $$(".star[data-h]", root).forEach((x) => x.onclick = () => { toggleBook(x.dataset.h); rerender(); }); }

  function raceSummary(runs) {
    const win = runs.find((r) => pos(r) === 1);
    const fav = [...runs].sort((a, b) => (num(a.starting_odds) ?? 999) - (num(b.starting_odds) ?? 999))[0];
    if (!win) return `<div class="pad note">No result recorded.</div>`;
    return `<div class="grid pad" style="margin:0">
      <div class="stat"><small>Winner</small><b style="font-size:17px">${esc(win.horse)}</b></div>
      <div class="stat"><small>Winning barrier</small><b>${dash(win.barrier)}</b></div>
      <div class="stat"><small>Winner's SP</small><b>${dash(win.starting_odds)}</b></div>
      <div class="stat"><small>Winning time</small><b>${dash(String(win.finish_time || "").replace("-", ":"))}</b></div>
      <div class="stat"><small>Favourite</small><b style="font-size:17px">${fav ? esc(fav.horse) + " (" + posLabel(fav) + ")" : "—"}</b></div>
      <div class="stat"><small>Second's margin</small><b>${dash((runs.find((r) => pos(r) === 2) || {}).margin)}${(runs.find((r) => pos(r) === 2) || {}).margin ? "L" : ""}</b></div>
    </div>`;
  }

  async function raceHistory(el, r) {
    if (!el) return;
    loading(el);
    try {
      const d = await get(`/api/runs?track=${encodeURIComponent(r.track)}&race_name=${encodeURIComponent(r.race_name)}&limit=2000`);
      const byDate = groupBy(d.runs.filter((x) => x.date !== r.date), (x) => x.date);
      const rows = Object.keys(byDate).sort().reverse().map((dt) => {
        const w = byDate[dt].find((x) => pos(x) === 1) || byDate[dt][0];
        return `<tr><td>${fmtDate(dt)}</td><td class="name">${horseCell(w)}</td><td>${dash(w.barrier)}</td><td>${dash(w.jockey)}</td><td>${dash(w.trainer)}</td><td>${dash(w.starting_odds)}</td><td>${dash(String(w.finish_time || "").replace("-", ":"))}</td><td><a href="${raceURL(w)}">Race →</a></td></tr>`;
      });
      el.innerHTML = rows.length ? `<div class="tablewrap"><table><thead><tr><th>Date</th><th class="name">Winner</th><th>Barrier</th><th>Jockey</th><th>Trainer</th><th>SP</th><th>Time</th><th></th></tr></thead><tbody>${rows.join("")}</tbody></table></div>`
        : `<div class="pad note">No earlier runnings of "${esc(r.race_name)}" at ${esc(track(r.track).name)} in the database.</div>`;
    } catch (e) { fail(el, e); }
  }

  // ============================================================ PAGES
  const pages = {};

  // ---------------------------------------------- 1. Form Guide homepage
  pages["form-guide"] = async function () {
    let state = "ALL", data = null;
    const rows = $("#rows");
    async function load(date) {
      loading(rows);
      try {
        data = await get("/api/meetings" + (date ? "?date=" + date : ""));
        $("#date").value = data.date || "";
        history.replaceState(null, "", "?date=" + data.date);
        render();
      } catch (e) { fail(rows, e); }
    }
    function render() {
      const q = $("#q").value.toLowerCase();
      const list = data.meetings.map((m) => ({ ...m, t: track(m.track, m) }))
        .filter((m) => state === "ALL" || (state === "INT" ? !m.t.aus : m.t.state === state))
        .filter((m) => (m.t.name + " " + m.track).toLowerCase().includes(q))
        .sort((a, b) => ["Metro", "Provincial", "Country", "International", ""].indexOf(a.t.type) - ["Metro", "Provincial", "Country", "International", ""].indexOf(b.t.type) || a.t.name.localeCompare(b.t.name));
      $("#count").textContent = list.length + " meetings · " + fmtDate(data.date, true) + (data.date === data.today ? " (today)" : "");
      rows.innerHTML = list.map((m) => `<tr><td class="name"><a href="${meetingURL(m.track, data.date)}">${esc(m.t.name)}</a> <span class="mini">${esc(m.track)}</span></td>
        <td>${esc(m.t.state) || "—"}</td><td>${esc(m.t.type) || "—"}</td><td>${m.races}</td><td>${m.runners}</td>
        <td>${esc(goingLabel(m)) || "—"}</td><td>${m.upcoming ? esc(fmtTime(m.first_race)) || "—" : '<span class="pill">Results</span>'}</td>
        <td><a class="btn" href="${meetingURL(m.track, data.date)}">${m.upcoming ? "Form Guide →" : "View Meeting →"}</a></td></tr>`).join("")
        || `<tr><td colspan="8">No meetings${data.meetings.length ? " match" : " on this date"}.</td></tr>`;
    }
    $$("#states button").forEach((b) => b.onclick = () => { $$("#states button").forEach((x) => x.classList.toggle("active", x === b)); state = b.dataset.state; render(); });
    $("#q").oninput = () => data && render();
    $("#date").onchange = () => load($("#date").value);
    $("#prev").onclick = () => data && data.prev && load(data.prev);
    $("#next").onclick = () => data && data.next && load(data.next);
    load(qs("date"));
  };

  // ---------------------------------------------- 2. Meeting
  pages["meeting"] = async function () {
    const t = qs("track"), d = qs("date");
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Choose a meeting from the <a href="form-guide.html">Form Guide</a>.</p>`; return; }
    $("#datecrumb").href = "form-guide.html?date=" + d;
    loading($("#runners"));
    let card;
    try { card = await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}`); } catch (e) { return fail($("#runners"), e); }
    const tr = track(t, card.runs[0]), up = card.upcoming;
    document.title = `${tr.name} ${fmtDate(d)} | The Sporting Almanac`;
    $("#trackname").textContent = tr.name; $("#trackcrumb").textContent = tr.name;
    $("#meta").textContent = [tr.state, tr.type, fmtDate(d, true), up ? "Upcoming" : "Results", card.runs[0] && card.runs[0].rail ? "Rail: " + card.runs[0].rail : ""].filter(Boolean).join(" · ");
    if (up) { $("#runners").closest("table").querySelector("thead").innerHTML = FIELD_HEAD; $$('[data-panel="stats"]').forEach((b) => b.textContent = "Field Stats"); }
    const races = groupBy(card.runs, (r) => r.race);
    const nums = Object.keys(races).map(Number).sort((a, b) => a - b);
    $("#m-races").textContent = nums.length; $("#m-runners").textContent = card.runs.filter((r) => !isScr(r)).length;
    if (up) { $("#m-first-label").textContent = "First Race"; $("#m-first").textContent = fmtTime(card.runs.map((r) => r.start_time).filter(Boolean).sort()[0]) || "—"; }
    $("#m-going").textContent = goingLabel(card.runs[0] || {}) || "—";
    let active = Number(qs("race")) || nums[0];
    function setRace(n) {
      active = n;
      const runs = races[n], r0 = runs[0];
      $("#racebuttons").innerHTML = nums.map((x) => `<button class="${x === n ? "primary" : ""}" data-r="${x}">R${x}<small>${up ? esc(fmtTime(races[x][0].start_time)) : dash(races[x][0].distance) + "m"}</small></button>`).join("");
      $$("#racebuttons button").forEach((b) => b.onclick = () => { setRace(Number(b.dataset.r)); history.replaceState(null, "", `?track=${encodeURIComponent(t)}&date=${d}&race=${b.dataset.r}`); });
      $("#racelabel").textContent = "Race " + n + (up && r0.start_time ? " · " + fmtTime(r0.start_time) : "");
      $("#racelink").href = raceURL(r0);
      $("#racetitle").textContent = r0.race_name || "Race " + n;
      $("#racedetails").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0),
        (up ? money(r0.prize_money) : money(runs.reduce((a, r) => a + (num(r.prize_money) || 0), 0))) + " prize money",
        runs.filter((r) => !isScr(r)).length + " runners", goingLabel(r0)].filter((x) => x && !x.startsWith("—")).join("  |  ");
      if (up) {
        const draw = () => { $("#runners").innerHTML = fieldRows(runs, card.history); bindStars($("#runners"), draw); };
        draw();
        $('[data-tabcontent="speed"]').innerHTML = predictedMap(runs, card.history);
        $('[data-tabcontent="stats"]').innerHTML = fieldStats(runs, card.history);
        $('[data-tabcontent="track"]').innerHTML = `<div class="pad"><p><b>${esc(tr.name)}</b> ${tr.state ? "· " + esc(tr.state) : ""} ${tr.type ? "· " + esc(tr.type) : ""}</p><p>Track condition: <b>${esc(goingLabel(r0) || "not yet rated")}</b></p>${r0.rail ? `<p>Rail: <b>${esc(r0.rail)}</b></p>` : ""}</div>`;
        raceHistory($('[data-tabcontent="history"]'), r0);
        return;
      }
      $("#runners").innerHTML = runs.map((r) => {
        const s = horseStats(card.history[r.horse_key] || [], r);
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.barrier)}</td><td>${dash(r.trainer)}</td><td>${dash(r.jockey)}</td><td>${dash(r.weight)}</td>
          <td>${s.last10}</td><td>${s.career.text}</td><td>${dash(r.starting_odds)}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td></tr>`;
      }).join("");
      $('[data-tabcontent="speed"]').innerHTML = speedMap(runs);
      $('[data-tabcontent="stats"]').innerHTML = raceSummary(runs);
      $('[data-tabcontent="track"]').innerHTML = `<div class="pad"><p><b>${esc(tr.name)}</b> ${tr.state ? "· " + esc(tr.state) : ""} ${tr.type ? "· " + esc(tr.type) : ""}</p><p>Track condition: <b>${esc(goingLabel(r0) || "—")}</b></p><p class="note">Track code: ${esc(t)}</p></div>`;
      raceHistory($('[data-tabcontent="history"]'), r0);
    }
    $("#raceall").innerHTML = nums.map((n) => { const runs = races[n], r0 = runs[0], w = runs.find((r) => pos(r) === 1);
      return `<tr><td>${n}</td><td>${up ? esc(fmtTime(r0.start_time)) + " · " : ""}${dash(r0.distance)}m</td><td>${esc(classLabel(r0)) || "—"}</td><td class="name">${esc(r0.race_name)}</td><td>${runs.filter((r) => !isScr(r)).length}</td><td>${w ? esc(w.horse) : up ? "—" : "—"}</td><td><a href="${raceURL(r0)}">View Race →</a></td></tr>`; }).join("");
    if (up) $("#raceall").closest("table").querySelector("thead").innerHTML = `<tr><th>Race</th><th>Time · Distance</th><th>Class</th><th class="name">Race Name</th><th>Runners</th><th>Winner</th><th></th></tr>`;
    setRace(nums.includes(active) ? active : nums[0]);
    tabs("#meetingtabs");
  };

  // ---------------------------------------------- 3. Race
  pages["race"] = async function () {
    const t = qs("track"), d = qs("date"), n = Number(qs("race")) || 1;
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Choose a race from the <a href="form-guide.html">Form Guide</a>.</p>`; return; }
    $("#meetinglink").href = meetingURL(t, d);
    $("#rn").textContent = n; $("#comparelink").href = `comparison.html?track=${encodeURIComponent(t)}&date=${d}&race=${n}`;
    loading($("#field"));
    let card;
    try { card = await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}&race=${n}`); } catch (e) { return fail($("#field"), e); }
    const runs = card.runs, r0 = runs[0], tr = track(t, r0), up = card.upcoming;
    $("#meetinglink").textContent = tr.name;
    if (!r0) { $("#field").innerHTML = `<tr><td colspan="11">No race ${n} at ${esc(tr.name)} on ${fmtDate(d)}.</td></tr>`; return; }
    if (up) {
      document.title = `${r0.race_name || "Race " + n} | The Sporting Almanac`;
      $("#rbadge").textContent = `Race ${n} · ${tr.name} · ${fmtDate(d, true)}${r0.start_time ? " · " + fmtTime(r0.start_time) : ""}`;
      $("#rtitle").textContent = r0.race_name || "Race " + n;
      $("#rmeta").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0), money(r0.prize_money), goingLabel(r0), r0.rail && "Rail " + r0.rail].filter((x) => x && x !== "—").join(" · ");
      $("#field").closest("table").querySelector("thead").innerHTML = FIELD_HEAD;
      const draw = () => { $("#field").innerHTML = fieldRows(runs, card.history); bindStars($("#field"), draw); };
      draw();
      $('[data-tabcontent="speed"]').innerHTML = predictedMap(runs, card.history);
      $$('[data-panel="stats"]').forEach((b) => b.textContent = "Field Stats");
      $('[data-tabcontent="stats"]').innerHTML = fieldStats(runs, card.history);
      $('[data-tabcontent="sectionals"]').innerHTML = `<div class="pad note">Positions in running appear here after the race.</div>`;
      raceHistory($('[data-tabcontent="history"]'), r0);
      tabs("#racetabs");
      return;
    }
    document.title = `${r0.race_name || "Race " + n} | The Sporting Almanac`;
    $("#rbadge").textContent = `Race ${n} · ${tr.name} · ${fmtDate(d, true)}`;
    $("#rtitle").textContent = r0.race_name || "Race " + n;
    $("#rmeta").textContent = [r0.distance && r0.distance + "m", r0.class || classLabel(r0), money(runs.reduce((a, r) => a + (num(r.prize_money) || 0), 0)), goingLabel(r0)].filter((x) => x && x !== "—").join(" · ");
    function render() {
      const b = book();
      $("#field").innerHTML = runs.map((r) => {
        const s = horseStats(card.history[r.horse_key] || [], r);
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.barrier)}</td><td>${dash(r.weight)}</td><td>${dash(r.jockey)}</td><td>${dash(r.trainer)}</td>
          <td>${s.last5}</td><td>${s.career.text}</td><td>${s.dist.text}</td><td>${dash(r.starting_odds)}</td>
          <td><button class="star ${b[r.horse] ? "on" : ""}" data-h="${esc(r.horse)}" title="Blackbook">${b[r.horse] ? "★" : "☆"}</button></td></tr>`;
      }).join("");
      $$("#field .star").forEach((x) => x.onclick = () => { toggleBook(x.dataset.h); render(); });
    }
    render();
    $('[data-tabcontent="speed"]').innerHTML = speedMap(runs);
    $('[data-tabcontent="stats"]').innerHTML = raceSummary(runs);
    $('[data-tabcontent="sectionals"]').innerHTML = `<div class="tablewrap"><table><thead><tr><th>Pos</th><th class="name">Horse</th><th>1200m</th><th>800m</th><th>400m</th><th>Finish</th><th>Time</th><th>Margin</th></tr></thead><tbody>${runs.map((r) =>
      `<tr><td>${posLabel(r)}</td><td class="name">${horseCell(r)}</td><td>${dash(r.pos_1200)}</td><td>${dash(r.pos_800)}</td><td>${dash(r.pos_400)}</td><td>${dash(pos(r))}</td><td>${dash(String(r.finish_time || "").replace("-", ":"))}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td></tr>`).join("")}</tbody></table></div>
      <p class="pad note">Positions in running at each point of the race. Split times aren't in the data.</p>`;
    raceHistory($('[data-tabcontent="history"]'), r0);
    tabs("#racetabs");
  };

  // ---------------------------------------------- 4. Horse profile
  pages["horse"] = async function () {
    const name = qs("horse");
    if (!name) { $("#main").innerHTML = `<p class="sub">Search for a horse on the <a href="blackbook.html">Blackbook</a> page, or open one from a race.</p>`; return; }
    $("#horseName").textContent = name.toUpperCase();
    loading($("#formrows"));
    let runs, entries = [];
    try {
      [runs, entries] = await Promise.all([get(`/api/runs?horse=${encodeURIComponent(name)}&limit=5000`).then((x) => x.runs), get(`/api/upcoming?horse=${encodeURIComponent(name)}`).catch(() => [])]);
    } catch (e) { return fail($("#formrows"), e); }
    $('[data-tabcontent="entries"]').innerHTML = `<h3>Upcoming Entries</h3>` + (entries.length ? `<div class="tablewrap"><table><thead><tr><th>Date</th><th>Time</th><th>Track</th><th class="name">Race</th><th>Dist</th><th>No.</th><th>Barrier</th><th>Weight</th><th>Jockey</th></tr></thead><tbody>${entries.map((e) =>
      `<tr style="${isScr(e) ? "opacity:.45;text-decoration:line-through" : ""}"><td>${fmtDate(e.date)}</td><td>${esc(fmtTime(e.start_time))}</td><td>${esc(track(e.track, e).name)}</td><td class="name"><a href="${raceURL(e)}">R${e.race} ${esc(e.race_name)}</a></td><td>${dash(e.distance)}</td><td>${dash(e.number)}</td><td>${dash(e.barrier)}</td><td>${wt(e)}</td><td>${dash(e.jockey)}</td></tr>`).join("")}</tbody></table></div>`
      : `<p class="note">No upcoming starts in the next few days.</p>`);
    if (entries.length) { const b = $('[data-panel="entries"]'); if (b) b.textContent = `Entries (${entries.length})`; }
    if (!runs.length) {
      $("#formrows").innerHTML = `<tr><td colspan="18">${entries.length ? "No starts yet — see Entries for its first run." : "No runs found for " + esc(name) + "."}</td></tr>`;
      if (entries.length) { $("#horseName").textContent = entries[0].horse.toUpperCase(); $("#trainer").textContent = "—"; }
      tabs("#horsetabs"); return;
    }
    runs.sort((a, b) => b.date.localeCompare(a.date) || 0);
    const last = runs[0], prev = runs[1], disp = last.horse;
    document.title = `${disp} | The Sporting Almanac`;
    $("#horseName").textContent = disp.toUpperCase();
    $("#silk").innerHTML = silk(last, true);
    $("#trainer").textContent = dash(last.trainer);
    const star = () => { const on = !!book()[disp]; $("#star").textContent = on ? "★" : "☆"; $("#star").classList.toggle("on", on); };
    $("#star").onclick = () => { toggleBook(disp); star(); }; star();

    const lastWin = runs.find((r) => pos(r) === 1);
    $("#m-run").textContent = days(last.date, todayISO());
    $("#m-win").textContent = lastWin ? days(lastWin.date, todayISO()) : "—";
    $("#m-weight").textContent = last.weight ? last.weight + "kg" : "—";
    $("#m-dist").textContent = last.distance ? last.distance + "m" : "—";
    $("#m-class").textContent = classLabel(last) || "—";

    const c = record(runs);
    $("#c-starts").textContent = c.n; $("#c-w").textContent = c.w; $("#c-s").textContent = c.s; $("#c-t").textContent = c.t;
    $("#c-pct").textContent = `Win ${c.win.toFixed(1)}% · Place ${c.place.toFixed(1)}% · Prize money ${money(runs.reduce((a, r) => a + (num(r.prize_money) || 0), 0))}`;
    const wins = runs.filter((r) => pos(r) === 1 && dist(r));
    $("#winrange").textContent = wins.length ? `${Math.min(...wins.map(dist))}–${Math.max(...wins.map(dist))}m` : "no wins yet";
    $("#goingrec").innerHTML = ["Good", "Soft", "Heavy", "Synthetic", "Firm"].map((g) => [g, record(runs.filter((r) => going(r) === g))])
      .filter(([, r]) => r.n).map(([g, r]) => `<p>${g}: <b>${r.text}</b></p>`).join("") || "<p>—</p>";
    const s = horseStats(runs.slice(1), last), tags = upTags(runs);
    $("#fresh").innerHTML = `<p>First-up: <b>${record(runs.filter((r) => tags.get(r) === 1)).text}</b></p><p>Second-up: <b>${record(runs.filter((r) => tags.get(r) === 2)).text}</b></p>
      <p>${esc(track(last.track).name)}: <b>${record(runs.filter((r) => r.track === last.track)).text}</b></p>
      <p>${esc(track(last.track).name)} ${dash(last.distance)}m: <b>${record(runs.filter((r) => r.track === last.track && near(dist(r), dist(last)))).text}</b></p>`;
    $("#lastcmp").innerHTML = `<p>${esc(dash(last.jockey))} on this horse: <b>${record(runs.filter((r) => r.jockey && r.jockey === last.jockey)).text}</b></p>
      ${prev ? `<p>Weight change: <b>${fmtDelta(num(last.weight), num(prev.weight), "kg")}</b></p><p>Distance change: <b>${fmtDelta(dist(last), dist(prev), "m")}</b></p>
      <p>Class: <b>${classLabel(prev) && classLabel(last) && classLabel(prev) !== classLabel(last) ? esc(classLabel(prev) + " → " + classLabel(last)) : "same"}</b></p>` : "<p>First start.</p>"}
      <p>Days between last two runs: <b>${prev ? days(prev.date, last.date) : "—"}</b></p>`;

    let scope = "all";
    function renderForm() {
      const list = runs.filter((r) => scope === "all" || (scope === "aus" ? track(r.track).aus : !track(r.track).aus));
      $("#formrows").innerHTML = list.map((r) => {
        const i = runs.indexOf(r), p = runs[i + 1];
        return `<tr class="${pos(r) === 1 ? "win" : ""}"><td>${fmtDate(r.date)}</td><td><a href="${meetingURL(r.track, r.date)}">${esc(track(r.track).name)}</a></td>
          <td class="name"><a href="${raceURL(r)}">R${r.race} ${esc(r.race_name)}</a></td><td>${dash(r.distance)}</td><td>${esc(goingLabel(r)) || "—"}</td><td>${esc(classLabel(r)) || "—"}</td>
          <td><b>${posLabel(r)}</b>${r.starters ? `<span class="mini">/${esc(r.starters)}</span>` : ""}</td><td>${r.margin && pos(r) !== 1 ? r.margin + "L" : "—"}</td><td>${dash(r.barrier)}</td><td>${dash(r.weight)}</td>
          <td>${dash(r.jockey)}</td><td>${dash(r.starting_odds)}</td><td>${dash(String(r.finish_time || "").replace("-", ":"))}</td><td>${dash(r.pos_400)}</td><td>${dash(r.pos_800)}</td>
          <td>${p ? fmtDelta(num(r.weight), num(p.weight), "") : "—"}</td><td>${p ? fmtDelta(dist(r), dist(p), "") : "—"}</td>
          <td>${p && classLabel(p) !== classLabel(r) ? esc(classLabel(p) + " → " + classLabel(r)) : "—"}</td></tr>`;
      }).join("") || `<tr><td colspan="18">No ${scope === "aus" ? "Australian" : "international"} runs.</td></tr>`;
    }
    $$("[data-scope]").forEach((b) => b.onclick = () => { $$("[data-scope]").forEach((x) => x.classList.toggle("active", x === b)); scope = b.dataset.scope; renderForm(); });
    renderForm();

    // Stats tab: records by distance band, going, track, jockey
    const band = (r) => { const x = dist(r); return !x ? "?" : x <= 1100 ? "Up to 1100m" : x <= 1300 ? "1101–1300m" : x <= 1600 ? "1301–1600m" : x <= 2000 ? "1601–2000m" : x <= 2400 ? "2001–2400m" : "2401m+"; };
    const table = (title, groups) => `<h3>${title}</h3><div class="tablewrap" style="margin-bottom:18px"><table><thead><tr><th class="name"></th><th>Record</th><th>Win %</th><th>Place %</th></tr></thead><tbody>${Object.entries(groups)
      .map(([k, v]) => [k, record(v)]).sort((a, b) => b[1].n - a[1].n).map(([k, r]) => `<tr><td class="name">${esc(k)}</td><td>${r.text}</td><td>${r.win.toFixed(0)}%</td><td>${r.place.toFixed(0)}%</td></tr>`).join("")}</tbody></table></div>`;
    $('[data-tabcontent="stats"]').innerHTML = table("By distance", groupBy(runs, band)) + table("By going", groupBy(runs, (r) => going(r) || "Unknown"))
      + table("By track", groupBy(runs, (r) => track(r.track).name)) + table("By jockey", groupBy(runs.filter((r) => r.jockey), (r) => r.jockey));
    tabs("#horsetabs");
  };
  function fmtDelta(a, b, unit) { if (a === null || b === null) return "—"; const d = Math.round((a - b) * 10) / 10; return d === 0 ? "0" : (d > 0 ? "+" : "−") + Math.abs(d) + unit; }

  // ---------------------------------------------- 5. Comparison
  pages["comparison"] = async function () {
    const t = qs("track"), d = qs("date"), n = Number(qs("race")) || 1;
    if (!t || !d) { $("#main").innerHTML = `<p class="sub">Open a race and choose <b>Compare runners</b>.</p>`; return; }
    $("#racelink").href = `race.html?track=${encodeURIComponent(t)}&date=${d}&race=${n}`;
    loading($("#compbody"));
    let card;
    try { card = await get(`/api/card?track=${encodeURIComponent(t)}&date=${d}&race=${n}`); } catch (e) { return fail($("#compbody"), e); }
    const runs = card.runs.filter((r) => !isScr(r)), up = card.upcoming, tr = track(t, runs[0]);
    $("#racelink").textContent = `${tr.name} Race ${n}`;
    if (!runs.length) { $("#compbody").innerHTML = `<tr><td>No such race.</td></tr>`; return; }
    $("#racehead").textContent = `${tr.name} · ${fmtDate(d, true)} · Race ${n} · ${runs[0].race_name || ""} (${dash(runs[0].distance)}m)`;
    const stats = new Map(runs.map((r) => [r, horseStats(card.history[r.horse_key] || [], r)]));
    let selected = up ? [...runs].sort((a, b) => stats.get(b).career.win - stats.get(a).career.win).slice(0, 4)
      : [...runs].sort((a, b) => (num(a.starting_odds) ?? 999) - (num(b.starting_odds) ?? 999)).slice(0, 4);
    $("#horses").innerHTML = runs.map((r, i) => `<option value="${i}">${esc(r.horse)}</option>`).join("");
    const rowsDef = [
      ["Silk", (r) => silk(r, true)], up ? ["Number", (r) => `<b>${dash(r.number)}</b>`] : ["Finished", (r) => `<b>${posLabel(r)}</b>`], ["Barrier", (r) => dash(r.barrier)], ["Weight", (r) => wt(r)],
      ["Jockey", (r) => dash(r.jockey)], ["Trainer", (r) => dash(r.trainer)], up ? ["Gear changes", (r) => dash(r.gear)] : ["Starting price", (r) => dash(r.starting_odds)],
      ["Recent form", (r) => stats.get(r).last10], ["Career", (r) => stats.get(r).career.text], ["At this distance", (r) => stats.get(r).dist.text],
      ["On this going", (r) => stats.get(r).going.text], ["At this track", (r) => stats.get(r).track.text], ["With this jockey", (r) => stats.get(r).jockey.text],
      ["First-up / second-up", (r) => stats.get(r).firstUp.text + " / " + stats.get(r).secondUp.text], ["Days since last run", (r) => dash(stats.get(r).daysSince)],
      ["Last start", (r) => { const l = stats.get(r).last; return l ? `${posLabel(l)} · ${esc(track(l.track).name)} ${dash(l.distance)}m · ${fmtDate(l.date)}` : "First start"; }],
    ];
    function comp() {
      $("#comphead").innerHTML = "<tr><th>Metric</th>" + selected.map((r) => `<th><a href="${horseURL(r.horse)}">${esc(r.horse)}</a> <button data-x="${runs.indexOf(r)}" title="Remove">×</button></th>`).join("") + "</tr>";
      $("#compbody").innerHTML = rowsDef.map(([l, f]) => `<tr><td>${l}</td>${selected.map((r) => `<td>${f(r)}</td>`).join("")}</tr>`).join("");
      $$("#comphead [data-x]").forEach((b) => b.onclick = () => { selected = selected.filter((r) => r !== runs[Number(b.dataset.x)]); comp(); });
    }
    $("#add").onclick = () => { const r = runs[Number($("#horses").value)]; if (!selected.includes(r)) selected.push(r); comp(); };
    comp();
  };

  // ---------------------------------------------- 6. Blackbook
  pages["blackbook"] = async function () {
    const input = $("#search"), box = $("#suggest");
    let timer;
    input.oninput = () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { box.classList.add("hidden"); return; }
      timer = setTimeout(async () => {
        try {
          const list = await get("/api/horses?q=" + encodeURIComponent(q));
          box.innerHTML = list.map((h) => `<div data-h="${esc(h.horse)}"><span>${esc(h.horse)}</span><span class="mini">${h.starts} starts · last ${fmtDate(h.last_date)}</span></div>`).join("") || `<div class="mini">No horses found</div>`;
          box.classList.remove("hidden");
          $$("[data-h]", box).forEach((x) => x.onclick = () => { const b = book(); b[x.dataset.h] ??= { note: "", added: todayISO() }; saveBook(b); input.value = ""; box.classList.add("hidden"); render(); });
        } catch (e) { box.innerHTML = `<div class="error">${esc(e.message)}</div>`; box.classList.remove("hidden"); }
      }, 200);
    };
    document.addEventListener("click", (e) => { if (!box.contains(e.target) && e.target !== input) box.classList.add("hidden"); });

    const lastRuns = {};
    async function render() {
      const b = book(), names = Object.keys(b).sort();
      $("#count").textContent = names.length + (names.length === 1 ? " horse" : " horses");
      $("#bookrows").innerHTML = names.map((h) => `<tr><td class="name" data-last="${esc(h)}"><span class="horsecell"><span class="silk none"></span><a href="${horseURL(h)}">${esc(h)}</a></span></td>
        <td><input class="field blacknote" value="${esc(b[h].note || "")}" data-note="${esc(h)}" placeholder="Add a note…"></td>
        <td data-next="${esc(horseKey(h))}" class="mini">—</td><td data-lastrun="${esc(h)}" class="mini">…</td><td><button data-remove="${esc(h)}">Remove</button></td></tr>`).join("")
        || `<tr><td colspan="5">No horses saved yet. Search above, or tap ☆ on any race or horse page.</td></tr>`;
      if (names.length) get("/api/upcoming?keys=" + encodeURIComponent(names.map(horseKey).join(","))).then((list) => {
        for (const e of list) {
          const cell = $$("[data-next]").find((x) => x.dataset.next === e.horse_key);
          if (cell && cell.textContent === "—") cell.innerHTML = `<a href="${raceURL(e)}"><b>${fmtDate(e.date)} ${esc(fmtTime(e.start_time))}</b> · ${esc(track(e.track, e).name)} R${e.race} · ${dash(e.distance)}m${e.barrier ? " · b" + esc(e.barrier) : ""}</a>${isScr(e) ? " (scratched)" : ""}`;
        }
      }).catch(() => {});
      $$("[data-note]").forEach((el) => el.onchange = () => { const b = book(); if (b[el.dataset.note]) { b[el.dataset.note].note = el.value; saveBook(b); } });
      $$("[data-remove]").forEach((el) => el.onclick = () => { const b = book(); delete b[el.dataset.remove]; saveBook(b); render(); });
      for (const h of names) {
        try {
          const r = lastRuns[h] ||= (await get(`/api/runs?horse=${encodeURIComponent(h)}&limit=1`)).runs[0] || null;
          const cell = $$("[data-lastrun]").find((x) => x.dataset.lastrun === h), nameCell = $$("[data-last]").find((x) => x.dataset.last === h);
          if (cell) cell.innerHTML = r ? `<a href="${raceURL(r)}">${posLabel(r)} · ${esc(track(r.track).name)} R${r.race} · ${dash(r.distance)}m · ${fmtDate(r.date)}</a>` : "No runs found";
          if (nameCell && r) nameCell.querySelector(".silk").outerHTML = silk(r);
        } catch (e) { /* leave as is */ }
      }
    }
    render();
  };

  // ------------------------------------------------------------ start
  window.FG = { track, record, figure, horseStats, API };
  document.addEventListener("DOMContentLoaded", () => {
    const p = document.body.dataset.page;
    if (pages[p]) pages[p]().catch((e) => console.error(e));
  });
})();
