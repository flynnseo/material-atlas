// 검색 품질 테스트: _meta/search_tests.json 의 "개떡같은 질의"가 기대한 카드를 상위 N위 안에 찾는지 확인
// 실행: node scripts/test_search.js   (build.py --test 가 자동 실행)
const fs = require('fs');
const path = require('path');
const S = require('./search.js');

const root = path.join(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'site', 'index.json'), 'utf8'));
const tests = JSON.parse(fs.readFileSync(path.join(root, '_meta', 'search_tests.json'), 'utf8'));
const idx = S.buildIndex(data);
const ids = new Set(data.docs.map(d => d.id));

let pass = 0, fail = 0, skip = 0;
for (const t of tests) {
  if (!ids.has(t.expect)) { skip++; continue; } // 아직 카드가 없는 테스트는 건너뜀
  const r = S.search(idx, t.q);
  const top = t.top || 3;
  const inHits = r.hits.slice(0, top).map(h => h.id);
  const inRel = t.related ? r.related.map(h => h.id) : [];
  const ok = inHits.includes(t.expect) || inRel.includes(t.expect);
  if (ok) pass++; else fail++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  "${t.q}" → ${t.expect}` + (ok ? '' : `   (받은 결과: ${inHits.join(', ') || '없음'})`));
}
console.log(`\n${pass} 통과 · ${fail} 실패 · ${skip} 대상 카드 없음`);
process.exit(fail ? 1 : 0);
