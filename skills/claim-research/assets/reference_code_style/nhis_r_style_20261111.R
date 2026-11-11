# R 작성 방식 대표본: 원문과 별도로 만든 합성 예제
# 현재 연구의 SAP·스키마가 우선한다. 아래 열·코드는 NHIS 실제 정의가 아니다.
# 입력 → 키 QC → 연결 → 조건별 대입 → QC → 요약을 최상위 구문으로 둔다.
# 외부 입력·파일 출력·난수 없이 실행한다. data.table이 설치되어 있어야 한다.
# 매칭·생존분석·가중치·결측 대체 규칙은 해당 연구에서 따로 확정한다.

library(data.table)

# 1. 합성 입력: 기준표는 사람당 1행, 추가표는 사람당 최대 1행
base <- data.table(
    person_id = sprintf("demo_%02d", 1:8),
    group_code = c("A", "A", "A", "A", "B", "B", "B", "B"),
    measure = c(-1, 0, 1, NA_real_, 2, -2, 0, NA_real_)
)

# 합성 응답만의 정의: 1=예, 2=아니오, 9/NA=모름
# demo_04는 응답 결측, demo_07/08은 추가표 미매칭, demo_09는 기준표 밖
detail <- data.table(
    person_id = sprintf("demo_%02d", c(1:6, 9)),
    answer_code = c(1L, 2L, 9L, NA_integer_, 1L, 2L, 1L),
    detail_present = TRUE
)

# 2. 입력 QC: 키와 허용 코드를 확인한 뒤 연결
stopifnot(
    nrow(base) > 0L,
    !anyNA(base$person_id), !anyNA(detail$person_id),
    all(nzchar(base$person_id)), all(nzchar(detail$person_id)),
    anyDuplicated(base$person_id) == 0L,
    anyDuplicated(detail$person_id) == 0L,
    !anyNA(base$group_code), all(base$group_code %in% c("A", "B")),
    all(is.na(detail$answer_code) | detail$answer_code %in% c(1L, 2L, 9L))
)

qc_input <- data.table(
    table = c("base", "detail"),
    rows = c(nrow(base), nrow(detail)),
    people = c(uniqueN(base$person_id), uniqueN(detail$person_id))
)
print(qc_input)

# 3. 기준표 전체를 유지하는 1:1 연결; 미매칭은 삭제하지 않는다
joined <- detail[base, on = "person_id"]
qc_join <- joined[, .(
    rows = .N,
    people = uniqueN(person_id),
    matched = sum(!is.na(detail_present)),
    unmatched = sum(is.na(detail_present))
)]
qc_join[, detail_outside_base := detail[!base, on = "person_id", .N]]
print(qc_join)
stopifnot(
    nrow(joined) == nrow(base),
    uniqueN(joined$person_id) == nrow(base),
    identical(joined$person_id, base$person_id),
    identical(joined$measure, base$measure)
)

# 4. 파생변수: 이전 단계 객체를 보존하고 조건을 직접 쓴다
analysis <- copy(joined)
analysis[, answer_flag := NA_integer_]
analysis[answer_code == 1L, answer_flag := 1L]
analysis[answer_code == 2L, answer_flag := 0L]
# 9·응답 결측·미매칭은 NA 유지. 표 전체의 NA를 0으로 바꾸지 않는다.

analysis[, measure_class := NA_character_]
analysis[is.na(measure), measure_class := "missing"]
analysis[!is.na(measure) & measure < 0, measure_class := "negative"]
analysis[!is.na(measure) & measure == 0, measure_class := "zero"]
analysis[!is.na(measure) & measure > 0, measure_class := "positive"]

# 5. 파생변수 QC: 분기 누락과 모름→0 오변환을 확인
qc_answer <- analysis[, .N, by = .(answer_code, answer_flag)]
qc_measure <- analysis[, .N, by = measure_class]
print(qc_answer)
print(qc_measure)
stopifnot(
    !anyNA(analysis$measure_class),
    all(is.na(analysis$answer_flag) | analysis$answer_flag %in% c(0L, 1L)),
    analysis[(is.na(answer_code) | answer_code == 9L) & !is.na(answer_flag), .N] == 0L,
    analysis[measure == 0 & measure_class != "zero", .N] == 0L,
    !("answer_flag" %in% names(joined))
)

# 6. 요약: 전체·관측·결측 분모를 함께 남기고 0분모는 NA 유지
summary <- analysis[, .(
    people = .N,
    answer_known = sum(!is.na(answer_flag)),
    answer_missing = sum(is.na(answer_flag)),
    answer_yes = sum(answer_flag == 1L, na.rm = TRUE),
    measure_known = sum(!is.na(measure)),
    measure_missing = sum(is.na(measure)),
    measure_sum = sum(measure, na.rm = TRUE)
), by = group_code]
summary[, answer_yes_pct := NA_real_]
summary[answer_known > 0L, answer_yes_pct := 100 * answer_yes / answer_known]
summary[, measure_mean := NA_real_]
summary[measure_known > 0L, measure_mean := measure_sum / measure_known]
setorder(summary, group_code)
stopifnot(
    sum(summary$people) == nrow(analysis),
    all(summary$answer_known + summary$answer_missing == summary$people),
    all(summary$measure_known + summary$measure_missing == summary$people)
)
print(summary)

# 실제 연구에서는 승인된 입력 버전·코드 해시·실행 조건을 기존 로그에 기록
# 이 예제의 실행 성공은 실제 NHIS 분석·연구 결과 검증을 뜻하지 않는다.
sessionInfo()
