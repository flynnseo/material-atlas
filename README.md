# MATERIAL ATLAS

소재·마감·사례·실험 카드 위키. 원본은 Markdown, 보는 화면은 `site/index.html` 한 장.

## 처음 한 번
```bash
pip install -r requirements.txt
python scripts/build.py --test      # mac: python3
```
→ `site/index.html` 더블클릭. 오프라인에서도 열린다.

## 어디서든 열기
GitHub에 push → Actions가 빌드해서 GitHub Pages에 올린다. 폰·다른 컴퓨터에서 Pages 주소로 바로.
(레포 Settings → Pages → Source: **GitHub Actions** 한 번 설정)

## 검색이 하는 일
| 쳐도 되는 것 | 예 |
| --- | --- |
| 오타 | 알루미눔, 아크릭 |
| 은어·현장 용어 | 스뎅, 서스, 알루마이트, 결무늬 |
| 초성 | ㅇㄹㅁㄴ |
| 영문·규격 | aluminum, 6061, SUS304 |
| 속성 조합 | 무광 금속, 투명 판재, 골드 코팅 스텐 |
| 조사 붙여서 | 알루미늄으로 선반 |

직접 맞은 카드 아래에 **연결된 자료**(마감↔소재↔사례 링크, 태그가 비슷한 카드)가 같이 뜬다.
못 찾은 검색어는 Claude Code에 `/search-tune 검색어 => 원했던 카드` 로 넘기면 고치고 테스트에 추가한다.

## 단축키
`/` 검색창 · `↑↓` 결과 이동 · `Enter` 열기 · `Esc` 지우기
