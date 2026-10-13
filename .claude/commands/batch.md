---
description: backlog에서 한 소재군 10개를 한 번에 draft 카드로
argument-hint: <family> [개수=10]
---
`_meta/backlog.md` 에서 "$ARGUMENTS" 소재군의 체크 안 된 항목을 위에서부터 최대 10개(두 번째 인자가 있으면 그 수) 가져온다.
각 항목에 대해 /add-material 과 같은 규칙으로 카드를 만들고 backlog에서 체크(`- [x]`)한다.
끝나면 `python scripts/build.py --test` 를 돌리고 표로 보고: id | 이름 | confidence | 출처 수 | 불확실한 점.
