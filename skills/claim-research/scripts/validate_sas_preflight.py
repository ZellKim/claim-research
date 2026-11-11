"""Read-only, bounded SAS preflight; not a complete SAS/macro parser or SAS execution.
Only explicitly supplied .sas/.txt files are read. Macro expansion, runtime types,
ODS availability and research validity require SAS/log/data review. Exit: 0 clean,
1 ERROR, 2 REVIEW only. --json prints metadata without source snippets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

MACRO_QUOTES = {'%str', '%nrstr', '%quote', '%nrquote', '%bquote', '%nrbquote', '%superq'}
AGGREGATES = {'sum', 'mean', 'avg', 'count', 'min', 'max', 'std', 'n', 'nmiss', 'median'}


def lex(source):
    """Return (value, kind, start, end); protect strings and macro-quoted arguments."""
    out, i, boundary, statement_start = [], 0, True, 0
    while i < len(source):
        if source[i].isspace():
            i += 1
            continue
        if source.startswith('/*', i):
            end = source.find('*/', i + 2)
            if end < 0:
                out.append(('', 'uncertain', i, len(source)))
                break
            i = end + 2
            continue
        if source.startswith('%*', i) or (boundary and source[i] == '*'):
            end = source.find(';', i)
            i = len(source) if end < 0 else end + 1
            continue
        start = i
        if source[i] in "'\"":
            quote = source[i]
            i += 1
            while i < len(source):
                if source[i] == quote:
                    i += 1
                    if i < len(source) and source[i] == quote:
                        i += 1
                        continue
                    break
                i += 1
            else:
                out.append(('', 'uncertain', start, i))
                break
            kind, value = 'string', source[start:i]
        else:
            match = re.match(r'%?[A-Za-z_][A-Za-z_0-9]*|[0-9]+', source[i:])
            value = match.group().lower() if match else source[i]
            i += len(match.group()) if match else 1
            kind = 'word' if match else 'symbol'
            after = i
            while after < len(source) and source[after].isspace():
                after += 1
            if value in MACRO_QUOTES and after < len(source) and source[after] == '(':
                i, depth = after + 1, 1
                while i < len(source) and depth:
                    if source[i] == '%' and i + 1 < len(source) and source[i+1] in "()'\"":
                        i += 2
                        continue
                    if source[i] == '(':
                        depth += 1
                    elif source[i] == ')':
                        depth -= 1
                    i += 1
                kind = 'macroquote' if depth == 0 else 'uncertain'
                value = source[start:i]
        out.append((value, kind, start, i))
        boundary = value == ';'
        if boundary:
            head = out[statement_start:-1]
            if len(head) == 1 and head[0][0] in ('datalines', 'cards', 'datalines4', 'cards4', 'parmcards', 'parmcards4'):
                terminator = ';;;;' if head[0][0].endswith('4') else ';'
                end = re.search(r'(?m)^[ \t]*' + terminator + r'[ \t]*(?:\r?\n|$)', source[i:])
                stop = i + end.end() if end else len(source)
                out.append((source[i:stop], 'inline' if end else 'uncertain', i, stop))
                i = stop
            statement_start = len(out)
    return out


def finding(file, line, rule, severity, message):
    return dict(file=str(file), line=line, rule=rule, severity=severity, message=message)


def sql_input_modifiers(sources):
    """Bounded static call-context analysis, not macro expansion or SAS execution."""
    regions, catalog = [], {}
    for file, source in sources.items():
        tokens = lex(source)
        current = dict(file=file, name=None, tokens=[], incoming=set())
        regions.append(current)
        stack, i = [], 0
        while i < len(tokens):
            value, kind, start, end = tokens[i]
            if value == '%macro' and i + 1 < len(tokens) and tokens[i+1][1] == 'word':
                name = tokens[i+1][0]
                stack.append(current)
                current = dict(file=file, name=name, tokens=[], incoming=set())
                regions.append(current)
                catalog.setdefault(name, []).append(current)
                while i < len(tokens) and tokens[i][0] != ';':
                    i += 1
            elif value == '%mend' and stack:
                current = stack.pop()
                while i < len(tokens) and tokens[i][0] != ';':
                    i += 1
            else:
                current['tokens'].append(tokens[i])
            i += 1

    intrinsic = MACRO_QUOTES | {
        '%if', '%then', '%else', '%do', '%end', '%to', '%by', '%while', '%until',
        '%let', '%local', '%global', '%put', '%return', '%goto', '%abort', '%include',
        '%sysfunc', '%qsysfunc', '%eval', '%sysevalf', '%scan', '%qscan', '%substr',
        '%qsubstr', '%length', '%index', '%upcase', '%qupcase', '%lowcase', '%unquote',
        '%sysget', '%symexist', '%symglobl', '%symlocal', '%sysmexecdepth', '%sysmexecname'
    }

    def statements(tokens):
        pending = []
        for token in tokens:
            pending.append(token)
            if token[0] == ';':
                yield pending
                pending = []
        if pending:
            yield pending

    def head_tokens(statement):
        vals = [t[0] if t[1] in ('word', 'symbol') else '' for t in statement]
        # A macro-controlled PROC/DATA statement can start after THEN/ELSE.
        starts = [0] + [i+1 for i, value in enumerate(vals) if value in ('%then', '%else')]
        return vals, starts

    changing = set()
    for region in regions:
        if region['name']:
            for statement in statements(region['tokens']):
                vals, starts = head_tokens(statement)
                if vals and vals[0] not in ('%let', '%put', '%local', '%global'):
                    if any(i < len(vals) and vals[i] in ('proc', 'data', 'run', 'quit') for i in starts):
                        changing.add(region['name'])
    # A wrapper around a step-producing macro can also change caller context.
    while True:
        more = {r['name'] for r in regions if r['name'] and any(
            t[1] == 'word' and t[0].startswith('%') and t[0][1:] in changing
            for t in r['tokens'])}
        if more <= changing:
            break
        changing.update(more)

    for region in regions:
        context = 'INHERIT' if region['name'] else 'UNKNOWN'
        region['calls'], region['bad'] = [], []
        for statement in statements(region['tokens']):
            vals, starts = head_tokens(statement)
            if not vals or vals[0] in ('%put', '%local', '%global'):
                continue
            generated_text = vals[0] == '%let'
            if not generated_text:
                for j in starts:
                    if j >= len(vals):
                        continue
                    if vals[j] == 'proc' and j+1 < len(vals):
                        context = 'SQL' if vals[j+1] == 'sql' else 'OTHER'
                    elif vals[j] == 'data':
                        context = 'DATA'
                    elif vals[j] == 'quit' or (vals[j] == 'run' and context != 'SQL'):
                        context = 'UNKNOWN'
            for i, token in enumerate(statement):
                value, kind, start, end = token
                if kind != 'word':
                    continue
                if value == 'input' and i+1 < len(statement) and vals[i+1] == '(':
                    depth, j = 1, i+2
                    while j < len(statement):
                        if vals[j] == '(':
                            depth += 1
                        elif vals[j] == ')':
                            depth -= 1
                        elif vals[j] == ',' and depth == 1:
                            if vals[j+1:j+3] == ['?', '?']:
                                region['bad'].append((token, 'UNKNOWN' if generated_text else context))
                            break
                        if depth == 0:
                            break
                        j += 1
                if not generated_text and value.startswith('%') and value not in intrinsic:
                    name = value[1:]
                    if name in catalog:
                        region['calls'].append((name, context))
                    if name in changing or name not in catalog:
                        context = 'UNKNOWN'

    # Propagate only named static calls; conditions and dynamic names stay unresolved.
    while True:
        changed = False
        for region in regions:
            for name, context in region['calls']:
                contexts = region['incoming'] if context == 'INHERIT' else {context}
                for target in catalog[name]:
                    if not contexts <= target['incoming']:
                        target['incoming'].update(contexts)
                        changed = True
        if not changed:
            break
    findings = []
    for region in regions:
        for token, context in region['bad']:
            contexts = (region['incoming'] or {'UNKNOWN'}) if context == 'INHERIT' else {context}
            if contexts <= {'DATA'}:
                continue
            severity = 'ERROR' if 'SQL' in contexts else 'REVIEW'
            message = ('INPUT with ?? is emitted into PROC SQL. Use a single ? and retain value QC.'
                       if severity == 'ERROR' else
                       'INPUT with ?? has unresolved macro/procedure context. Review SQL callers; DATA-step use is valid.')
            source = sources[region['file']]
            findings.append(finding(region['file'], source.count('\n', 0, token[2])+1,
                                    'ISS-055', severity, message))
    return findings


def performance_candidates(source, file):
    """Review static APPEND/sort/copy chains; table volume and necessity are unknown."""
    statements, pending = [], []
    for token in lex(source):
        pending.append(token)
        if token[0] == ';':
            statements.append(pending)
            pending = []
    if pending:
        statements.append(pending)

    def values(statement):
        return [t[0] if t[1] in ('word', 'symbol') else '' for t in statement]

    def head(statement):
        vals = values(statement)
        if not vals or vals[0] in ('%put', '%let', '%local', '%global'):
            return vals, None
        starts = [0] + [i+1 for i, v in enumerate(vals) if v in ('%then', '%else')]
        for i in starts:
            if i < len(vals) and vals[i] in ('proc', 'data', 'set', 'run', 'quit', '%mend'):
                return vals, i
        return vals, None

    def dataset(statement, i):
        vals = values(statement)
        if i >= len(vals) or statement[i][1] != 'word' or vals[i].startswith('%'):
            return None, i
        name, i = vals[i], i+1
        if i < len(vals) and vals[i] == '.':
            if i+1 >= len(vals) or statement[i+1][1] != 'word':
                return None, i
            name += '.' + vals[i+1]
            i += 2
        if i < len(vals) and (vals[i] == '&' or vals[i].startswith('%')):
            return None, i
        return name, i

    appends, sorts, blocks = [], [], []
    for position, statement in enumerate(statements):
        vals, start = head(statement)
        if start is None:
            continue
        if vals[start:start+2] in (['proc', 'append'], ['proc', 'sort']):
            option = 'base' if vals[start+1] == 'append' else 'data'
            for j in range(start+2, len(vals)-1):
                if vals[j:j+2] == [option, '=']:
                    name, end = dataset(statement, j+2)
                    if name:
                        (appends if option == 'base' else sorts).append((name, position, statement[start]))
                    break
        if vals[start] != 'data':
            continue
        target, end = dataset(statement, start+1)
        if not target or target == '_null_' or (end < len(vals) and vals[end] not in ('(', '/', ';')):
            continue
        body, source_tables, j = [], [], position+1
        while j < len(statements):
            child = statements[j]
            child_vals, child_start = head(child)
            if child_start is not None and child_vals[child_start] in ('proc', 'data', 'run', 'quit', '%mend'):
                break
            body.extend(child_vals)
            if child_start is not None and child_vals[child_start] == 'set':
                parent, tail = dataset(child, child_start+1)
                if parent and (tail == len(child_vals) or child_vals[tail] in ('(', ';', 'end', 'nobs', 'point', 'key')):
                    source_tables.append(parent)
                else:
                    source_tables.append(None)
            j += 1
        if len(source_tables) == 1 and source_tables[0]:
            narrowed = any(v in ('keep', 'drop', 'where', 'if', 'delete', 'output', 'merge', 'update', 'modify')
                           for v in vals + body)
            is_view = 'view' in vals and '/' in vals
            blocks.append((target, source_tables[0], not narrowed and not is_view,
                           statement[start]))

    findings, roots = [], set()
    for table, sort_position, token in sorts:
        if any(parent == table and append_position < sort_position for parent, append_position, _ in appends):
            roots.add(table)
            findings.append(finding(file, source.count('\n', 0, token[2])+1, 'ISS-056', 'REVIEW',
                'APPEND accumulation is followed by a whole-table SORT. Review row budget, monthly reduction and sort workspace; the sort may be required.'))
    lineage = set(roots)
    emitted = set()
    while True:
        before = set(lineage)
        for target, parent, full_width, token in blocks:
            if parent in lineage:
                lineage.add(target)
                if full_width and token[2] not in emitted:
                    emitted.add(token[2])
                    findings.append(finding(file, source.count('\n', 0, token[2])+1, 'ISS-056', 'REVIEW',
                        'An accumulated-table lineage is materialized with SET without row/column reduction. Review derived-table placement, duplicate copies and peak storage.'))
        if lineage == before:
            break
    return findings


def inspect(source, file, check_sql_inputs=True):
    tokens, findings, statement = lex(source), [], []
    def emit(token, rule, severity, message):
        findings.append(finding(file, source.count('\n', 0, token[2]) + 1, rule, severity, message))
    for token in tokens:
        if token[1] == 'uncertain':
            emit(token, 'PREFLIGHT-LEX', 'REVIEW', 'Unterminated lexical construct; manual review required.')
        if statement and token[1] == 'word':
            previous = statement[-1]
            # D/T/DT/N/X/B are documented SAS literal suffixes. Other adjacent
            # words may reflect missing separators or intended macro text.
            if (previous[1] == 'string' and previous[3] == token[2]
                    and token[0] not in {'d', 't', 'dt', 'n', 'x', 'b'}
                    and not any(t[0] == '%put' for t in statement)):
                emit(previous, 'PREFLIGHT-LITERAL', 'REVIEW', 'Quoted literal is glued to an identifier; inspect missing separators or intended macro text.')
        statement.append(token)
        if token[0] != ';':
            continue
        vals = [t[0] if t[1] in ('word', 'symbol') else '' for t in statement]
        if '%put' in vals:
            if any(t[1] == 'macroquote' for t in statement):
                emit(statement[vals.index('%put')], 'ISS-048', 'REVIEW', 'Macro quoting in PUT requires expansion-aware review.')
            tail = source[token[3]:].split('\n', 1)[0]
            following = lex(tail)
            if following and not following[0][0].startswith('%'):
                # Valid subsequent SAS statements are not leftover prose.
                first = following[0][0]
                valid = {'data', 'proc', 'run', 'quit', 'options', 'libname', 'filename', 'ods', 'title', 'footnote'}
                if first not in valid:
                    emit(token, 'ISS-048', 'REVIEW', 'Trailing statement after PUT requires context review; it may be a valid DATA-step statement.')
            statement = []
            continue
        if vals and vals[0] == 'libname' and any(t[1] == 'string' for t in statement):
            emit(statement[0], 'ISS-050', 'REVIEW', 'File LIBNAME statement may reassign an existing libref; inspect assignment context.')
        if len(vals) > 2 and vals[:2] == ['ods', 'output']:
            for j in range(2, len(vals) - 3):
                if vals[j] == '=' and vals[j+2] == '.' and vals[j+1] != 'work':
                    emit(statement[j], 'ISS-052', 'REVIEW', 'ODS output targets a non-WORK library; verify fresh-output and empty-result handling.')
        for j in range(len(vals) - 2):
            if vals[j:j+2] != ['create', 'table']:
                continue
            k = j + 2
            if statement[k][1] == 'string' or vals[k] == '&' or vals[k].startswith('%'):
                emit(statement[k], 'ISS-051', 'REVIEW', 'Macro or name-literal CREATE target requires expansion-aware review.')
                continue
            if not re.fullmatch(r'[a-z_][a-z_0-9]{0,31}', vals[k]):
                emit(statement[k], 'ISS-051', 'ERROR', 'Invalid CREATE TABLE target token.')
                continue
            k += 1
            if k < len(vals) and vals[k] == '.':
                k += 1
                if k >= len(vals) or statement[k][1] == 'string' or vals[k] == '&' or vals[k].startswith('%'):
                    emit(statement[j], 'ISS-051', 'REVIEW', 'Dynamic or name-literal member requires review.')
                    continue
                if not re.fullmatch(r'[a-z_][a-z_0-9]{0,31}', vals[k]):
                    emit(statement[k], 'ISS-051', 'ERROR', 'Invalid CREATE TABLE member token.')
                    continue
                k += 1
            if k < len(vals) and vals[k] not in ('as', 'like', '(', ';'):
                if vals[k] == '&' or vals[k].startswith('%'):
                    emit(statement[k], 'ISS-051', 'REVIEW', 'Dynamic CREATE TABLE suffix requires review.')
                else:
                    emit(statement[k], 'ISS-051', 'ERROR', 'Unexpected token after CREATE TABLE name.')
        # Lexical candidate only: macro fragments can intentionally span statements.
        # PUT text was handled above; strings, comments, macro quotes and inline
        # data never contribute parentheses to vals.
        depth, outer, unmatched_close = 0, [], False
        for t, value in zip(statement, vals):
            if value == ')':
                depth -= 1
                unmatched_close = unmatched_close or depth < 0
            if depth == 0:
                outer.append((value, t))
            if value == '(':
                depth += 1
        if depth != 0 or unmatched_close:
            emit(statement[0], 'PREFLIGHT-PAREN', 'REVIEW', 'Unbalanced unquoted parentheses in a statement; inspect truncation or intentional macro fragments.')
        words = [x[0] for x in outer]
        if 'select' in words and any(words[j:j+2] == ['group', 'by'] for j in range(len(words)-1)):
            aggregate = any(words[j] in AGGREGATES and words[j+1] == '(' for j in range(len(words)-1))
            if not aggregate:
                emit(next(t for v, t in outer if v == 'select'), 'ISS-049', 'REVIEW', 'GROUP BY without recognized outer aggregate; inspect HAVING, subqueries and intended grain before changing it.')
        statement = []
    if check_sql_inputs:
        findings.extend(sql_input_modifiers({str(file): source}))
    findings.extend(performance_candidates(source, file))
    return findings


def read_source(path):
    path = Path(path)
    if not path.is_file() or path.suffix.lower() not in ('.sas', '.txt'):
        raise ValueError('Explicit SAS/TXT regular file required.')
    return path.read_text(encoding='utf-8-sig')


def comparable(source):
    """Conservative identity, not proof of semantic equivalence after macro expansion."""
    result, statement = [], []
    def flush():
        if not statement:
            return
        dynamic = any(t[1] != 'string' and (t[0].startswith('%') or t[0] == '&') for t in statement)
        if dynamic:
            result.append(('macro_statement', source[statement[0][2]:statement[-1][3]].strip()))
        else:
            result.extend((t[1], source[t[2]:t[3]]) for t in statement)
        statement.clear()
    for token in lex(source):
        if token[1] == 'inline':
            flush()
            result.append(('inline', source[token[2]:token[3]]))
        else:
            statement.append(token)
            if token[0] == ';':
                flush()
    flush()
    return result


def equivalent(left, right):
    # Ordinary token case, quoted content, inline data and macro-statement spacing survive.
    return comparable(left) == comparable(right)


def run(files=(), pairs=(), manifest=None):
    findings, sources = [], {}
    def load(path):
        key = str(Path(path))
        if key not in sources:
            sources[key] = read_source(path)
            findings.extend(inspect(sources[key], key, check_sql_inputs=False))
        return sources[key]
    for path in files:
        try:
            load(path)
        except (OSError, UnicodeError, ValueError):
            findings.append(finding(path, 0, 'PREFLIGHT-INPUT', 'ERROR', 'Cannot read an explicit UTF-8 SAS/TXT file.'))
    for left, right in pairs:
        try:
            if not equivalent(load(left), load(right)):
                findings.append(finding(left, 0, 'PAIR-MISMATCH', 'ERROR', 'Executable token sequences differ from the supplied paired file.'))
        except (OSError, UnicodeError, ValueError):
            findings.append(finding(left, 0, 'PREFLIGHT-INPUT', 'ERROR', 'Cannot read both explicit paired files.'))
    if manifest:
        try:
            data = json.loads(Path(manifest).read_text(encoding='utf-8-sig'))
            if not isinstance(data, list) or not data:
                raise ValueError()
            for item in data:
                path = Path(item['file'])
                if not path.is_absolute():
                    path = Path(manifest).parent / path
                load(path)
                expected = item['sha256']
                if not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
                    raise ValueError()
                if hashlib.sha256(path.read_bytes()).hexdigest() != expected.lower():
                    findings.append(finding(path, 0, 'MANIFEST-DRIFT', 'ERROR', 'File hash differs from the supplied recorded hash.'))
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            findings.append(finding(manifest, 0, 'MANIFEST-INPUT', 'ERROR', 'Manifest or one of its explicit SAS/TXT entries is invalid or unreadable.'))
    findings.extend(sql_input_modifiers(sources))
    code = 1 if any(f['severity'] == 'ERROR' for f in findings) else 2 if findings else 0
    return {'static_only': True, 'sas_executed': False, 'exit_code': code, 'findings': findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*')
    parser.add_argument('--pair', action='append', nargs=2, default=[], metavar=('INPUT', 'ANNOTATED'))
    parser.add_argument('--manifest')
    parser.add_argument('--json', action='store_true', help='Print JSON to stdout; never edit source or manifest.')
    args = parser.parse_args()
    if not (args.files or args.pair or args.manifest):
        parser.error('Supply explicit files, pairs or a manifest; directory scanning is not supported.')
    report = run(args.files, args.pair, args.manifest)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for f in report['findings']:
            print('{file}:{line}: {severity} {rule}: {message}'.format(**f))
        print('Static only; SAS was not executed. Exit:', report['exit_code'])
    return report['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
