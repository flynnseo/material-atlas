---
description: 빌드 + 검색 테스트 + 커밋/푸시
---
1. `python scripts/build.py --test`
2. 오류가 있으면 멈추고 보고.
3. 없으면 변경된 카드 목록으로 커밋 메시지를 만든다: `atlas: +N 소재, +M 마감, ~K 수정` 형식.
4. `git add -A && git commit` 후 `git push`. 푸시하면 GitHub Actions가 사이트를 다시 배포한다.
