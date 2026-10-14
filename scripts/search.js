/* MATERIAL ATLAS 검색 엔진 — 브라우저(atlas.html)와 Node(테스트) 양쪽에서 쓴다.
 *
 * 목표: "개떡같이" 쳐도 찾는다.
 *  1) 정규화   : 대소문자·공백·기호 무시, 한글을 자모로 분해 → "알루미눔"도 "알루미늄"과 거의 같게
 *  2) 초성검색 : "ㅇㄹㅁㄴ" → 알루미늄
 *  3) 동의어   : vocab.yaml 동의어 → 정식 태그 ("스뎅" → stainless-steel, "무광" → matte)
 *  4) 퍼지     : 자모 바이그램 Dice 유사도로 오타 허용
 *  5) 조사허용 : "알루미늄으로" 처럼 키워드 뒤에 붙은 말 허용
 *  6) 소프트AND: 여러 단어면 다 맞을수록 위로, 하나 빠져도 결과는 남김
 *  7) 그래프   : 직접 맞은 카드의 링크·백링크·유사 카드를 "연결된 자료"로 끌어올림
 */
(function (root) {
  'use strict';

  var CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'.split('');
  var JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'.split('');
  var JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'];
  var CHO_SET = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ';

  function jamo(s) {
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 0xac00 && c <= 0xd7a3) {
        var k = c - 0xac00;
        out += CHO[Math.floor(k / 588)] + JUNG[Math.floor((k % 588) / 28)] + JONG[k % 28];
      } else out += s[i];
    }
    return out;
  }

  function choseong(s) {
    var out = '';
    for (var i = 0; i < s.length; i++) {
      var c = s.charCodeAt(i);
      if (c >= 0xac00 && c <= 0xd7a3) out += CHO[Math.floor((c - 0xac00) / 588)];
      else if (CHO_SET.indexOf(s[i]) >= 0) out += s[i];
    }
    return out;
  }

  function isChoQuery(s) {
    if (s.length < 2) return false;
    for (var i = 0; i < s.length; i++) if (CHO_SET.indexOf(s[i]) < 0) return false;
    return true;
  }

  // 정규화: NFKC, 소문자, 공백·기호 제거, 자모 분해
  function norm(s) {
    s = String(s == null ? '' : s);
    if (s.normalize) s = s.normalize('NFKC');
    s = s.toLowerCase().replace(/[\s\-_·.,/()\[\]{}'"`~!?:;+*&%#@|\\]+/g, '');
    return jamo(s);
  }

  function grams(s) {
    var g = {}, p = '^' + s + '$', n = 0;
    for (var i = 0; i < p.length - 1; i++) {
      var b = p.substr(i, 2);
      if (!g[b]) { g[b] = 1; n++; }
    }
    return { g: g, n: n };
  }

  function dice(a, b) {
    if (!a.n || !b.n) return 0;
    var hit = 0;
    for (var k in a.g) if (b.g[k]) hit++;
    return (2 * hit) / (a.n + b.n);
  }

  // 한 키(이름/별칭/태그)와 한 토큰의 일치도 0~1
  function matchKey(t, tg, key) {
    if (!key.t || !t) return 0;
    if (key.t === t) return 1;
    if (key.t.indexOf(t) === 0) return t.length >= 2 ? 0.9 : 0.5;     // 앞부분 입력 중
    if (t.indexOf(key.t) === 0 && key.t.length >= 4) return 0.85;    // 키워드+조사 ("알루미늄으로")
    if (key.t.indexOf(t) > 0 && t.length >= 3) return 0.7;           // 중간 포함
    var d = dice(tg, key.g);
    // 짧은 키는 바이그램이 적어서 기준을 높인다
    var th = Math.min(key.t.length, t.length) <= 4 ? 0.6 : 0.5;
    return d >= th ? d * 0.85 : 0;
  }

  /* ---------- 인덱스 만들기 ---------- */
  // data = { docs: [...], synonyms: [[동의어, 정식태그], ...], tagLabels: {태그: 한글명} }  (build.py가 생성)
  function buildIndex(data) {
    var docs = data.docs;
    var byId = {};
    var keyW = { name: 1.0, alias: 0.95, id: 0.9, tag: 0.6 };

    docs.forEach(function (d) {
      byId[d.id] = d;
      var keys = [];
      function add(v, w, raw) {
        if (!v) return;
        var t = norm(v);
        if (!t) return;
        keys.push({ t: t, g: grams(t), w: w, raw: raw || v });
      }
      add(d.name_ko, keyW.name); add(d.name_en, keyW.name);
      (d.aliases || []).forEach(function (a) { add(a, keyW.alias); });
      add(d.id, keyW.id);
      d._keys = keys;
      d._tags = {};
      (d.tags || []).forEach(function (t) { d._tags[t] = 0.8; });
      // 카드 자신의 소재군/하위군이면 더 강하게 (마감 카드의 applies_to 보다 소재 카드가 위로)
      [d.family, d.subfamily].forEach(function (t) { if (t) d._tags[t] = 0.9; });
      d._cho = choseong(d.name_ko || '') + ' ' + (d.aliases || []).map(choseong).join(' ');
      d._choName = choseong(d.name_ko || '');
      d._text = norm(d.text || '');
    });

    // 동의어 사전: 정식 태그 자체도 동의어로 등록
    var syn = [];
    var seen = {};
    function addSyn(word, tag) {
      var t = norm(word);
      if (!t || seen[t + '|' + tag]) return;
      seen[t + '|' + tag] = 1;
      syn.push({ t: t, g: grams(t), tag: tag, raw: word });
    }
    (data.synonyms || []).forEach(function (p) { addSyn(p[0], p[1]); }); // [[동의어, 정식태그], ...]
    Object.keys(data.tagLabels || {}).forEach(function (tag) { addSyn(tag, tag); });

    return { docs: docs, byId: byId, syn: syn, tagLabels: data.tagLabels || {} };
  }

  /* ---------- 질의 확장 ---------- */
  function expandToken(idx, t, tg) {
    var out = {};
    idx.syn.forEach(function (s) {
      var m = matchKey(t, tg, s);
      if (m >= 0.6 && (!out[s.tag] || out[s.tag] < m)) out[s.tag] = m;
    });
    return out; // { 정식태그: 확신도 }
  }

  function scoreToken(d, tok) {
    var best = 0, why = '';
    // 1) 이름/별칭/id
    for (var i = 0; i < d._keys.length; i++) {
      var k = d._keys[i];
      var m = matchKey(tok.t, tok.g, k) * k.w;
      if (m > best) { best = m; why = k.raw; }
    }
    // 2) 동의어 → 태그
    for (var tag in tok.exp) {
      if (d._tags[tag]) {
        var s = d._tags[tag] * tok.exp[tag];
        if (s > best) { best = s; why = '#' + tag; }
      }
    }
    // 3) 초성
    if (tok.cho && d._choName === tok.raw) {               // 이름 초성과 정확히 같으면 우선
      if (0.9 > best) { best = 0.9; why = '초성'; }
    } else if (tok.cho && d._cho.indexOf(tok.raw) >= 0) {
      if (0.85 > best) { best = 0.85; why = '초성'; }
    }
    // 4) 본문
    if (best < 0.3 && tok.t.length >= 4 && d._text.indexOf(tok.t) >= 0) { best = 0.3; why = '본문'; }
    return { s: best, why: why };
  }

  /* ---------- 검색 ---------- */
  // opts: { types: ['material',...] | null, limit: 30 }
  function search(idx, query, opts) {
    opts = opts || {};
    var limit = opts.limit || 30;
    var raw = String(query || '').trim();
    if (!raw) return { hits: [], related: [], tokens: [], suggest: null };

    var tokens = raw.split(/\s+/).filter(Boolean).map(function (w) {
      var t = norm(w);
      var tg = grams(t);
      return { raw: w, t: t, g: tg, cho: isChoQuery(w), exp: expandToken({ syn: idx.syn }, t, tg) };
    }).filter(function (x) { return x.t; });

    var hits = [];
    idx.docs.forEach(function (d) {
      if (opts.types && opts.types.length && opts.types.indexOf(d.type) < 0) return;
      var sum = 0, matched = 0, why = [];
      tokens.forEach(function (tok) {
        var r = scoreToken(d, tok);
        if (r.s > 0) { matched++; sum += r.s; why.push(r.why); }
      });
      if (!matched) return;
      var score = sum / tokens.length;
      if (matched < tokens.length) score *= 0.6; // 소프트 AND
      if (d.status === 'deep') score *= 1.05;
      if (d.status === 'verified') score *= 1.02;
      if (score >= 0.22) hits.push({ id: d.id, score: score, why: why });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    hits = hits.slice(0, limit);

    // 그래프 확장: 링크(0.5) · 백링크(0.5) · 유사(0.3)
    // 상위 10개만 '직접 결과'로 고정. 그 아래 결과도 여러 상위 카드가 가리키면 연결된 자료로 올라온다.
    var direct = {};
    hits.slice(0, 10).forEach(function (h) { direct[h.id] = 1; });
    var rel = {};
    hits.slice(0, 8).forEach(function (h) {
      var d = idx.byId[h.id];
      function push(id, w, via) {
        if (direct[id] || !idx.byId[id]) return;
        var s = h.score * w;
        if (!rel[id]) rel[id] = { id: id, score: s, via: via + ' ' + d.id, n: 1 };
        else { rel[id].n++; if (rel[id].score < s) { rel[id].score = s; rel[id].via = via + ' ' + d.id; } }
      }
      (d.links || []).forEach(function (id) { push(id, 0.5, '←'); });
      (d.backlinks || []).forEach(function (id) { push(id, 0.5, '→'); });
      (d.related || []).forEach(function (id) { push(id, 0.3, '≈'); });
    });
    Object.keys(rel).forEach(function (k) { rel[k].score += 0.05 * (rel[k].n - 1); });
    var related = Object.keys(rel).map(function (k) { return rel[k]; })
      .sort(function (a, b) { return b.score - a.score; }).slice(0, 12);

    // 결과 없음 → "혹시 이거?" (가장 가까운 키)
    var suggest = null;
    if (!hits.length && tokens.length) {
      var best = 0;
      idx.docs.forEach(function (d) {
        d._keys.forEach(function (k) {
          var s = dice(tokens[0].g, k.g);
          if (s > best) { best = s; suggest = { id: d.id, label: k.raw }; }
        });
      });
      if (best < 0.25) suggest = null;
    }

    var inRel = {};
    related.forEach(function (r) { inRel[r.id] = 1; });
    hits = hits.filter(function (h, i) { return i < 10 || !inRel[h.id]; });
    return { hits: hits, related: related, tokens: tokens.map(function (t) { return { raw: t.raw, exp: Object.keys(t.exp) }; }), suggest: suggest };
  }

  var api = { norm: norm, jamo: jamo, choseong: choseong, buildIndex: buildIndex, search: search };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.AtlasSearch = api;
})(this);
