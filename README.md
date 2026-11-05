# Design Library

디자인 자료를 모으고, 미리보기와 검색으로 다시 꺼내 보는 개인 라이브러리입니다. 디자인 레퍼런스 맥락에서 웹사이트 URL을 주면 에이전트가 원본을 관찰해 `DESIGN.md`, 디자인 토큰과 작은 재사용 화면을 만들고 검증합니다. “저장만” 요청과 아이콘/라이브러리/자료/UX 규칙/소셜 링크 수집은 가볍게 저장하며 메모와 분류는 나중에 해도 됩니다.

[사이트 디자인 추출 절차](.agents/skills/design-library-gallery/references/extraction.md)는 실제 브라우저 관찰, 토큰별 근거와 두 화면 너비의 새 화면 비교를 요구합니다. 차단된 사이트나 캡처만 있는 입력은 확인 범위를 적은 부분 결과로 남깁니다. `new`는 초안 생성기, `collect`는 저장 명령이며 이 명령 자체가 사이트를 분석하지는 않습니다.

## 다섯 분류와 수집함

| 분류 | 모아둘 자료 |
|---|---|
| 디자인 레퍼런스 | 사이트, 앱 화면, 레이아웃, 사용자 흐름과 모션 |
| UI 컴포넌트/라이브러리 | 화면 구현에 가져다 쓸 컴포넌트와 도구 |
| 아이콘/에셋 | 아이콘, 폰트, 일러스트 등의 소재 |
| 디자인 시스템 | 색상, 서체, 간격, 토큰과 사용 지침 |
| UX 규칙 | 탐색, 입력, 피드백, 오류 복구, 접근성과 문구 원칙 |
| 수집함 | 아직 분류하지 않은 링크나 이미지 |

기록 원본은 `references/<id>/reference.json`입니다. 제목, 원본 URL, 분류, 태그와 짧은 메모를 저장합니다. 이미지 미리보기는 `.reference-previews/`에 따로 보관하며 Git 원격과 공개 빌드에는 포함하지 않습니다. 이미지 파일은 로컬 백업에 포함해야 합니다. 기존 상세 설명과 UI 추출 패키지의 `DESIGN.md`, `tokens.json`, 프로토타입은 유지합니다.

첫 읽기 기록에는 제공받은 여섯 X 게시물과 연결된 자료를 담았습니다. 라이브러리, 프롬프트 모음과 에이전트 스킬의 차이, 작성자의 주장과 직접 확인한 사실을 구분합니다. Radix, WAI-ARIA, DTCG, GOV.UK 공식 문서도 함께 기록했습니다. 각 원문과 확인일은 개별 기록에서 볼 수 있습니다.

Lucide, Phosphor, Land-book, Mobbin, Laws of UX, Nielsen의 사용성 원칙도 가벼운 저장 형식으로 담았습니다. 수집함에는 원 게시물에서 발견한 Font in Logo를 보관했습니다. 상세 분석이나 실행 검증은 저장의 필수 조건이 아닙니다.

[저장소](https://github.com/seungwonme/design-library) / [갤러리 열기](https://seungwonme.github.io/design-library/) / [프로젝트 스킬](.agents/skills/design-library-gallery/SKILL.md) / [Aside 디자인 규칙](references/aside-glass/DESIGN.md)

## REA, taste-skill, prototype

| 단계 | 역할 | 실행 가이드 |
|---|---|---|
| REA | 앱/ASAR/웹의 구조와 소스 근거를 분석하고 실제 화면 측정과 대조 | [REA 기반 추출](.agents/skills/design-library-gallery/references/rea-extraction.md) |
| taste-skill | 마케팅 페이지의 시각 방향 또는 기존 앱의 개선 항목 선택 | [용도별 Taste 적용](.agents/skills/design-library-gallery/references/taste-and-prototype.md) |
| Matt Pocock prototype | 같은 콘텐츠로 구조가 다른 화면을 비교하고 선택 이유를 보관 | [프로토타입 비교](.agents/skills/design-library-gallery/references/taste-and-prototype.md#prototype을-공통-비교-절차로-쓰기) |

프로젝트 스킬에 도구 선택, 실제 호출, 결과 정리와 미설치 시 대체 절차를 포함했습니다. REA MCP와 Taste/prototype은 현재 하네스에 설치된 도구와 스킬을 확인해 사용합니다. 설치와 원본 문서는 [REA](https://github.com/morluto/rea), [taste-skill](https://github.com/leonxlnx/taste-skill), [Matt Pocock skills](https://github.com/mattpocock/skills)에서 확인할 수 있습니다.

Taste 기본 v2의 웹 아트 디렉션과 앱/대시보드 개선을 구분합니다. 원본의 색/서체/컴포넌트 규칙과 기존 스택을 우선하며, 사진이나 특정 화면의 배치를 디자인 시스템의 필수 요소로 가져오지 않습니다.

## 프로젝트 스킬

프로젝트 스킬은 `design-library-gallery` 하나입니다. 전역 `design-library`와 이름이 충돌하지 않도록 호출명을 구분했으며, 본문부터 테스트까지 전체 묶음을 포함합니다.

```text
.agents/skills/design-library-gallery/
├── SKILL.md
├── README.md
├── references/    # 설정, REA 추출, Taste/prototype, 계약과 발행
├── scripts/       # 생성, 검증, 빌드, GitHub 발행
├── assets/        # 빈 설정, 토큰/메타데이터 템플릿, 갤러리와 Actions
└── tests/         # 행동 검사와 평가 기록

references/<id>/
├── reference.json # 모든 기록의 원본
├── index.html     # 추출 패키지의 미리보기, 단순 기록은 빌드 때 생성
├── DESIGN.md      # 직접 추출했을 때의 사용 규칙
├── tokens.json    # 직접 추출했을 때의 수치
└── assets/        # 공개가 승인된 추출 자산

.reference-previews/ # 로컬 전용 캡처/이미지, Git 무시 대상
```

저장소를 작업 폴더로 연 뒤 다음 이름으로 호출할 수 있습니다.

- Codex: `$design-library-gallery`
- Claude Code: `/design-library-gallery`
- GJC: `/skill:design-library-gallery`

Claude Code의 `.claude/skills/design-library-gallery`와 GJC의 `.gjc/skills`는 저장소 안의 정본을 가리키는 상대 링크입니다. Codex는 `.agents/skills/`에서 직접 읽습니다. 실제 사용자 설정과 원본 레퍼런스 자산은 스킬 폴더 밖에 둡니다.

## 로컬 사용

Python 3.10+, uv와 Git이 필요하며, GitHub 발행에는 인증된 `gh`를 사용합니다.

```sh
uv --no-config run --locked --script scripts/gallery.py --help
uv --no-config run --locked --script scripts/gallery.py doctor
uv --no-config run --locked --script scripts/gallery.py collect <id> --source <url> --title <title>
uv --no-config run --locked --script scripts/gallery.py view
```

명령은 저장소 루트에서 실행합니다. `collect`의 기본 분류는 수집함입니다. `--image <path>`로 이미지만 저장하거나 링크에 캡처를 붙일 수 있습니다. 직접 적은 UX 규칙은 URL 없이 `--title`과 `--note`만으로 저장할 수 있습니다. `view`가 출력하는 URL을 브라우저에서 열면 미공개 자료와 로컬 이미지까지 보입니다. 서버는 Ctrl-C로 종료하며, 새 자료를 저장한 뒤 `view`를 다시 실행하면 새 목록을 만듭니다. 래퍼는 이 checkout을 직접 선택합니다.

디자인 시스템을 재사용할 때는 글꼴, 의미 색상, 간격과 컴포넌트 규칙을 대상 서비스에 맞게 적용합니다. 원본 사진과 특정 화면 배치는 재현 요청이나 대상 콘텐츠에 필요한 경우에 사용합니다.

검증 명령 `check`는 회귀 테스트, 전체 패키지의 공식 토큰 스키마/별칭/CSS 검사와 임시 공개 빌드를 수행합니다. 실제 시각 검수와 모델의 스킬 선택 평가는 별도입니다.

## 수정과 발행

링크/이미지를 수집할 때는 [수집과 열람 절차](.agents/skills/design-library-gallery/references/design-book.md)를 따릅니다.

```sh
uv --no-config run --locked --script scripts/gallery.py collect <id> --source <url> --category asset --tag SVG --note <memo>
```

`collect`는 저장만 하며 commit/push나 공개 발행을 하지 않습니다. 공개할 링크와 메모는 별도 검토합니다. 도구와 생성 파일을 갱신할 때는 기능 worktree에서 `bundle --project-skill --apply`를 사용합니다. 공개는 기존 `publish`/`finish` 절차를 따릅니다.

레퍼런스의 값은 `tokens.json`, 사용 규칙은 `DESIGN.md`, 출처와 검증 범위는 `reference.json`에서 관리합니다. 갤러리 자체의 테마는 루트 `gallery.css`에 있습니다.

```sh
uv --no-config run --locked --script scripts/gallery.py validate <id> --ready --public
uv --no-config run --locked --script scripts/gallery.py publish references/<id>
uv --no-config run --locked --script scripts/gallery.py publish references/<id> --apply
```

기본 `publish`는 계획만 출력합니다. `--apply`는 별도 worktree에서 공개 파일과 전체 스킬 묶음을 준비하고 PR과 CI 빌드까지 진행합니다. 리뷰 후 머지까지 승인된 작업에는 `--merge`를 추가할 수 있으며, Actions 배포와 실제 Pages의 커밋을 확인합니다. 중단된 발행은 `finish --pr <number> --entry <id> --apply`로 이어갈 수 있습니다.

루트 래퍼는 프로젝트 스킬의 코드를 우선 실행합니다. `.design-library/`는 호환 런타임과 생성 파일의 버전/hash 기록을 담습니다. 발행 스크립트가 프로젝트 묶음과 런타임을 같은 원본으로 갱신하므로 생성 사본을 각각 편집할 필요가 없습니다.

```sh
uv --no-config run --locked --script scripts/gallery.py check
```
