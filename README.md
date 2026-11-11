# claim-research

NHIS/국민건강보험공단·HIRA/심평원 청구자료의 SAS/R 추출, 분석, 오류 해결, 코호트 구성과 QC에 사용하는 스킬입니다. 기존 `claim-research`에 코드 작성 안내와 필요한 템플릿·정적 검사기를 함께 제공합니다. 기본 사용에 별도 학습 엔진이나 새 플러그인을 설치할 필요는 없습니다.

현재 프로젝트의 지침, 승인 연구계획/SAP와 실제 스키마를 우선합니다. HIRA, NHIS 원주 현지 추출, NHIS 제공자료·반출 후 분석의 경로를 구분하며, 제공된 SAS 테이블이라는 사실만으로 반출 허용이나 공통 스키마를 가정하지 않습니다.

## Codex에서 설치하기

Codex에 아래 내용을 붙여 넣으세요. 스킬 설치와 전역 적용 규칙의 병합을 함께 요청하는 프롬프트입니다.

```text
$skill-installer

다음 GitHub 경로의 claim-research 스킬을 설치해 주세요.
https://github.com/ZellKim/claim-research/tree/main/skills/claim-research

현재 설치된 같은 이름의 스킬과 실제 설치 위치를 먼저 확인해 주세요.
기존 설치가 있으면 내용을 백업하고 차이를 검토한 뒤 기존 스킬을 업데이트해 주세요.
기존 사용자 수정과 설치 관리 정보를 임의로 삭제하지 말고, 같은 이름의 설치본을 추가로 만들지 마세요.

다음 전역 적용 블록도 읽어 주세요.
https://github.com/ZellKim/claim-research/blob/main/global-rule_20261111.md

현재 CODEX_HOME의 AGENTS.md에 이 블록을 병합해 주세요.
CODEX_HOME이 설정되지 않았으면 현재 사용자의 기본 ~/.codex/AGENTS.md를 사용해 주세요.
AGENTS.override.md가 있으면 실제 적용되는 전역 지침과 기존 override 의도를 먼저 확인해 주세요.
기존 전역 지침을 백업하고, BEGIN CLAIM_RESEARCH_ROUTING과 END CLAIM_RESEARCH_ROUTING 사이의 블록만 추가하거나 갱신해 주세요.
다른 규칙은 그대로 보존하고 전역 파일 전체를 덮어쓰지 마세요.
기존 규칙과 충돌하거나 관리 블록이 중복되어 있으면 자동 병합하지 말고 해당 차이를 알려 주세요.

설치 위치, 변경한 파일, 확인한 범위와 추가 확인이 필요한 항목을 알려 주세요.
```

스킬 설치만으로 전역 AGENTS.md가 변경되는 것은 아닙니다. [전역 적용 블록](global-rule_20261111.md)은 관련 연구 작업에서 스킬을 먼저 읽도록 하는 짧은 지침입니다. 개인 컴퓨터의 절대경로를 이 블록에 넣을 필요는 없습니다.

Codex는 스킬 변경을 자동으로 감지합니다. 목록에 나타나지 않으면 재시작하세요. 전역 지침 변경은 새 세션에서 적용 여부를 확인하세요. [공식 스킬 안내](https://learn.chatgpt.com/docs/build-skills), [공식 AGENTS.md 안내](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

## 수동 설치 또는 업데이트

`skills/claim-research/` 전체를 아래 위치에 복사합니다. `SKILL.md`, `agents/`, `references/`, `assets/`, `scripts/`를 함께 유지해야 내부 상대경로가 이어집니다.

| 환경 | 사용자별 설치 위치 |
|---|---|
| Codex | `~/.agents/skills/claim-research/` |
| Claude Code | `~/.claude/skills/claim-research/` |

`~`는 각 컴퓨터의 현재 사용자 홈입니다. 이미 설치되어 있으면 먼저 백업·차이 검토를 거쳐 업데이트하세요. Codex의 전역 적용은 위 프롬프트 또는 [전역 적용 블록](global-rule_20261111.md)으로 별도 병합합니다. Claude Code 설치 위치에 Codex의 전역 AGENTS.md를 복사하지 않습니다.

## 포함된 자료와 사용 순서

1. [SKILL.md](skills/claim-research/SKILL.md)에서 자료원과 작업 단계를 선택합니다.
2. 현재 프로젝트의 코드 작성 안내를 읽습니다. 별도 안내가 없으면 SKILL.md의 탐색 순서에 따라 접근 가능한 관리 라이브러리를 확인하고, 없으면 [번들 코드생성 안내](skills/claim-research/references/code-generation_20261111.md)를 사용합니다.
3. 선택한 경로의 `references/`를 읽습니다. **NHIS 제공 SAS 테이블 가공**은 [150줄 SAS 스타일 대표본](skills/claim-research/assets/reference_code_style/nhis_sas_style_20261111.txt)을 먼저 참고합니다. 짧은 목적 주석, 직접 SQL/DATA, 즉시 QC와 작은 반복 매크로를 WORK 합성 자료로 보여 줍니다. 오류 중단·진행 표시 등 추가 QC 구현은 [30 WORK 모의자료 템플릿](skills/claim-research/assets/sas_templates/30_NHIS_proc_sql_block_qc_template.txt)에서 필요한 부분을 확인합니다. R 작성 방식은 번들 코드생성 안내의 합성 예제를 참고합니다.
4. [SAS 정적 검사기](skills/claim-research/scripts/validate_sas_preflight.py)는 해당 프로젝트의 요구에 맞는 정확한 전달 파일에 적용합니다. 사용 방법과 적용 범위는 번들 코드생성 안내를 따릅니다. [검사기 테스트](skills/claim-research/scripts/tests/test_validate_sas_preflight.py)는 정적 검사 기능을 확인하기 위한 자료입니다.

템플릿은 연구기간·대상자·변수·코드셋·분석모형의 승인 근거가 아닙니다. 모의자료 예제는 실제 연구 데이터에 대한 검증을 대신하지 않습니다. 정적 검사 통과, SAS/R 실행 성공, 실제 결과의 정확성과 재현성 확인을 구분하고 수행하지 못한 검증은 명시합니다.

기존 자료원별 의미·근거·QC 참조를 함께 보존합니다. 학습 관련 참조도 포함하지만, 별도 학습 엔진은 기본 사용의 의존성이 아닙니다. 설치만으로 연구 실행이나 학습 작업을 예약·시작하지 않습니다.

## 공통 기능과 연구별 자료의 경계

번들은 자료원 선택, 코드 작성 원칙, WORK 모의자료 템플릿과 정적 검사를 제공합니다. 로컬 연구 라이브러리에서 관리하는 **원주 추출 17파일, 연구별 예제 25파일과 원문 Word의 읽기용 분할본은 포함하지 않습니다.** 새 SAS 스타일 대표본은 원문의 작성 패턴을 합성 자료로 재구성한 독립 예제이며, 원문이나 분할본 없이 사용할 수 있습니다. 00·10·20 SAS 템플릿도 배포하지 않습니다. 실제 서버 설정·추출 조건·연구 정의가 필요한 작업은 현재 프로젝트의 승인 자료와 로컬 라이브러리를 확인해야 합니다.

연구별 코드가 필요할 때는 프로젝트 안내가 가리키는 자료만 찾아 참고합니다. 예제의 연구기간·서버 경로·대상자 필터·삭제 구문을 그대로 채택하지 않으며, 로컬 자료가 없다는 이유로 전체 Drive를 검색하지 않습니다. 필요한 환경·스키마·승인 기준이 없으면 그 정보에 의존하는 실행 코드를 확정하지 않습니다.

## 공개 범위

이 저장소는 재사용 가능한 스킬과 코드 작성·검증 자료를 배포합니다. 연구 원자료, 연구별 완성 산출물, 개인 컴퓨터의 경로 설정은 배포 대상이 아닙니다. 설치 환경에서 생성되는 `runtime-context.json`과 `.canonical-manifest.json`도 공개 번들에 포함하지 않습니다.

