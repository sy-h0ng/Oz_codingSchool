# 2일차 Git Branch 전략

## 1. Git Branch 전략이 필요한 이유

Git branch 전략은 여러 명의 개발자가 같은 프로젝트에서 동시에 작업할 때 코드 충돌과 배포 위험을 줄이기 위한 협업 규칙이다.  
각 기능, 버그 수정, 배포 준비 작업을 독립된 branch에서 진행하면 `main` branch의 안정성을 유지하면서 작업 내역을 추적할 수 있다.

Branch 전략을 사용하면 다음과 같은 장점이 있다.

- 기능별 작업 범위를 분리할 수 있다.
- Pull Request를 통해 코드 리뷰를 진행할 수 있다.
- 배포 가능한 코드와 개발 중인 코드를 구분할 수 있다.
- 문제가 생겼을 때 특정 branch나 commit 단위로 원인을 추적하기 쉽다.

대표적인 branch 전략으로는 **Git Flow**와 **GitHub Flow**가 있다.

## 2. Git Flow

Git Flow는 Vincent Driessen이 제안한 branch 전략으로, 출시 버전과 개발 버전을 명확히 나누는 방식이다.  
Atlassian의 Gitflow Workflow 설명에 따르면 Git Flow는 `main` branch와 `develop` branch를 중심으로, 기능 개발, 출시 준비, 긴급 수정 등을 별도 branch에서 관리한다.

### 2.1 주요 Branch

| Branch | 역할 |
| --- | --- |
| `main` | 실제 배포 가능한 공식 release 이력을 저장하는 branch |
| `develop` | 다음 배포 버전을 위해 기능들이 통합되는 개발 branch |
| `feature/*` | 새로운 기능을 개발하는 branch |
| `release/*` | 배포 전 테스트, 문서 정리, 버그 수정을 진행하는 branch |
| `hotfix/*` | 운영 중인 `main` branch에서 긴급 버그를 수정하는 branch |

### 2.2 Git Flow 작업 흐름

1. `main`에서 `develop` branch를 만든다.
2. 새로운 기능은 `develop`에서 `feature/*` branch를 만들어 개발한다.
3. 기능 개발이 끝나면 `feature/*` branch를 `develop`에 병합한다.
4. 배포 시점이 되면 `develop`에서 `release/*` branch를 만든다.
5. 배포 준비가 끝나면 `release/*` branch를 `main`과 `develop`에 병합한다.
6. 운영 중 긴급 수정이 필요하면 `main`에서 `hotfix/*` branch를 만든다.
7. 수정 완료 후 `hotfix/*` branch를 `main`과 `develop`에 병합한다.

### 2.3 Git Flow 장점

- 배포 버전과 개발 버전을 명확히 구분할 수 있다.
- 정기적인 release가 있는 프로젝트에 적합하다.
- 긴급 수정용 `hotfix` branch가 있어 운영 대응이 체계적이다.
- 여러 기능이 동시에 개발되는 대규모 팀에서 작업 흐름을 관리하기 좋다.

### 2.4 Git Flow 단점

- branch 종류가 많아 초보자에게 복잡하게 느껴질 수 있다.
- 작은 프로젝트나 빠른 배포가 필요한 프로젝트에서는 관리 비용이 커질 수 있다.
- `develop`, `release`, `hotfix` 등 여러 branch를 지속적으로 동기화해야 한다.

## 3. GitHub Flow

GitHub Flow는 GitHub 공식 문서에서 소개하는 가벼운 branch 기반 협업 방식이다.  
기본 아이디어는 `main` branch를 항상 배포 가능한 상태로 유지하고, 모든 변경 사항은 별도의 branch에서 작업한 뒤 Pull Request를 통해 병합하는 것이다.

### 3.1 주요 Branch

| Branch | 역할 |
| --- | --- |
| `main` | 항상 배포 가능한 안정적인 branch |
| `feature/*` 또는 작업 branch | 기능 개발, 버그 수정, 문서 수정 등을 진행하는 branch |

GitHub Flow에서는 Git Flow처럼 `develop`, `release`, `hotfix` branch를 고정적으로 사용하지 않는다.  
작업 단위마다 branch를 만들고, 리뷰와 테스트를 거친 뒤 `main`에 병합한다.

### 3.2 GitHub Flow 작업 흐름

1. 최신 `main` branch에서 새로운 작업 branch를 만든다.
2. 작업 branch에서 기능 개발, 버그 수정, 문서 수정을 진행한다.
3. 작업 내용을 commit하고 원격 저장소에 push한다.
4. Pull Request를 생성한다.
5. 팀원 리뷰와 테스트를 진행한다.
6. 문제가 없으면 `main` branch에 merge한다.
7. 필요하면 `main` branch를 기준으로 배포한다.

### 3.3 GitHub Flow 장점

- branch 구조가 단순해서 배우기 쉽다.
- Pull Request 중심으로 협업하기 좋다.
- 빠른 수정과 배포가 필요한 프로젝트에 적합하다.
- `main`을 항상 배포 가능한 상태로 유지하는 데 집중할 수 있다.

### 3.4 GitHub Flow 단점

- `main` branch 안정성을 지키기 위한 테스트와 리뷰 규칙이 중요하다.
- 정기 release, 장기 유지보수 버전, 복잡한 배포 단계를 가진 프로젝트에는 부족할 수 있다.
- 팀이 Pull Request 리뷰를 소홀히 하면 불안정한 코드가 `main`에 들어갈 위험이 있다.

## 4. Git Flow와 GitHub Flow 비교

| 구분 | Git Flow | GitHub Flow |
| --- | --- | --- |
| 구조 | 복잡함 | 단순함 |
| 핵심 branch | `main`, `develop` | `main` |
| 보조 branch | `feature`, `release`, `hotfix` | 작업 단위 branch |
| 적합한 프로젝트 | 정기 release, 운영 버전 관리가 필요한 프로젝트 | 빠른 개발과 배포가 필요한 프로젝트 |
| 장점 | 배포 단계가 명확하고 안정적 | 이해하기 쉽고 빠르게 적용 가능 |
| 단점 | 관리 비용이 높음 | 리뷰와 테스트가 약하면 `main` 안정성이 낮아질 수 있음 |

## 5. 팀 프로젝트에서의 적용 방안

현재 학습 목적의 웹개발 프로젝트에서는 **GitHub Flow**를 우선 적용하는 것이 적합하다고 판단한다.

이유는 다음과 같다.

- 팀원이 branch 전략을 처음 익히는 단계라면 단순한 흐름이 더 적합하다.
- `main` branch와 기능 branch만으로도 기능 개발, 리뷰, 병합 과정을 충분히 연습할 수 있다.
- 문서 수정, UI 개발, 기능 추가처럼 작은 단위의 작업을 Pull Request로 관리하기 좋다.
- 빠른 피드백과 반복 개발이 필요한 초기 웹 프로젝트에 잘 맞는다.

단, 프로젝트가 커지고 실제 배포 버전 관리가 필요해지면 Git Flow 또는 Git Flow의 일부 개념인 `release/*`, `hotfix/*` branch 도입을 검토할 수 있다.

## 6. 우리 팀 Branch 규칙 제안

우리 팀은 우선 다음 규칙으로 branch를 관리한다.

### 6.1 기본 Branch

- `main`: 최종 결과물이 유지되는 branch
- 작업 branch: 기능, 문서, 수정 작업을 수행하는 branch

### 6.2 Branch 이름 규칙

| 작업 유형 | Branch 예시 |
| --- | --- |
| 기능 개발 | `feature/login-page` |
| 문서 작성 | `docs/git-branch-strategy` |
| 버그 수정 | `fix/header-layout` |
| 스타일 수정 | `style/main-page-css` |

### 6.3 작업 순서

1. `main` branch를 최신 상태로 가져온다.
2. 작업 목적에 맞는 branch를 만든다.
3. 작업을 완료하고 commit한다.
4. 원격 저장소에 branch를 push한다.
5. Pull Request를 생성한다.
6. 팀원 리뷰 후 `main` branch에 merge한다.
7. merge 후 작업 branch를 삭제한다.

### 6.4 Commit 메시지 예시

| 유형 | 예시 |
| --- | --- |
| 문서 작성 | `docs: git branch 전략 정리` |
| 기능 추가 | `feat: 로그인 페이지 추가` |
| 버그 수정 | `fix: 헤더 메뉴 정렬 오류 수정` |
| 스타일 수정 | `style: 메인 페이지 여백 조정` |

## 7. 결론

Git Flow와 GitHub Flow는 모두 협업과 버전 관리를 안정적으로 하기 위한 branch 전략이다.  
Git Flow는 release 관리가 중요한 프로젝트에 적합하고, GitHub Flow는 단순하고 빠른 협업이 필요한 프로젝트에 적합하다.

우리 팀은 초기 웹개발 프로젝트 단계에서는 GitHub Flow를 사용하고, 프로젝트 규모가 커지거나 배포 관리가 복잡해질 경우 Git Flow의 일부 전략을 추가로 도입하는 방향이 적절하다.
