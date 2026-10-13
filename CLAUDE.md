# MATERIAL ATLAS — Claude Code 작업 규칙

패션 공간·리테일·전시·건축·예술 오브제에 쓰이는 소재와 마감을 카드로 모은 개인 위키.
주인: 태건(Jeremy). 목적: 브랜드 공간 면접·입사 후 오브제/집기 제작 레퍼런스. 답은 한국어로, 짧고 밀도 있게.

## 구조
- `materials/<family>/MTL-*.md` 소재 · `finishes/FIN-*.md` 마감 · `cases/CASE-*.md` 사례 · `lab/LAB-*.md` 직접 실험
- `materials/_new/` 분류가 애매한 신소재 (`novelty: emerging`)
- `_meta/schema.yaml` 필드 정의 · `_meta/vocab.yaml` 통제 태그+동의어 · `_meta/backlog.md` 조사 대기열 · `_meta/search_tests.json` 검색 회귀 테스트
- `_templates/` 카드 템플릿 · `scripts/build.py` 검사·빌드 · `scripts/search.js` 검색 엔진 · `scripts/atlas_template.html` 화면
- `site/` 는 빌드 결과물(커밋 안 함). GitHub Actions가 push마다 빌드해서 Pages로 배포.

## 규칙
1. 카드는 `_templates/` 에서 시작하고 `schema.yaml` 필수 필드를 채운다. 모르는 값은 비우고 `confidence: C`.
2. 수치·사실은 출처 없이 쓰지 않는다. 출처 URL은 `sources` 에. A=제조사 데이터시트/규격, B=신뢰할 2차 자료 2곳+, C=그 외.
3. 태그는 `vocab.yaml` 에 있는 것만. 새 태그는 vocab에 **동의어와 함께** 먼저 추가.
4. **검색 품질이 이 프로젝트의 핵심이다.** 카드를 만들 때마다 `aliases` 에 현장 용어, 을지로식 은어, 흔한 오타, 영문/미국식 철자, 규격번호, 상표 계열명을 넣는다.
5. 카드끼리는 id 필드(`finishes`, `cases`, `materials`, `variant_of`, `applies_to`)나 본문 `[[ID]]` 로 연결한다. 사례↔소재는 양방향으로.
6. `hands_on`, `status: deep`, `confidence: A` 승격은 태건만 한다. `sample: true` 카드는 실제 리서치로 덮어쓰면 `sample` 줄을 지운다.
7. 작업 후 항상 `python scripts/build.py --test`. 오류 0일 때만 커밋. 커밋/푸시는 `/build` 로만.
8. `scripts/search.js` 를 고칠 때는 `search_tests.json` 이 전부 통과해야 한다. 테스트를 지워서 통과시키지 말 것.
9. 이미지·사진은 `assets/<카드id>-01.jpg` 식으로. 저작권 있는 이미지를 대량 복제하지 말고 출처 링크를 우선.

## 명령
`/add-material` `/batch` `/case` `/audit` `/compare` `/search-tune` `/build`

## 실행 환경
Windows 데스크탑과 맥북 양쪽에서 같은 레포를 쓴다. 경로는 항상 `/` 와 상대경로, Python은 `python`(Windows) / `python3`(mac) 둘 다 동작하게.
