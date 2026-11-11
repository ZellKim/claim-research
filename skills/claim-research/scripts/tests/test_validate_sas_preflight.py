"""Synthetic tests only; no SAS engine or production research data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'validate_sas_preflight.py'
spec = importlib.util.spec_from_file_location('sas_preflight', MODULE)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class PreflightChecks(unittest.TestCase):
    def findings(self, source):
        return preflight.inspect(source, 'fixture.sas')

    def test_put_trailing_prose(self):
        rows = self.findings('%put NOTE: done; unintended prose;')
        self.assertEqual([(r['rule'], r['severity']) for r in rows], [('ISS-048', 'REVIEW')])

    def test_put_legal_next_statement_and_macro_quote(self):
        self.assertEqual(self.findings('%put NOTE: done; run;'), [])
        rows = self.findings('%put %nrstr(a;b);')
        self.assertEqual([(r['rule'], r['severity']) for r in rows], [('ISS-048', 'REVIEW')])

    def test_comments_and_strings_are_not_executable_keywords(self):
        text = "/* create table wom ms.x as select 1; */\n* libname ms 'x';\n%* ods output X=ms.x;\ndata x; x='create table wom ms.x as select 1;'; run;"
        self.assertEqual(self.findings(text), [])
        self.assertEqual(self.findings('%put NOTE: create table wom ms.x as text;'), [])

    def test_groupby_without_aggregate_is_review(self):
        rows = self.findings('proc sql; create table work.x as select a from y group by a; quit;')
        self.assertEqual([(r['rule'], r['severity']) for r in rows], [('ISS-049', 'REVIEW')])

    def test_aggregate_and_having_do_not_trigger_groupby_review(self):
        for source in ['select a,sum(b) from y group by a;',
                       'select a from y group by a having count(*)>1;']:
            self.assertEqual(self.findings(source), [])

    def test_subquery_aggregate_does_not_hide_outer_candidate(self):
        rows = self.findings('select a,(select sum(b) from z) as b from y group by a;')
        self.assertEqual(rows[0]['rule'], 'ISS-049')
        self.assertEqual(rows[0]['severity'], 'REVIEW')

    def test_libname_candidate_but_not_function(self):
        self.assertEqual(self.findings("libname ms '/tmp';")[0]['severity'], 'REVIEW')
        self.assertEqual(self.findings("data _null_; rc=libname('MS',p); run;"), [])

    def test_invalid_create_target(self):
        rows = self.findings('create table wom ms.invalid_target as select x from y;')
        self.assertEqual((rows[0]['rule'], rows[0]['severity']), ('ISS-051', 'ERROR'))

    def test_legal_create_as_like_schema_options(self):
        for source in ['create table work.x as select x from y;',
                       'create table work.x like work.y;',
                       'create table work.x (x num, y char(8));',
                       'create table work.x(compress=yes) as select x from y;']:
            self.assertEqual(self.findings(source), [])

    def test_macro_and_name_literal_targets_are_only_review(self):
        for source in ['create table &lib..x as select x from y;',
                       'create table work.&member as select x from y;',
                       "create table work.'member name'n as select x from y;",
                       'create table %member() as select x from y;']:
            rows = self.findings(source)
            self.assertTrue(rows)
            self.assertTrue(all(r['severity']=='REVIEW' for r in rows))

    def test_nonwork_ods_is_review_not_syntax_error(self):
        self.assertEqual(self.findings('ods output TestsForLocation=ms.result;')[0]['severity'], 'REVIEW')
        self.assertEqual(self.findings('ods output TestsForLocation=work.result;'), [])

    def test_paired_comments_whitespace_and_string_content(self):
        self.assertTrue(preflight.equivalent("data x; y='a b';run;", "/*note*/ data x ; y = 'a b' ; run ;"))
        self.assertFalse(preflight.equivalent("data x;y='a b';run;", "data x;y='ab';run;"))
        self.assertFalse(preflight.equivalent("data x;y='A';run;", "data x;y='a';run;"))

    def test_manifest_drift_and_no_source_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'a.sas'
            path.write_text('data x;run;', encoding='utf-8')
            manifest = Path(temp)/'manifest.json'
            manifest.write_text(json.dumps([{'file':'a.sas','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]), encoding='utf-8')
            self.assertEqual(preflight.run([path], manifest=manifest)['exit_code'], 0)
            path.write_text('data y;run;', encoding='utf-8')
            before = path.read_bytes(), manifest.read_bytes()
            report = preflight.run([path], manifest=manifest)
            self.assertEqual(report['exit_code'], 1)
            self.assertEqual(report['findings'][0]['rule'], 'MANIFEST-DRIFT')
            self.assertEqual((path.read_bytes(),manifest.read_bytes()), before)

    def test_explicit_file_only_exit_codes_and_private_output(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'a.txt'
            path.write_text("libname ms '/private/path';", encoding='utf-8')
            report = preflight.run([path])
            self.assertEqual(report['exit_code'], 2)
            self.assertNotIn('/private/path', json.dumps(report))
            self.assertFalse(report['sas_executed'])
            self.assertTrue(report['static_only'])
            self.assertEqual(preflight.run([temp])['exit_code'], 1)
            self.assertEqual(set(report['findings'][0]), {'file','line','rule','severity','message'})

    def test_put_data_followup_is_not_an_error(self):
        for source in ['data x; %put NOTE: started; x=1; run;',
                       'data x; %put NOTE: started; set y; run;']:
            self.assertFalse(any(f['severity']=='ERROR' for f in self.findings(source)))

    def test_pair_preserves_macro_value_and_inline_case(self):
        self.assertFalse(preflight.equivalent('%let grp=A;', '%let grp=a;'))
        self.assertFalse(preflight.equivalent('data x; input x $; datalines;\nA\n;\nrun;',
                                               'data x; input x $; datalines;\na\n;\nrun;'))

    def test_pair_preserves_inline_data_whitespace(self):
        self.assertFalse(preflight.equivalent('data x; input x $; cards;\nA  B\n;\nrun;',
                                               'data x; input x $; cards;\nA B\n;\nrun;'))

    def test_empty_manifest_is_not_a_clean_check(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest=Path(temp)/'empty.json'; manifest.write_text('[]',encoding='utf-8')
            self.assertEqual(preflight.run(manifest=manifest)['exit_code'],1)

    def test_pair_preserves_macro_statement_internal_whitespace(self):
        self.assertFalse(preflight.equivalent('%let grp=A B;', '%let grp=A  B;'))
        self.assertFalse(preflight.equivalent('data x; x=&value + 1; run;', 'data x; x=&value  + 1; run;'))

    def test_pair_preserves_macro_function_argument_whitespace(self):
        self.assertFalse(preflight.equivalent('%let out=%sysfunc(compbl(A B));',
                                               '%let out=%sysfunc(compbl(A  B));'))
        self.assertTrue(preflight.equivalent('  %let grp=A B;  ', '%let grp=A B;'))

    def test_truncated_macro_tail_parenthesis_is_review(self):
        source = '%require(ms.example_lines,person_key claim_key amount category);t example_tail,person_key service_dt total_amount duration);'
        rows = self.findings(source)
        self.assertEqual([(r['rule'], r['severity']) for r in rows], [('PREFLIGHT-PAREN', 'REVIEW')])
        self.assertNotIn('example_tail', json.dumps(rows))

    def test_parenthesis_missing_open_close_and_macro_fragments(self):
        for source in ['data x; x=sum(a,b; run;', 'data x; x=)(; run;', '%fragment(); );']:
            rows = self.findings(source)
            self.assertTrue(any(r['rule']=='PREFLIGHT-PAREN' for r in rows))
            self.assertTrue(all(r['severity']=='REVIEW' for r in rows))

    def test_adjacent_macro_calls_and_nested_parentheses_are_clean(self):
        for source in ['%require(ms.a,JID);%require(ms.b,JID);',
                       'data x; x=sum(a,(b*c)); run;']:
            self.assertEqual(self.findings(source), [])

    def test_parenthesis_protected_contexts_do_not_trigger(self):
        sources = ["data x; /* ) */ x='('; * );\nrun;",
                   '%let x=%str(%));', '%let x=%nrstr(%();',
                   '%put NOTE: unmatched );',
                   'data x; input x $; datalines;\n) ( (\n;\nrun;',
                   'data x; input x $; cards4;\n) ( (\n;;;;\nrun;']
        for source in sources:
            self.assertFalse(any(r['rule']=='PREFLIGHT-PAREN' for r in self.findings(source)))

    def test_literal_glued_to_truncated_function_is_review_even_at_eof(self):
        source = "select x from work.a where visit='INPATIENT'um(event_cost) as ip_observed"
        rows = self.findings(source)
        self.assertEqual([(r['rule'], r['severity']) for r in rows], [('PREFLIGHT-LITERAL', 'REVIEW')])
        self.assertNotIn('INPATIENT', json.dumps(rows))

    def test_documented_literal_suffixes_are_not_glued_identifier_findings(self):
        for source in ["data x; d='01JAN2015'd; t='12:30't; dt='01JAN2015:12:30'dt; run;",
                       "data x; 'name with space'n=1; x='41'x; if mask='00100000'b then x=1; run;",
                       "data x; d='01JAN2015'D; x='41'X; run;"]:
            self.assertEqual(self.findings(source), [])

    def test_literal_gluing_inside_protected_text_is_not_executable(self):
        for source in ["/* 'A'word */ data x; y=1; run;", '%put NOTE: "A"word;',
                       '%let x=%nrstr("A"word);', "data x; y='text "+'"A"word'+"'; run;",
                       'data x; input x $; datalines;\n"A"word\n;\nrun;']:
            self.assertFalse(any(r['rule']=='PREFLIGHT-LITERAL' for r in self.findings(source)))

    def test_separated_literal_and_identifier_are_not_glued(self):
        for source in ["data x; if s='A' then x=1; run;", "data _null_; put 'A' x; run;",
                       "data _null_; put 'A'/*comment*/x; run;"]:
            self.assertFalse(any(r['rule']=='PREFLIGHT-LITERAL' for r in self.findings(source)))

    def test_pair_cli_backend_reports_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b = Path(temp)/'a.sas',Path(temp)/'b.txt'
            a.write_text('data x;run;',encoding='utf-8')
            b.write_text('data y;run;',encoding='utf-8')
            report=preflight.run(pairs=[(a,b)])
            self.assertEqual(report['exit_code'],1)
            self.assertEqual(report['findings'][0]['rule'],'PAIR-MISMATCH')


class SqlInputChecks(unittest.TestCase):
    def findings(self, text):
        return [f for f in preflight.inspect(text, 'fixture.sas') if f['rule'] == 'ISS-055']

    def test_direct_sql_character_and_numeric_date_modifiers_are_errors(self):
        text = "proc sql; select input(compress(strip(c),'-/'),?? yymmdd8.), input(put(n,z8.),?? yymmdd8.) from src; quit;"
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR', 'ERROR'])

    def test_sql_single_modifier_and_datastep_double_modifier_are_valid(self):
        text = 'proc sql; select input(c,? yymmdd8.) from src; quit; data dst; set src; d=input(c,?? yymmdd8.); run;'
        self.assertEqual(self.findings(text), [])

    def test_nested_comma_does_not_hide_the_input_modifier(self):
        text = "proc sql; select input(compress(catx('-',a,b),'-/'),?? yymmdd8.) from src; quit;"
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR'])

    def test_literal_question_marks_inputn_and_later_arguments_do_not_match(self):
        text = "proc sql; select '??', input('??',? best32.), inputn(c,'best32.') from src; quit;"
        self.assertEqual(self.findings(text), [])

    def test_comment_between_question_marks_is_still_detected(self):
        self.assertEqual(len(self.findings('proc sql; select input(c,? /* note */ ? best32.) from src; quit;')), 1)

    def test_comments_macro_quotes_and_inline_data_are_not_code(self):
        text = """/* proc sql; select input(x,?? best32.) from src; quit; */
%let note=%nrstr(proc sql; select input(x,?? best32.) from src; quit;);
data src; input text $; datalines;
proc sql; select input(x,?? best32.) from src;
;
run;
"""
        self.assertEqual(self.findings(text), [])

    def test_put_text_does_not_open_a_sql_context(self):
        text = 'data x; %put NOTE: proc sql; d=input(c,?? best32.); run;'
        self.assertEqual(self.findings(text), [])

    def test_sql_expression_macro_is_detected_without_name_allowlists(self):
        text = '%macro arbitrary_parser(x);input(&x,?? best32.)%mend; proc sql; select %arbitrary_parser(c) from src; quit;'
        rows = self.findings(text)
        self.assertEqual([f['severity'] for f in rows], ['ERROR'])

    def test_conditional_sql_expression_branches_are_both_inspected(self):
        text = "%macro parse(x,t);%if &t=C %then %do;input(&x,?? yymmdd8.)%end;%else %do;input(put(&x,z8.),?? yymmdd8.)%end;%mend;proc sql;select %parse(c,C) from src;quit;"
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR', 'ERROR'])

    def test_nested_static_macro_calls_reach_sql_context(self):
        text = '%macro leaf(x);input(&x,?? best32.)%mend;%macro wrap(x);%leaf(&x)%mend;%macro wrap2(x);%wrap(&x)%mend;proc sql;select %wrap2(c) from src;quit;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR'])

    def test_recursive_call_graph_terminates_and_keeps_the_error(self):
        text = '%macro recur(x);%recur(&x) input(&x,?? best32.)%mend;proc sql;select %recur(c) from src;quit;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR'])

    def test_data_step_expression_macro_is_not_a_sql_error(self):
        text = '%macro parse(x);input(&x,?? best32.)%mend;data dst;set src;n=%parse(c);run;'
        self.assertEqual(self.findings(text), [])

    def test_macro_with_explicit_data_step_remains_valid(self):
        text = '%macro build;data dst;set src;n=input(c,?? best32.);run;%mend;%build;'
        self.assertEqual(self.findings(text), [])

    def test_a_sql_caller_is_enough_even_with_valid_data_step_callers(self):
        text = '%macro parse(x);input(&x,?? best32.)%mend;data dst;n=%parse(c);run;proc sql;select %parse(c) from src;quit;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR'])

    def test_unresolved_macro_context_is_review_instead_of_clean(self):
        self.assertEqual([f['severity'] for f in self.findings('%macro parse(x);input(&x,?? best32.)%mend;')], ['REVIEW'])

    def test_unknown_macro_side_effect_does_not_create_a_false_definite_error(self):
        text = 'proc sql;%unknown_step;select input(c,?? best32.) from src;quit;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['REVIEW'])

    def test_known_data_step_macro_side_effect_is_conservative(self):
        text = '%macro start_data;data dst;%mend;proc sql;%start_data;n=input(c,?? best32.);run;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['REVIEW'])

    def test_run_does_not_finish_proc_sql(self):
        self.assertEqual([f['severity'] for f in self.findings('proc sql;run;select input(c,?? best32.) from src;quit;')], ['ERROR'])

    def test_conditional_proc_sql_and_other_proc_contexts(self):
        text = '%macro build;%if &ok %then proc sql;select input(c,?? best32.) from src;quit;%mend;'
        self.assertEqual([f['severity'] for f in self.findings(text)], ['ERROR'])
        self.assertEqual([f['severity'] for f in self.findings('proc fcmp;n=input(c,?? best32.);quit;')], ['REVIEW'])

    def test_cross_file_helper_and_sql_caller_are_checked_together(self):
        with tempfile.TemporaryDirectory() as temp:
            helper, caller = Path(temp)/'helper.txt', Path(temp)/'caller.txt'
            helper.write_text('%macro parse(x);input(&x,?? best32.)%mend;')
            caller.write_text('proc sql;select %parse(c) from src;quit;')
            before = helper.read_bytes(), caller.read_bytes()
            report = preflight.run([helper, caller])
            rows = [f for f in report['findings'] if f['rule'] == 'ISS-055']
            self.assertEqual([f['severity'] for f in rows], ['ERROR'])
            self.assertEqual(report['exit_code'], 1)
            self.assertEqual(rows[0]['file'], str(helper))
            self.assertEqual((helper.read_bytes(), caller.read_bytes()), before)

    def test_manifest_only_inspects_actual_files_and_blocks_the_error(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'bad.txt'
            source.write_text('proc sql;select input(c,?? best32.) from src;quit;')
            manifest = Path(temp)/'manifest.json'
            manifest.write_text(json.dumps([{'file':'bad.txt', 'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]))
            before = source.read_bytes(), manifest.read_bytes()
            report = preflight.run(manifest=manifest)
            self.assertEqual(report['exit_code'], 1)
            self.assertTrue(any(f['rule']=='ISS-055' and f['severity']=='ERROR' for f in report['findings']))
            self.assertEqual((source.read_bytes(), manifest.read_bytes()), before)

    def test_manifest_also_supplies_cross_file_call_context(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = [Path(temp)/'helper.txt', Path(temp)/'caller.txt']
            paths[0].write_text('%macro parse(x);input(&x,?? best32.)%mend;')
            paths[1].write_text('proc sql;select %parse(c) from src;quit;')
            manifest = Path(temp)/'manifest.json'
            manifest.write_text(json.dumps([{'file':p.name, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]))
            rows = preflight.run(manifest=manifest)['findings']
            self.assertEqual([f['severity'] for f in rows if f['rule']=='ISS-055'], ['ERROR'])


class PerformanceChecks(unittest.TestCase):
    def findings(self, source):
        return [f for f in preflight.inspect(source, 'fixture.sas') if f['rule']=='ISS-056']

    def root(self):
        return 'proc append base=out.dx data=work.month;run;proc sort data=out.dx nodupkey;by id mid day code;run;'

    def test_accumulation_then_whole_sort_requires_review(self):
        self.assertEqual([f['severity'] for f in self.findings(self.root())], ['REVIEW'])

    def test_full_copy_lineage_and_derived_flags_are_reviewed(self):
        source = self.root() + 'data work.flags;set out.dx;flag=(code="DEMO");run;data out.final;set work.flags;run;'
        rows = self.findings(source)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(f['severity']=='REVIEW' for f in rows))

    def test_no_materialization_warning_for_narrowed_keep_or_drop(self):
        for copy in ('data out.small;set out.dx(keep=id day);run;',
                     'data out.small(keep=id day);set out.dx;run;',
                     'data out.small;set out.dx;keep id day;run;',
                     'data out.small;set out.dx;drop code;run;'):
            self.assertEqual(len(self.findings(self.root()+copy)), 1)

    def test_filtered_data_steps_are_not_reported_as_full_copies(self):
        for copy in ('data out.small;set out.dx;where day>0;run;',
                     'data out.small;set out.dx;if flag;run;',
                     'data out.small;set out.dx;if not flag then delete;run;'):
            self.assertEqual(len(self.findings(self.root()+copy)), 1)

    def test_null_data_step_does_not_create_a_copy(self):
        self.assertEqual(len(self.findings(self.root()+'data _null_;set out.dx;put id;run;')), 1)

    def test_data_view_is_not_a_disk_materialization(self):
        self.assertEqual(len(self.findings(self.root()+'data out.v / view=out.v;set out.dx;run;')), 1)

    def test_sort_alone_is_not_a_cumulative_sort_candidate(self):
        self.assertEqual(self.findings('proc sort data=out.dx;by id;run;'), [])

    def test_an_earlier_sort_does_not_match_a_later_append(self):
        self.assertEqual(self.findings('proc sort data=out.dx;by id;run;proc append base=out.dx data=work.month;run;'), [])

    def test_sort_of_an_unrelated_dataset_is_not_matched(self):
        self.assertEqual(self.findings('proc append base=out.dx data=work.month;run;proc sort data=out.other;by id;run;'), [])

    def test_comments_and_strings_are_not_performance_operations(self):
        source = '/* '+self.root()+' */ data a;x="proc append base=out.dx data=work.month;run;proc sort data=out.dx;run;";run;'
        self.assertEqual(self.findings(source), [])

    def test_dynamic_targets_are_not_treated_as_static_tables(self):
        source = 'proc append base=&target data=work.month;run;proc sort data=&target;by id;run;'
        self.assertEqual(self.findings(source), [])

    def test_multiple_set_inputs_are_not_reported_as_row_preserving_copies(self):
        self.assertEqual(len(self.findings(self.root()+'data out.combined;set out.dx out.other;run;')), 1)

    def test_case_insensitive_names_and_compressed_copies(self):
        source = 'PROC APPEND BASE=OUT.DX DATA=WORK.MONTH;RUN;PROC SORT DATA=out.dx;BY ID;RUN;data out.c(compress=yes);set OUT.dx;run;'
        self.assertEqual(len(self.findings(source)), 2)

    def test_monthly_dedup_does_not_hide_the_final_sort_workspace_review(self):
        source = 'proc sort data=work.month nodupkey;by id;run;'+self.root()
        self.assertEqual(len(self.findings(source)), 1)

    def test_a_performance_candidate_is_review_not_automatic_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'candidate.txt'
            source.write_text(self.root())
            before = source.read_bytes()
            report = preflight.run([source])
            self.assertEqual(report['exit_code'], 2)
            self.assertFalse(any(f['severity']=='ERROR' for f in report['findings']))
            self.assertEqual(source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
