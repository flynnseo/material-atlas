---
description: 소재 하나를 리서치해서 draft 카드로 만든다
argument-hint: <소재 이름>
---
"$ARGUMENTS" 소재 카드를 만든다.

1. `materials/` 와 `site/index.json`(있으면)에서 같은/비슷한 소재가 이미 있는지 먼저 찾는다. 있으면 새로 만들지 말고 그 카드를 보강한다.
2. 웹 리서치: 제조사 데이터시트, 소재 라이브러리, 업계 매체에서 정의·특성·가공·마감·공간 사용례를 찾는다.
3. `_templates/material.md` 를 복사해 `materials/<family>/<id>.md` 로 만든다.
   - `aliases` 를 최대한 채운다: 한국 현장 용어, 을지로식 은어, 흔한 오타, 영문/미국식 철자, 규격번호, 상표 계열명.
   - 수치는 출처가 있을 때만. 출처 URL은 `sources` 에. 출처 1개 이하면 `confidence: C`.
   - 태그는 `_meta/vocab.yaml` 에 있는 것만. 필요한 태그가 없으면 vocab에 동의어와 함께 먼저 추가.
   - 관련 마감·사례 id를 `finishes`/`cases` 에 넣는다. 아직 없는 카드여도 넣어둔다(만들 대상 표시).
4. `python scripts/build.py --test` → 오류 0 확인.
5. `_meta/search_tests.json` 에 이 소재를 찾는 "엉터리 질의" 2개(오타/은어)를 추가하고 다시 테스트.
6. 무엇을 확신하고 무엇이 불확실한지 3줄로 보고. 커밋은 하지 말 것(태건이 검수 후 /build).
