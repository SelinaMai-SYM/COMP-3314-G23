#!/usr/bin/env python3
"""Verify one exact committed candidate in a fresh checkout and environment.

This is a verification command, not a publisher. Run it through the shared
``validation`` scheduler (cpu_limit <= 900, wall_limit <= 1800), passing a new
external output directory. It never pushes, renames a branch or changes GitHub.
PDF pages are rendered for the separate visual review; this command cannot
certify that review. Failed and interrupted commands retain their evidence.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET

THREADS = {name: '1' for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS', 'BLIS_NUM_THREADS']}
CLEAR = ['PYTHONPATH', 'COMP3314_DATA_ROOT', 'COMP3314_ARTIFACT_ROOT', 'PYTHONHOME', 'VIRTUAL_ENV',
    'PYTHONSTARTUP', 'PYTHONUSERBASE', 'PIP_TARGET', 'PIP_PREFIX', 'PIP_USER',
    'PIP_TRUSTED_HOST', 'PIP_NO_VERIFY', 'PIP_REQUIREMENT', 'PIP_CONSTRAINT',
    'PIP_EXTRA_INDEX_URL', 'PIP_FIND_LINKS', 'PIP_NO_INDEX',
    'GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
    'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_SHALLOW_FILE',
    'GIT_NAMESPACE', 'GIT_SSL_NO_VERIFY', 'GIT_CONFIG_COUNT', 'GIT_CONFIG_PARAMETERS']
BENCHMARKS = ['AR', 'JAFFE', 'ORL', 'UMIST', 'BinAlpha', 'MSRA50', 'YaleB', 'USPS']


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    os.replace(temporary, path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def cpu_seconds():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + child.ru_utime + child.ru_stime


def _ps_time(value):
    days = 0
    if '-' in value:
        day, value = value.split('-', 1)
        days = int(day)
    return days * 86400 + sum(float(part) * 60 ** i for i, part in enumerate(reversed(value.split(':'))))


def aux_label_page(text, label):
    """Read the page field of one ordinary or hyperref LaTeX newlabel.

    Balanced groups permit nested braces in other fields; a missing, repeated
    or nonnumeric page is an error rather than an inferred page count.
    """
    matches = list(re.finditer(r'\\newlabel\s*\{' + re.escape(label) + r'\}\s*', text))
    if len(matches) != 1:
        raise ValueError('expected exactly one compiled LaTeX label: ' + label)

    def group(value, offset):
        while offset < len(value) and value[offset].isspace(): offset += 1
        if offset >= len(value) or value[offset] != '{':
            raise ValueError('malformed compiled LaTeX label: ' + label)
        start = offset + 1
        depth = 1
        offset += 1
        while offset < len(value):
            char = value[offset]
            if char == '\\':
                offset += 2
                continue
            if char == '{': depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0: return value[start:offset], offset + 1
            offset += 1
        raise ValueError('unclosed compiled LaTeX label: ' + label)

    body, _ = group(text, matches[0].end())
    _, offset = group(body, 0)
    page, _ = group(body, offset)
    if not re.fullmatch(r'[1-9]\d*', page.strip()):
        raise ValueError('compiled LaTeX label page is not a positive integer: ' + label)
    return int(page.strip())


def report_main_boundaries(source,auxiliary):
    """Count flushed main floats before references, using compiled markers."""
    # Ignore TeX comments, preserving escaped percent signs in ordinary text.
    lines=[]
    for line in source.splitlines():
        for index,char in enumerate(line):
            if char!='%':continue
            before=index-1
            while before>=0 and line[before]=='\\':before-=1
            if (index-before-1)%2==0:
                line=line[:index];break
        lines.append(line)
    source='\n'.join(lines)
    def marker(label):
        matches=list(re.finditer(r'\\label\s*\{\s*'+re.escape(label)+r'\s*\}',source))
        if len(matches)!=1:raise ValueError('expected exactly one report source marker: '+label)
        return matches[0]
    body=marker('main_end');references=marker('references_start')
    bibliography=re.search(r'\\bibliography\s*\{',source)
    appendix=re.search(r'\\appendix\b',source)
    clearpages=list(re.finditer(r'\\clearpage\b',source))
    if (bibliography is None or appendix is None or not body.start()<references.start()<bibliography.start()<appendix.start()
        or not any(body.end()<=clear.start()<references.start() for clear in clearpages)):
        raise ValueError('report source must order main_end, main clearpage, references_start, bibliography, appendix')
    body_page=aux_label_page(auxiliary,'main_end')
    references_page=aux_label_page(auxiliary,'references_start')
    main_pages=references_page-1
    if not 0<body_page<=main_pages:
        raise ValueError('compiled main_end must precede references_start and fit inside the flushed main pages')
    return {'main_pages':main_pages,'body_end_page':body_page,'references_start_page':references_page,
        'within_four_page_limit':main_pages<=4,
        'main_page_source':'compiled references_start page minus one; includes flushed main floats, excludes references'}


def junit_results(path):
    """Record actual testcase outcomes; do not infer counts from console prose."""
    tree = ET.parse(path)
    tag = lambda node: node.tag.rsplit('}', 1)[-1]
    cases = []
    for node in tree.getroot().iter():
        if tag(node) != 'testcase': continue
        outcomes = [child for child in node if tag(child) in ['failure', 'error', 'skipped']]
        if len(outcomes) > 1:
            raise ValueError('ambiguous JUnit testcase outcome')
        outcome = outcomes[0] if outcomes else None
        status = tag(outcome) if outcome is not None else 'passed'
        row = {'classname': node.get('classname', ''), 'name': node.get('name', ''), 'status': status}
        if outcome is not None:
            row.update(message=outcome.get('message', ''), detail=''.join(outcome.itertext()).strip())
        cases.append(row)
    counts = {name: sum(case['status'] == status for case in cases) for name, status in
        [('passed', 'passed'), ('failures', 'failure'), ('errors', 'error'), ('skipped', 'skipped')]}
    return {'junit_path': str(path), 'junit_sha256': sha(path), 'tests': len(cases), **counts,
        'testcases': cases, 'reported_suites': [dict(node.attrib) for node in tree.getroot().iter() if tag(node) == 'testsuite']}


def descendants(root, ps_path, environment):
    """Keep children in the scheduler's process group, and sample the tree."""
    raw = subprocess.check_output([ps_path, '-axo', 'pid=,ppid=,time=,rss='], text=True, env=environment)
    rows = {}
    for line in raw.splitlines():
        fields = line.split()
        if len(fields) == 4:
            pid, parent = map(int, fields[:2])
            rows[pid] = (parent, _ps_time(fields[2]), int(fields[3]) * 1024)
    selected = {root}
    while True:
        expanded = selected | {pid for pid, row in rows.items() if row[0] in selected}
        if expanded == selected: break
        selected = expanded
    live = [pid for pid in selected if pid != root and pid in rows]
    return live, sum(rows[pid][1] for pid in live), sum(rows[pid][2] for pid in selected if pid in rows)


class BudgetExceeded(RuntimeError):
    pass


class Acceptance:
    def __init__(self, args):
        self.args = args
        self.output = Path(args.output).expanduser().resolve()
        self.repository = repository_argument(args.repository)
        self.data = Path(args.data_root).expanduser().resolve()
        if not self.data.is_dir(): raise ValueError('explicit data root does not exist')
        source = Path(self.repository) if not self.repository.startswith('https://') else None
        if source is not None and (self.data == source or source in self.data.parents):
            raise ValueError('data root must be independent of the source repository')
        for protected in [self.data, source]:
            if protected is not None and (self.output == protected or protected in self.output.parents or self.output in protected.parents):
                raise ValueError('acceptance output must be separate from repository and data roots')
        if self.output.exists() and (not self.output.is_dir() or any(self.output.iterdir())):
            raise ValueError('acceptance output must be new or empty; previous evidence is never overwritten')
        self.output.mkdir(parents=True, exist_ok=True)
        self.logs = self.output / 'command logs'
        self.logs.mkdir()
        self.checkout = self.output / 'fresh checkout with spaces'
        self.venv = self.output / 'fresh environment with spaces'
        self.products = self.output / 'acceptance outputs'
        self.products.mkdir()
        self.started = time.perf_counter()
        self.cpu_start = cpu_seconds()
        self.env = os.environ.copy()
        dynamic_git_config = [name for name in self.env
            if name.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_'))]
        clear_keys = sorted(set(CLEAR) | set(dynamic_git_config))
        actually_removed = [name for name in clear_keys if name in self.env]
        for name in clear_keys: self.env.pop(name, None)
        self.env.update(THREADS)
        self.env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
            PYTEST_ADDOPTS='-p no:cacheprovider', MPLBACKEND='Agg',
            PIP_CONFIG_FILE=os.devnull, PIP_NO_INPUT='1', PIP_DISABLE_PIP_VERSION_CHECK='1',
            PIP_INDEX_URL='https://pypi.org/simple')
        # Python is invoked by absolute path. External build tools come only
        # from ordinary system locations, not an inherited worktree/venv bin.
        self.env['PATH'] = os.pathsep.join(['/usr/bin', '/bin', '/usr/sbin', '/sbin',
            '/Library/TeX/texbin', '/opt/homebrew/bin', '/usr/local/bin'])
        self.ps_path = shutil.which('ps', path=self.env['PATH'])
        if not self.ps_path or not Path(self.ps_path).is_absolute():
            raise ValueError('an absolute system ps executable is required for acceptance accounting')
        self.result = {'schema': 'fresh-checkout-acceptance-v1', 'status': 'RUNNING',
            'started_at_utc': utc(), 'repository': self.repository, 'branch': args.branch,
            'expected_commit': args.expected_commit.lower(), 'observed_commit': None,
            'expected_commit_verified': False, 'data_root': str(self.data),
            'checkout': str(self.checkout), 'venv': str(self.venv),
            'cpu_limit_seconds': args.cpu_limit, 'wall_limit_seconds': args.wall_limit,
            'environment_overrides': {**THREADS, **{key: self.env[key] for key in [
                'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE', 'PYTEST_ADDOPTS', 'MPLBACKEND',
                'PIP_CONFIG_FILE', 'PIP_NO_INPUT', 'PIP_DISABLE_PIP_VERSION_CHECK', 'PIP_INDEX_URL', 'PATH']}},
            'cleared_environment_keys': actually_removed,
            'environment_clear_policy': sorted(CLEAR) + ['GIT_CONFIG_KEY_*', 'GIT_CONFIG_VALUE_*'],
            'preserved_git_ca_environment_keys': [name for name in ['GIT_SSL_CAINFO', 'GIT_SSL_CAPATH'] if name in self.env],
            'clone_tls_verification': 'command-local git -c http.sslVerify=true; global configuration is not modified',
            'process_monitor_executable': self.ps_path,
            'commands': [], 'checks': [],
            'max_sampled_tree_rss_bytes': 0, 'no_publication_actions': True,
            'visual_review_passed': False, 'visual_review_status': 'SEPARATE_REVIEW_REQUIRED',
            'harness_path': str(Path(__file__).resolve()), 'harness_sha256': sha(__file__)}
        self.save()

    def save(self):
        self.result.update(wall_seconds=time.perf_counter() - self.started,
            cpu_seconds=cpu_seconds() - self.cpu_start)
        atomic_json(self.output / 'acceptance.json', self.result)

    def check_budget(self, live_cpu=0):
        if time.perf_counter() - self.started >= self.args.wall_limit:
            raise BudgetExceeded('WALL_LIMIT')
        if cpu_seconds() - self.cpu_start + live_cpu >= self.args.cpu_limit:
            raise BudgetExceeded('CPU_LIMIT')

    def check(self, name, ok, **details):
        self.check_budget()
        self.result['checks'].append({'name': name, 'passed': bool(ok), **details})
        self.save()
        if not ok: raise ValueError('acceptance check failed: ' + name)

    def run(self, name, argv, cwd=None, capture=False):
        self.check_budget()
        index = len(self.result['commands']) + 1
        log = self.logs / f'{index:02d}-{name}.log'
        entry = {'name': name, 'argv': list(map(str, argv)), 'cwd': str(cwd or self.checkout),
            'started_at_utc': utc(), 'status': 'RUNNING', 'log_path': str(log)}
        self.result['commands'].append(entry)
        self.save()
        started = time.perf_counter()
        cpu = cpu_seconds()
        process = None
        known = []
        try:
            with log.open('w') as stream:
                process = subprocess.Popen(entry['argv'], cwd=entry['cwd'], env=self.env,
                    stdout=stream, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
                checkpoint = time.perf_counter()
                while process.poll() is None:
                    known, live_cpu, rss = descendants(os.getpid(), self.ps_path, self.env)
                    self.result['max_sampled_tree_rss_bytes'] = max(self.result['max_sampled_tree_rss_bytes'], rss)
                    self.check_budget(live_cpu)
                    if time.perf_counter() - checkpoint >= 5:
                        self.save()
                        checkpoint = time.perf_counter()
                    time.sleep(.25)
                entry['exit_code'] = process.wait()
                entry['status'] = 'COMPLETED' if entry['exit_code'] == 0 else 'FAILED'
            if entry['exit_code'] != 0:
                raise RuntimeError(f'{name} exited {entry["exit_code"]}; see {log}')
            return log.read_text(errors='replace') if capture else None
        except BaseException as exc:
            entry.update(status='TIMEOUT' if isinstance(exc, BudgetExceeded) else 'FAILED', error=repr(exc))
            if process is not None:
                try: current, _, _ = descendants(os.getpid(), self.ps_path, self.env)
                except (OSError, subprocess.SubprocessError): current = known
                # Never signal the scheduler or this runner. Keep descendants
                # in the outer scheduler's process group for its accounting.
                for pid in reversed(list(dict.fromkeys(current + [process.pid]))):
                    if pid == os.getpid(): continue
                    try: os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError: pass
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                # A terminated direct child can leave a live grandchild. Stop
                # every sampled descendant even if the direct wait returned.
                for pid in reversed(list(dict.fromkeys(current + [process.pid]))):
                    if pid == os.getpid(): continue
                    try: os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                process.wait()
                entry['exit_code'] = process.returncode
            raise
        finally:
            entry.update(wall_seconds=time.perf_counter() - started, cpu_seconds=cpu_seconds() - cpu,
                ended_at_utc=utc(), log_sha256=sha(log) if log.exists() else None)
            self.save()

    def verify_checkout(self):
        # --no-local forces normal Git transport for a local path, so --depth
        # is honored instead of being ignored by the local-copy optimization.
        self.run('clone', ['git', '-c', 'http.sslVerify=true', 'clone', '--no-local', '--single-branch', '--depth', '1',
            '--branch', self.args.branch, '--', self.repository, self.checkout], cwd=self.output)
        observed = self.run('commit', ['git', 'rev-parse', 'HEAD'], capture=True).strip()
        self.result['observed_commit'] = observed
        self.result['expected_commit_verified'] = observed == self.args.expected_commit.lower()
        self.check('exact_expected_commit', self.result['expected_commit_verified'], observed=observed,
            expected=self.args.expected_commit.lower())
        branch = self.run('branch', ['git', 'symbolic-ref', '--short', 'HEAD'], capture=True).strip()
        shallow = self.run('shallow', ['git', 'rev-parse', '--is-shallow-repository'], capture=True).strip()
        status = self.run('initial-cleanliness', ['git', 'status', '--porcelain'], capture=True).strip()
        self.check('single_branch_shallow_clean_checkout', branch == self.args.branch and shallow == 'true' and status == '',
            observed_branch=branch, shallow=shallow, initial_status=status)
        self.check('independent_git_objects', (self.checkout / '.git').is_dir()
            and not (self.checkout / '.git/objects/info/alternates').exists())
        self.check('no_local_data_pointer', not (self.checkout / 'local/data_root.txt').exists())
        tracked = self.run('tracked-files', ['git', 'ls-files', '-z'], capture=True).split('\0')
        self.tracked = [name for name in tracked if name]
        unsafe = []
        raw_data = []
        for name in self.tracked:
            path = self.checkout / name
            if path.is_symlink() and not path.resolve().is_relative_to(self.checkout): unsafe.append(name)
            parts = Path(name).parts
            if len(parts) >= 4 and parts[0] == 'benchmarks' and parts[2] == 'data':
                if path.is_file() and path.name not in ['.gitkeep', '.gitignore'] and not path.name.lower().startswith('readme'):
                    raw_data.append(name)
        self.check('no_external_source_symlinks', not unsafe, paths=unsafe)
        self.check('no_embedded_benchmark_data', not raw_data, paths=raw_data)
        fresh_harness = self.checkout / 'scripts/submission_refresh/acceptance.py'
        self.check('committed_acceptance_harness', fresh_harness.is_file()
            and sha(fresh_harness) == self.result['harness_sha256'])
        self.before = {name: sha(self.checkout / name) for name in self.tracked if (self.checkout / name).is_file()}
        atomic_json(self.output / 'source_inventory.json', {'commit': observed, 'files': self.before})
        self.result['source_inventory_sha256'] = sha(self.output / 'source_inventory.json')

    def environment(self):
        self.run('new-venv', [sys.executable, '-m', 'venv', self.venv])
        self.python = self.venv / 'bin/python'
        self.env['PATH'] = str(self.venv / 'bin') + os.pathsep + self.env['PATH']
        self.env['PIP_REQUIRE_VIRTUALENV'] = '1'
        self.result['environment_after_venv'] = {'PATH': self.env['PATH'], 'PIP_REQUIRE_VIRTUALENV': '1'}
        self.check('venv_isolated_from_system_site', 'include-system-site-packages = false'
            in (self.venv / 'pyvenv.cfg').read_text().lower())
        self.run('install-locked-dependencies', [self.python, '-m', 'pip', 'install', '-r', 'environment/requirements.lock.txt'])
        self.run('install-own-checkout', [self.python, '-m', 'pip', 'install', '--no-deps', '-e', str(self.checkout)])
        frozen = self.run('dependency-freeze', [self.python, '-m', 'pip', 'freeze', '--all'], capture=True)
        (self.output / 'tested-environment.txt').write_text(frozen)
        self.result['dependency_freeze_sha256'] = sha(self.output / 'tested-environment.txt')
        probe = '''import importlib,importlib.metadata,json,pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve();versions={};locations={}
for line in (root/'environment/requirements.lock.txt').read_text().splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 name,wanted=line.split('==');actual=importlib.metadata.version(name)
 if actual!=wanted:raise RuntimeError(f'locked version mismatch: {name}: {actual} != {wanted}')
 versions[name]=actual
for name in ['SSC_method','benchmarks','baselines','experiments','method_extension']:
 module=importlib.import_module(name);location=pathlib.Path(module.__file__).resolve()
 if not location.is_relative_to(root):raise RuntimeError('module imported outside own checkout: '+name)
 locations[name]=str(location)
import certifi
print(json.dumps({'python':sys.version,'executable':sys.executable,'prefix':sys.prefix,'base_prefix':sys.base_prefix,'packages':versions,'module_locations':locations,'certifi_ca_file':certifi.where()},sort_keys=True,indent=2))
'''
        verified = self.run('verify-installed-environment', [self.python, '-c', probe, self.checkout], capture=True)
        atomic_json(self.output / 'installed_environment.json', json.loads(verified))

    def pytest_stage(self, name, command, junit, expected_integration_skip):
        """Keep JUnit evidence even when pytest returns a failing exit code."""
        record = {'junit_path': str(junit), 'report_exists': False}
        try:
            self.run(name, command)
        finally:
            record['report_exists'] = junit.is_file()
            if junit.is_file():
                try: record.update(junit_results(junit))
                except (ET.ParseError, OSError, ValueError) as exc: record['parse_error'] = repr(exc)
            self.result[name] = record
            self.save()
        self.check(name + '-junit-valid', record['report_exists'] and 'parse_error' not in record
            and record.get('tests', 0) > 0 and record.get('passed', 0) > 0, report=record)
        self.check(name + '-no-failures-or-errors', record['failures'] == record['errors'] == 0,
            failures=record['failures'], errors=record['errors'])
        skipped = [case for case in record['testcases'] if case['status'] == 'skipped']
        integration_name = 'test_available_catalogue_replay_and_seed0'
        integration = [case for case in record['testcases'] if case['name'] == integration_name
            and case['classname'].endswith('test_candidates')]
        if expected_integration_skip:
            allowed = len(skipped) == 1 and len(integration) == 1 and skipped == integration
            allowed = allowed and 'integration check requires COMP3314_DATA_ROOT' in (
                skipped[0].get('message', '') + '\n' + skipped[0].get('detail', ''))
            self.check(name + '-only-expected-no-data-skip', allowed, actual_skips=skipped,
                policy='Only the explicit candidate-data integration skip is allowed. Missing CVXPY/backend reference skips fail acceptance.')
        else:
            self.check(name + '-real-integration-executed', not skipped and len(integration) == 1
                and integration[0]['status'] == 'passed', actual_skips=skipped)

    def focused_regressions(self):
        config = self.checkout / 'configs/submission_refresh/revalidation_v4_queue.json'
        tasks = json.loads(config.read_text())['tasks']
        matches = [task for task in tasks if task.get('run_id') == 'validation-focused-tests-v4']
        self.check('focused-v4-selection-present', len(matches) == 1)
        command = matches[0]['command']
        self.check('focused-v4-pytest-command', command[:3] == ['{python}', '-m', 'pytest']
            and command.count('--junitxml') == 1)
        arguments = list(command[3:])
        index = arguments.index('--junitxml')
        self.check('focused-v4-junit-argument', index + 1 < len(arguments))
        junit = self.products / 'focused-regressions.xml'
        arguments[index + 1] = str(junit)
        self.check('focused-v4-no-unresolved-placeholders', not any('{' in value or '}' in value for value in arguments))
        self.check('focused-no-data-environment', all(key not in self.env for key in
            ['COMP3314_DATA_ROOT', 'COMP3314_ARTIFACT_ROOT', 'PYTHONPATH']))
        self.result['focused_selection'] = {'config': str(config.relative_to(self.checkout)),
            'sha256': sha(config), 'task_run_id': matches[0]['run_id'],
            'qualification': 'The committed v4 pytest selection is reused verbatim except its fresh JUnit output path.'}
        self.pytest_stage('focused-regressions', [self.python, '-m', 'pytest', *arguments], junit,
            expected_integration_skip=True)

    def no_data_rebuilds(self):
        self.check('no-inherited-data-or-artifact-root', all(key not in self.env for key in
            ['COMP3314_DATA_ROOT', 'COMP3314_ARTIFACT_ROOT', 'PYTHONPATH']))
        self.run('synthetic', [self.python, '-m', 'experiments.v3_reproduction', 'smoke', '--dataset', 'synthetic'])
        historical = self.products / 'historical rebuild'
        joint = self.products / 'joint historical rebuild'
        current = self.products / 'current subset rebuild'
        evidence = self.products / 'baseline graph rebuild'
        self.run('historical-no-data', [self.python, '-m', 'experiments.v3_reproduction', 'rebuild-results',
            '--release-manifest', 'configs/final/release_manifest.json', '--output', historical])
        self.run('joint-no-data', [self.python, '-m', 'experiments.submission_refresh', 'rebuild',
            '--config', 'configs/submission_refresh/campaign.yaml', '--output', joint])
        self.run('current-no-data', [self.python, '-m', 'experiments.submission_refresh.current_release', 'rebuild',
            '--release-manifest', 'configs/subset_search/release_manifest.json', '--output', current])
        self.run('evidence-no-data', [self.python, '-m', 'experiments.submission_refresh', 'rebuild-evidence',
            '--config', 'configs/submission_refresh/campaign.yaml', '--release-manifest',
            'configs/submission_refresh/evidence_manifest.json', '--output', evidence])
        for folder, marker in [(historical, 'validation.json'), (current, 'validation.json'), (evidence, 'evidence_validation.json')]:
            result = json.loads((folder / marker).read_text())
            self.check('rebuild-marker-' + folder.name, result.get('ok') is True, marker=result)
        comparisons = [
            (historical, 'results/final/generated', ['closest_to_paper.csv', 'fixed_protocol_reference.csv',
                'selection_manifest.csv', 'coverage_72_cells.csv', 'batch_repeatability.csv']),
            (joint, 'results/submission_refresh', ['joint_metric_selection.csv', 'endpoint_comparison.csv',
                'all_joint_configurations.csv', 'all_native_endpoints.csv',
                'historical_repeatability_batches.csv', 'historical_repeatability_summary.csv']),
            (current, 'results/subset_search', ['joint_search_summary.csv', 'native_best_summary.csv',
                'fixed_protocol_summary.csv', 'closest_matches.csv', 'top_matches.csv',
                'fixed_protocol_distribution.csv', 'fixed_protocol_family_distributions.csv',
                'reference_contrasts.csv', 'matched_sc_summary.csv', 'matched_sc_contrasts.csv']),
            (evidence, 'results/submission_refresh', ['expanded_baseline_selection.csv',
                'expanded_baseline_native_selection.csv', 'baseline_source_native_diagnostics.csv'])]
        for rebuilt, committed, files in comparisons:
            for name in files:
                details = compare_csv(self.checkout / committed / name, rebuilt / name)
                self.check('csv-parity-' + rebuilt.name + '-' + name, True, **details)
        for benchmark in BENCHMARKS:
            name = benchmark + '.md'
            committed = self.checkout / 'results/subset_search' / name
            self.check('subset-markdown-parity-' + benchmark, committed.is_file()
                and committed.read_bytes() == (current / name).read_bytes())
        self.result['no_data_checks_environment'] = {'PYTHONPATH': None, 'COMP3314_DATA_ROOT': None, 'COMP3314_ARTIFACT_ROOT': None,
            'data_root_argument_supplied': False, 'external_artifact_argument_supplied': False,
            'scope': 'Commands use committed scalar release inputs; independent data is supplied only to the later real-data smoke.'}

    def real_smoke(self):
        destination = self.products / 'real data smoke'
        self.run('orl-jaffe-msra-real-smoke', [self.python, '-m', 'experiments.v3_reproduction',
            'run-experiments', '--config', 'configs/submission_refresh/reproduction_adapter.yaml',
            '--data-root', self.data, '--datasets', 'ORL_att92', 'JAFFE', 'MSRA25_EBSA_16x16',
            '--smoke', '--output', destination])
        record = json.loads((destination / 'smoke.json').read_text())
        datasets = {row['dataset_id']: row for row in record.get('datasets', [])}
        self.check('explicit-data-smoke-datasets', record.get('ok') is True
            and set(datasets) == {'ORL_att92', 'JAFFE', 'MSRA25_EBSA_16x16'})
        self.check('msra-preserves-native-full-source', datasets['MSRA25_EBSA_16x16']['shape'] == [1799, 256])
        self.result['real_smoke_scope'] = 'Three rounding seeds per method/dataset; loader/execution smoke, not new promoted results.'

    def real_candidate_replay(self):
        junit = self.products / 'real-candidate-replay.xml'
        program = '''import os,sys,pytest
os.environ["COMP3314_DATA_ROOT"]=sys.argv[1]
raise SystemExit(pytest.main(["-q","tests/submission_refresh/test_candidates.py","--junitxml",sys.argv[2],"-ra"]))
'''
        self.pytest_stage('real-candidate-replay', [self.python, '-c', program, self.data, junit], junit,
            expected_integration_skip=False)
        self.check('candidate-replay-data-override-confined-to-child', 'COMP3314_DATA_ROOT' not in self.env)

    def report(self):
        tools = {name: shutil.which(name, path=self.env['PATH']) for name in
            ['make', 'bash', 'mktemp', 'pdflatex', 'bibtex', 'pdfinfo', 'pdftotext', 'pdftoppm', 'pdftocairo']}
        self.check('report-tools-present', all(tools.values()), tools=tools)
        report = self.checkout / 'report/Group_23.pdf'
        self.check('committed-report-present', report.is_file()
            and self.before.get('report/Group_23.pdf') is not None)
        self.check('committed-report-unchanged-before-compile', sha(report) == self.before['report/Group_23.pdf'])
        committed_text_path = self.products / 'committed-report-text.txt'
        self.run('committed-pdf-text', [tools['pdftotext'], '-layout', report, committed_text_path])
        committed_text = committed_text_path.read_text()
        self.check('committed-report-text-nonempty', bool(committed_text.strip()))
        self.result['committed_report_text_sha256'] = sha(committed_text_path)
        self.run('compile-report', [tools['make'], '-C', 'report', 'all', 'PYTHON=' + str(self.python),
            'REPORT_DATE=' + self.args.report_date])
        info = self.run('pdf-info', [tools['pdfinfo'], report], capture=True)
        (self.products / 'report-pdfinfo.txt').write_text(info)
        text_path = self.products / 'report-text.txt'
        self.run('pdf-text', [tools['pdftotext'], '-layout', report, text_path])
        text = text_path.read_text()
        normalize_whitespace = lambda value: ' '.join(value.split())
        self.check('committed-and-regenerated-pdf-text-parity',
            normalize_whitespace(committed_text) == normalize_whitespace(text),
            committed_text_sha256=sha(committed_text_path), regenerated_text_sha256=sha(text_path),
            comparison='case-sensitive exact text after whitespace normalization; binary PDF metadata may differ')
        pages = text.split('\f')
        if pages and not pages[-1].strip(): pages.pop()
        main = (self.checkout / 'report/main.tex').read_text()
        appendix = re.search(r'\\appendix\s*\\section\{([^}]+)\}', main)
        self.check('appendix-boundary-declared', appendix is not None)
        normalize = lambda value: ' '.join(value.split()).casefold()
        heading = normalize(appendix.group(1))
        boundaries = [i for i, page in enumerate(pages) if heading in normalize(page)]
        self.check('appendix-boundary-found-once', len(boundaries) == 1, pages=[i + 1 for i in boundaries])
        aux = self.checkout / 'report/main.aux'
        main_boundary = report_main_boundaries(main,aux.read_text())
        main_pages = main_boundary['main_pages']
        self.check('main-and-references-source-order',True,**main_boundary)
        appendix_page = boundaries[0] + 1
        page_count = re.search(r'^Pages:\s+(\d+)\s*$', info, re.M)
        self.check('four-page-main-limit', page_count is not None and int(page_count.group(1)) == len(pages)
            and main_boundary['within_four_page_limit'], **main_boundary,total_pages=len(pages),references_excluded=True,
            aux_sha256=sha(aux))
        self.check('appendix-follows-main', main_boundary['references_start_page']<=appendix_page<=len(pages),
            appendix_first_page=appendix_page, main_end_page=main_pages,
            intervening_preappendix_pages=appendix_page - main_pages - 1)
        self.check('preprint-template-retained', r'\usepackage[preprint]{neurips_2026}' in main)
        authors = ['Han Jiale', 'Lu Sinan', 'Mahatharadol Vie', 'Mai Sheung Ying']
        self.check('four-author-identities-retained', all(normalize(name) in normalize(text) for name in authors), authors=authors)
        self.check('two-graph-diagram-retained', 'figures/ssc_two_graph_pipeline.pdf' in main
            and (self.checkout / 'report/figures/ssc_two_graph_pipeline.pdf').is_file())
        compile_log = (self.checkout / 'report/main.log').read_text(errors='replace')
        undefined = re.findall(r'(?:undefined references|undefined citations|(?:Citation|Reference)[^\n]*undefined)', compile_log, re.I)
        self.check('no-undefined-citations-or-references', not undefined, matches=undefined)
        cjk = re.findall(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]', text)
        self.check('pdf-no-cjk-prose-flags', not cjk, flag_count=len(cjk),
            qualification='Character check only; final natural-language and visual review remains separate.')
        rendered = self.products / 'rendered report pages'
        rendered.mkdir()
        self.run('render-every-pdf-page', [tools['pdftoppm'], '-r', '110', '-png', report, rendered / 'page'])
        images = sorted(rendered.glob('page-*.png'))
        self.check('rendered-page-count', len(images) == len(pages), count=len(images))
        self.result['report'] = {'compiled_pdf_sha256': sha(report),
            'committed_pdf_sha256': self.before.get('report/Group_23.pdf'),
            'main_pages': main_pages, 'total_pages': len(pages),
            'main_page_source': main_boundary['main_page_source'],
            'body_end_page':main_boundary['body_end_page'],'references_start_page':main_boundary['references_start_page'],
            'appendix_first_page': appendix_page, 'compiled_aux_sha256': sha(aux),
            'committed_text_sha256': sha(committed_text_path),
            'committed_and_regenerated_text_match': True,
            'text_sha256': sha(text_path), 'rendered_pages': {str(p.relative_to(self.output)): sha(p) for p in images},
            'visual_review_status': 'SEPARATE_REVIEW_REQUIRED',
            'binary_pdf_equality_required': False, 'binary_pdf_note': 'TeX PDF creation metadata may differ; committed/regenerated text parity and generated table sources are checked.'}
        for name, before in self.before.items():
            if name.startswith('report/tables/refresh_') and name.endswith('.tex'):
                self.check('report-table-parity-' + Path(name).name, sha(self.checkout / name) == before)

    def final_source_check(self):
        protected = [name for name in self.before if name.startswith(('SSC_method/', 'baselines/',
            'benchmarks/', 'method_extension/', 'experiments/', 'configs/', 'scripts/'))
            or name in ['pyproject.toml', 'environment/requirements.lock.txt', 'report/main.tex',
                'report/references.bib', 'report/neurips_2026.sty',
                'report/figures/ssc_two_graph_pipeline.tikz', 'report/figures/ssc_two_graph_pipeline.tex']]
        changed = [name for name in protected if not (self.checkout / name).is_file()
            or sha(self.checkout / name) != self.before[name]]
        self.check('tested-source-and-configuration-unchanged', not changed, paths=changed)
        self.result['final_local_status'] = self.run('final-checkout-status', ['git', 'status', '--porcelain'], capture=True)
        self.result['tested_commit'] = self.result['observed_commit']

    def execute(self):
        try:
            self.verify_checkout()
            self.environment()
            self.focused_regressions()
            self.no_data_rebuilds()
            self.real_smoke()
            if self.args.real_candidate_replay:
                self.real_candidate_replay()
            else:
                self.result['real-candidate-replay'] = {'status': 'NOT_REQUESTED',
                    'qualification': 'Enable --real-candidate-replay only when the independent data root includes the declared AR/UMIST/BinAlpha parents.'}
            self.report()
            self.final_source_check()
            self.result.update(status='PASSED', acceptance_passed=True,
                scope='Exact-commit isolated computational acceptance. Visual PDF review, external/live links and publication checks remain separate.')
            return 0
        except BaseException as exc:
            self.result.update(status='TIMEOUT' if isinstance(exc, BudgetExceeded) else 'FAILED',
                acceptance_passed=False, error=repr(exc))
            return 1
        finally:
            self.result['ended_at_utc'] = utc()
            self.save()


def repository_argument(value):
    if value.startswith('https://'):
        parsed = urllib.parse.urlsplit(value)
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('repository HTTPS URL must not contain credentials, query or fragment')
        return value
    if '://' in value or value.startswith('git@'):
        raise ValueError('use an explicit local repository path or credential-free HTTPS URL')
    path = Path(value).expanduser().resolve()
    if not path.is_dir(): raise ValueError('local repository path does not exist')
    return str(path)


def _equivalent(left, right):
    if left == right: return True
    try:
        a, b = float(left), float(right)
        return math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=0, abs_tol=1e-9)
    except (ValueError, TypeError):
        pass
    try:
        a, b = json.loads(left), json.loads(right)
        return a == b
    except (ValueError, TypeError):
        return False


def compare_csv(committed, rebuilt):
    """Compare deterministic CSV views, allowing only numeric serialization noise."""
    def read(path):
        with Path(path).open(newline='') as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            rows = list(reader)
        if not fields or not rows: raise ValueError('empty acceptance CSV: ' + str(path))
        return fields, rows
    fields, left = read(committed)
    other, right = read(rebuilt)
    if set(fields) != set(other) or len(left) != len(right):
        raise ValueError('rebuilt CSV schema/count mismatch: ' + str(committed))
    # Generated views have a declared deterministic row order. Keeping that
    # order also catches a changed tie break, not merely changed numbers.
    for index, (a, b) in enumerate(zip(left, right)):
        for field in fields:
            if not _equivalent(a[field], b[field]):
                raise ValueError(f'rebuilt CSV value/order mismatch: {committed}, row {index + 1}, {field}')
    return {'committed': str(committed), 'rebuilt': str(rebuilt), 'rows': len(left),
        'columns': fields, 'committed_sha256': sha(committed), 'rebuilt_sha256': sha(rebuilt),
        'numeric_absolute_tolerance': 1e-9}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--branch', required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--data-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--cpu-limit', type=float, default=900)
    parser.add_argument('--wall-limit', type=float, default=1800)
    parser.add_argument('--report-date', default='2026-11-10')
    parser.add_argument('--real-candidate-replay', action='store_true',
        help='Run the explicit real-source candidate replay after the no-data stages and real smoke')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[0-9a-fA-F]{40}', args.expected_commit):
        parser.error('--expected-commit must be the full 40-character commit SHA')
    if not args.branch or args.branch.startswith('-') or re.search(r'[\s~^:?*\[\\]', args.branch):
        parser.error('invalid explicit branch name')
    if not 0 < args.cpu_limit <= 900 or not 0 < args.wall_limit <= 1800:
        parser.error('acceptance limits must be positive and at most 900 CPU / 1800 wall seconds')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.report_date):
        parser.error('--report-date must use YYYY-MM-DD')
    def interrupted(signum, _frame):
        if signum == signal.SIGXCPU: raise BudgetExceeded('CPU_LIMIT_SIGNAL')
        raise InterruptedError('acceptance interrupted by signal ' + str(signum))
    for signum in [signal.SIGTERM, signal.SIGINT, signal.SIGXCPU]: signal.signal(signum, interrupted)
    try:
        acceptance = Acceptance(args)
        code = acceptance.execute()
        print(json.dumps({'status': acceptance.result['status'], 'expected_commit': args.expected_commit,
            'observed_commit': acceptance.result.get('observed_commit'),
            'evidence': str(acceptance.output / 'acceptance.json'),
            'visual_review_status': acceptance.result['visual_review_status']}, sort_keys=True))
        return code
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
