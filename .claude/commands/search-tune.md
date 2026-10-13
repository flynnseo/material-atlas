---
description: 검색이 못 찾은 질의를 고친다
argument-hint: <못 찾은 검색어> => <원했던 카드 id 또는 이름>
---
"$ARGUMENTS" 를 해결한다.

1. `node -e` 로 `scripts/search.js` 를 불러 그 질의의 결과와 점수, why 를 출력해 원인을 진단한다.
2. 고치는 순서(가벼운 것부터):
   a. 해당 카드 `aliases` 에 그 표현 추가
   b. `_meta/vocab.yaml` 동의어 추가 (여러 카드에 걸친 표현이면)
   c. 그래도 안 되면 `scripts/search.js` 의 점수 규칙 수정 — 반드시 `_meta/search_tests.json` 전체가 계속 통과해야 함
3. 이 질의를 search_tests.json 에 추가하고 `python scripts/build.py --test`.
