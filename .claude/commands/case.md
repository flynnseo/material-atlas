---
description: 브랜드 공간/작품 사례 카드를 만들고 소재 카드와 양방향 연결
argument-hint: <브랜드> <공간/작품 이름>
---
"$ARGUMENTS" 사례 카드를 만든다.

1. 공식 사이트·건축/디자인 매체 기사로 위치, 연도, 디자이너, 눈에 띄는 소재와 마감을 조사한다. 확인 안 된 소재 추정은 본문에 "추정"이라고 쓰고 `confidence: C`.
2. `_templates/case.md` → `cases/<id>.md`.
3. 쓰인 소재/마감 id를 `materials`/`finishes` 에 넣고, 해당 소재 카드의 `cases` 에도 이 사례 id를 추가한다(양방향).
4. 없는 소재 카드는 backlog.md 에 추가만 한다.
5. `python scripts/build.py --test`, 결과 보고.
