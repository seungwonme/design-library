# Design Book / UI References

UI 라이브러리, 디자인 지침, 디자인 시스템과 토큰, UI/UX 흐름을 찾아보고 재사용하기 위한 디자인 북입니다. 각 기록에는 추천 이유, 적용 조건, 피할 조건, 출처와 확인 범위를 남깁니다. 기존 UI 추출 패키지의 토큰과 실행 가능한 미리보기도 함께 보관합니다.

## 네 장과 두 가지 기록

| 장 | 다루는 질문 |
|---|---|
| UI 라이브러리 | 어떤 문제를 해결하고, 어떤 스택과 도입 조건에 맞는가? |
| 디자인 지침 | 어떤 판단이 도움이 되며, 반례와 예외는 무엇인가? |
| 디자인 시스템과 토큰 | 값과 의미, 테마와 상태가 어떻게 연결되는가? |
| UI/UX 흐름 | 시작, 성공, 수정, 오류와 복귀가 어떻게 이어지는가? |

읽기 기록은 `reference.json`에 평가를 쓰고 빌드가 읽기 페이지를 만듭니다. UI 추출 패키지는 기존 `DESIGN.md`, `tokens.json`, 프로토타입을 유지합니다. 문서 확인, 직접 검증, 추출 패키지는 검색 필터와 화면에서 구분합니다. 초안은 공개 빌드에서 제외됩니다.

첫 읽기 기록에는 제공받은 여섯 X 게시물과 연결된 자료를 담았습니다. 라이브러리, 프롬프트 모음과 에이전트 스킬의 차이, 작성자의 주장과 직접 확인한 사실을 구분합니다. Radix, WAI-ARIA, DTCG, GOV.UK 공식 문서도 함께 기록했습니다. 각 원문과 확인일은 개별 기록에서 볼 수 있습니다.

[갤러리 열기](https://seungwonme.github.io/ui-references/) / [프로젝트 스킬](.agents/skills/reference-ui-gallery/SKILL.md) / [Aside 디자인 규칙](references/aside-glass/DESIGN.md)

## REA, taste-skill, prototype

| 단계 | 역할 | 실행 가이드 |
|---|---|---|
| REA | 앱/ASAR/웹의 구조와 소스 근거를 분석하고 실제 화면 측정과 대조 | [REA 기반 추출](.agents/skills/reference-ui-gallery/references/rea-extraction.md) |
| taste-skill | 마케팅 페이지의 시각 방향 또는 기존 앱의 개선 항목 선택 | [용도별 Taste 적용](.agents/skills/reference-ui-gallery/references/taste-and-prototype.md) |
| Matt Pocock prototype | 같은 콘텐츠로 구조가 다른 화면을 비교하고 선택 이유를 보관 | [프로토타입 비교](.agents/skills/reference-ui-gallery/references/taste-and-prototype.md#prototype을-공통-비교-절차로-쓰기) |

프로젝트 스킬에 도구 선택, 실제 호출, 결과 정리와 미설치 시 대체 절차를 포함했습니다. REA MCP와 Taste/prototype은 현재 하네스에 설치된 도구와 스킬을 확인해 사용합니다. 설치와 원본 문서는 [REA](https://github.com/morluto/rea), [taste-skill](https://github.com/leonxlnx/taste-skill), [Matt Pocock skills](https://github.com/mattpocock/skills)에서 확인할 수 있습니다.

Taste 기본 v2의 웹 아트 디렉션과 앱/대시보드 개선을 구분합니다. 원본의 색/서체/컴포넌트 규칙과 기존 스택을 우선하며, 사진이나 특정 화면의 배치를 디자인 시스템의 필수 요소로 가져오지 않습니다.

## 프로젝트 스킬

프로젝트 스킬은 `reference-ui-gallery` 하나입니다. 전역 `reference-ui`와 이름이 충돌하지 않도록 호출명을 구분했으며, 본문부터 테스트까지 전체 묶음을 포함합니다.

```text
.agents/skills/reference-ui-gallery/
├── SKILL.md
├── README.md
├── references/    # 설정, REA 추출, Taste/prototype, 계약과 발행
├── scripts/       # 생성, 검증, 빌드, GitHub 발행
├── assets/        # 빈 설정, 토큰/메타데이터 템플릿, 갤러리와 Actions
└── tests/         # 행동 검사와 평가 기록

references/<id>/
├── index.html
├── DESIGN.md
├── tokens.json
├── reference.json
└── assets/        # 해당 레퍼런스가 사용하는 공개 자산
```

저장소를 작업 폴더로 연 뒤 다음 이름으로 호출할 수 있습니다.

- Codex: `$reference-ui-gallery`
- Claude Code: `/reference-ui-gallery`
- GJC: `/skill:reference-ui-gallery`

Claude Code의 `.claude/skills/reference-ui-gallery`와 GJC의 `.gjc/skills`는 저장소 안의 정본을 가리키는 상대 링크입니다. Codex는 `.agents/skills/`에서 직접 읽습니다. 실제 사용자 설정과 원본 레퍼런스 자산은 스킬 폴더 밖에 둡니다.

## 로컬 사용

Python 3.10+, uv와 Git이 필요하며, GitHub 발행에는 인증된 `gh`를 사용합니다.

```sh
uv --no-config run --locked --script scripts/gallery.py --help
uv --no-config run --locked --script scripts/gallery.py doctor
uv --no-config run --locked --script scripts/gallery.py catalog --public
uv --no-config run --locked --script scripts/gallery.py build --output ./site-preview
python3 -m http.server --directory ./site-preview
```

명령은 저장소 루트에서 실행합니다. 빌드 출력은 새 폴더나 빈 폴더를 지정합니다. 래퍼가 이 checkout을 직접 선택하므로 개인 설정 파일 없이도 실행할 수 있습니다.

디자인 시스템을 재사용할 때는 글꼴, 의미 색상, 간격과 컴포넌트 규칙을 대상 서비스에 맞게 적용합니다. 원본 사진과 특정 화면 배치는 재현 요청이나 대상 콘텐츠에 필요한 경우에 사용합니다.

검증 명령 `check`는 회귀 테스트, 전체 패키지의 공식 토큰 스키마/별칭/CSS 검사와 임시 공개 빌드를 수행합니다. 실제 시각 검수와 모델의 스킬 선택 평가는 별도입니다.

## 수정과 발행

링크/문서를 수집할 때는 [디자인 북 절차](.agents/skills/reference-ui-gallery/references/design-book.md)를 따릅니다.

```sh
uv --no-config run --locked --script scripts/gallery.py note <id> --title <title> --source <url> --platform web --category guideline
```

`note`는 미확인 초안을 만들며 토큰이나 실행 증거를 생성하지 않습니다. 사용 조건과 출처를 작성한 뒤 `validate --ready`로 검사합니다. 도구와 생성 파일을 갱신할 때는 격리된 기능 worktree에서 `bundle --project-skill --apply`를 사용합니다. 공개는 기존 `publish`/`finish` 절차를 따릅니다.

레퍼런스의 값은 `tokens.json`, 사용 규칙은 `DESIGN.md`, 출처와 검증 범위는 `reference.json`에서 관리합니다. 갤러리 자체의 테마는 루트 `gallery.css`에 있습니다.

```sh
uv --no-config run --locked --script scripts/gallery.py validate <id> --ready --public
uv --no-config run --locked --script scripts/gallery.py publish references/<id>
uv --no-config run --locked --script scripts/gallery.py publish references/<id> --apply
```

기본 `publish`는 계획만 출력합니다. `--apply`는 별도 worktree에서 공개 파일과 전체 스킬 묶음을 준비하고 PR과 CI 빌드까지 진행합니다. 리뷰 후 머지까지 승인된 작업에는 `--merge`를 추가할 수 있으며, Actions 배포와 실제 Pages의 커밋을 확인합니다. 중단된 발행은 `finish --pr <number> --entry <id> --apply`로 이어갈 수 있습니다.

루트 래퍼는 프로젝트 스킬의 코드를 우선 실행합니다. `.reference-ui/`는 호환 런타임과 생성 파일의 버전/hash 기록을 담습니다. 발행 스크립트가 프로젝트 묶음과 런타임을 같은 원본으로 갱신하므로 생성 사본을 각각 편집할 필요가 없습니다.

```sh
uv --no-config run --locked --script scripts/gallery.py check
```
