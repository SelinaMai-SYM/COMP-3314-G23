"""Verified CSV transport; compression never changes logical CSV bytes.

This module is deliberately standard-library-only so the fresh-checkout
acceptance harness can load it before installing the project. It does not
interpret metrics, change selection or read scientific arrays.
"""
from __future__ import annotations
from contextlib import contextmanager
import csv
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zlib

DEFAULT_MIN_BYTES = 90 * 1024 ** 2


def _forms(path):
    path = Path(path)
    if path.name.endswith('.csv.gz'):
        plain = path.with_suffix('')
    elif path.suffix == '.csv':
        plain = path
    else:
        raise ValueError('CSV transport requires a .csv or .csv.gz path: ' + str(path))
    return plain, plain.with_name(plain.name + '.gz')


def _present(path):
    return path.exists() or path.is_symlink()


def resolve_csv(path, required=False):
    """Return the sole existing representation, or None for an absent optional.

    Both representations are always an error, including calls with actual.gz.
    An invalid existing plain path is never bypassed in favor of gzip.
    """
    plain, compressed = _forms(path)
    found = [item for item in (plain, compressed) if _present(item)]
    if len(found) > 1:
        raise ValueError('ambiguous CSV transport: both plain and gzip exist: ' + str(plain))
    if found:
        if not found[0].is_file():
            raise ValueError('existing CSV transport is not a readable file: ' + str(found[0]))
        return found[0]
    if required:
        raise FileNotFoundError('CSV transport is absent: ' + str(plain))
    return None


@contextmanager
def open_csv(path, mode='rt', newline=''):
    """Read UTF-8 CSV text from its unique representation, without fallback."""
    if mode not in ('r', 'rt'):
        raise ValueError('open_csv supports read-only text modes r/rt')
    actual = resolve_csv(path, required=True)
    opener = gzip.open if actual.name.endswith('.csv.gz') else open
    former_limit = csv.field_size_limit()
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max(former_limit, limit))
            break
        except OverflowError:
            limit //= 10
    try:
        with opener(actual, 'rt', encoding='utf-8', newline=newline) as stream:
            yield stream
    finally:
        csv.field_size_limit(former_limit)


def _sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _raw_info(path):
    compressed = Path(path).name.endswith('.csv.gz')
    opener = gzip.open if compressed else open
    h = hashlib.sha256()
    length = 0
    with opener(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            length += len(block)
    return h.hexdigest(), length


def _validate(path):
    """Validate structure/UTF-8/CRC without interpreting scientific values."""
    before = _sha(path)
    try:
        with open_csv(path) as stream:
            reader = csv.reader(stream, strict=True)
            fields = next(reader, None)
            if not fields or any(not field or '\0' in field for field in fields) or len(fields) != len(set(fields)):
                raise ValueError('empty or invalid CSV header: ' + str(path))
            count = 0
            for row in reader:
                if len(row) != len(fields) or any('\0' in value for value in row):
                    raise ValueError('malformed CSV row: ' + str(path))
                count += 1
            if not count:
                raise ValueError('empty CSV body: ' + str(path))
        raw_hash, raw_bytes = _raw_info(path)
        if _sha(path) != before:
            raise ValueError('CSV transport changed during validation: ' + str(path))
    except (OSError, EOFError, UnicodeError, csv.Error, zlib.error) as exc:
        raise ValueError('invalid or corrupt CSV transport: ' + str(path)) from exc
    return {'uncompressed_sha256': raw_hash, 'uncompressed_bytes': raw_bytes,
            'row_count': count, 'column_count': len(fields)}


def copy_plain_csv(source, destination):
    """Atomically materialize exact CSV bytes; corrupt gzip never replaces output."""
    actual = resolve_csv(source, required=True)
    destination = Path(destination)
    if destination.suffix != '.csv':
        raise ValueError('plain CSV destination must end in .csv')
    if actual.resolve() == destination.resolve():
        _validate(actual)
        return destination
    if _present(destination.with_name(destination.name + '.gz')):
        raise ValueError('plain destination would create ambiguous CSV transport')
    _validate(actual)
    before = _sha(actual)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix='.csv-copy-', dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        opener = gzip.open if actual.name.endswith('.csv.gz') else open
        with os.fdopen(handle, 'wb') as target, opener(actual, 'rb') as stream:
            shutil.copyfileobj(stream, target)
            target.flush()
            os.fsync(target.fileno())
        if _sha(actual) != before or _raw_info(actual) != (_sha(temporary), temporary.stat().st_size):
            raise ValueError('CSV source changed during materialization')
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def pack_large_csvs(directory, min_bytes=DEFAULT_MIN_BYTES, names=None):
    """Pack selected CSVs deterministically after validating every input.

    Existing gzip files are validated and inventoried, never overwritten.
    All staging/verification completes before any plain file is replaced.
    ``names`` limits transport to safe basenames, including optional inputs.
    Returned paths are filenames relative to ``directory``.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError('CSV transport directory must exist')
    if isinstance(min_bytes, bool) or not isinstance(min_bytes, int) or min_bytes < 0:
        raise ValueError('CSV compression threshold must be a nonnegative integer')
    if names is None:
        logical = sorted({(_forms(path)[0]).name for path in directory.iterdir()
                          if path.name.endswith(('.csv', '.csv.gz'))})
    else:
        logical = []
        for name in names:
            name = str(name)
            if Path(name).name != name or name in ('', '.', '..'):
                raise ValueError('CSV names must be safe basenames')
            logical.append(_forms(Path(name))[0].name)
        if len(logical) != len(set(logical)):
            raise ValueError('duplicate logical CSV names')
        logical.sort()
    records = []
    staged = []
    observed = []
    with tempfile.TemporaryDirectory(prefix='.csv-transport-', dir=directory) as work:
        for name in logical:
            actual = resolve_csv(directory / name, required=names is not None)
            if actual is None:
                continue
            physical_hash = _sha(actual)
            info = _validate(actual)
            if _sha(actual) != physical_hash:
                raise ValueError('CSV transport changed during packing validation: ' + str(actual))
            observed.append((actual, physical_hash))
            record = {'csv_path': name, 'transport_path': actual.name, **info}
            if actual.name.endswith('.csv.gz'):
                record.update(status='EXISTING_GZIP', compressed_sha256=physical_hash,
                              compressed_bytes=actual.stat().st_size)
            elif actual.stat().st_size < min_bytes:
                record.update(status='UNCHANGED_PLAIN', compressed_sha256=None, compressed_bytes=None)
            else:
                before = _sha(actual)
                target = directory / (name + '.gz')
                temporary = Path(work) / target.name
                with actual.open('rb') as stream, temporary.open('wb') as raw:
                    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
                        shutil.copyfileobj(stream, compressed)
                    raw.flush()
                    os.fsync(raw.fileno())
                verified = _validate(temporary)
                if verified != info or before != _sha(actual):
                    raise ValueError('CSV changed or gzip verification failed before publication: ' + name)
                record.update(status='PACKED_GZIP', transport_path=target.name,
                              compressed_sha256=_sha(temporary), compressed_bytes=temporary.stat().st_size)
                staged.append((actual, target, temporary, before))
            records.append(record)
        # No earlier file is packed if a later selected input is invalid.
        if any(_sha(path) != wanted for path, wanted in observed):
            raise ValueError('CSV transport changed before publication')
        for actual, target, temporary, before in staged:
            if _present(target) or _sha(actual) != before:
                raise ValueError('CSV transport target exists or input changed before publication: ' + str(actual))
        for actual, target, temporary, before in staged:
            os.link(temporary, target)  # Atomic create, never replace an unknown transport.
            actual.unlink()
    return records
