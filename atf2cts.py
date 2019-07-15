#!/usr/bin/env python3

from xml.dom.minidom import parseString

import atf2tei
import cts


def segmentor(fp):
    'Read a file object and segment it into atf records.'
    atf = None
    sync = False
    for line in fp.readlines():
        if line.startswith('&'):
            print('New atf record: ', line.strip())
            # Start of a new record. Flush the old one, if any.
            if atf and sync:
                yield atf
            atf = line
            sync = True
        else:
            atf += line
    if atf and sync:
        yield atf


def convert(atf, data_path):
    '''Convert an atf string and write it out as XML.

    returns a (success, parse_failed, export_failed) flag tuple.'''
    success = (True, False, False)
    parse_failed = (False, True, False)
    export_failed = (False, False, True)
    try:
        doc = atf2tei.convert(atf)
    except Exception as e:
        print('Error converting ATF:', e)
        print(atf)
        return parse_failed
    try:
        dom = parseString(str(doc))
    except Exception as e:
        print('Error parsing converted XML:', e)
        print(doc)
        return export_failed
    texts = dom.getElementsByTagName('text')
    assert len(texts) == 1
    text = texts[0]
    urn = text.getAttribute('n')
    lang = text.getAttribute('xml:lang')
    title = dom.getElementsByTagName('title')[0].firstChild.data

    doc_basename = urn.split(':')[-1]
    doc_dirname = doc_basename.split('.')[-1]
    doc_path = os.path.join(data_path, doc_dirname)
    doc_filename = os.path.join(
            doc_path, doc_basename + '.' + lang + '.xml')
    print('Writing', urn, lang, 'to', doc_filename)

    work = cts.Work()
    work.group_urn = textgroup.urn
    work.work_urn = urn
    work.language = lang
    work.description = 'Test doc converted from atf.'
    work.label = ' '.join(['CDLI', doc_dirname, title])
    work.title = title

    os.makedirs(doc_path, exist_ok=True)
    with io.open(os.path.join(doc_path, '__cts__.xml'),
                 encoding='utf-8',
                 mode='w') as f:
        f.write(str(work))

    with io.open(doc_filename, encoding='utf-8', mode='w') as f:
        f.write(str(doc))

    return success


if __name__ == '__main__':
    import io
    import os
    import sys

    from concurrent import futures
    from datetime import datetime

    start = datetime.utcnow()
    failed_parse = []
    failed_export = []
    successful = 0
    parse_failures = 0
    export_failures = 0

    data_path = 'data/test'
    os.makedirs(data_path, exist_ok=True)
    textgroup = cts.TextGroup()
    textgroup.urn = 'urn:cts:cdli:test'
    textgroup.name = 'atf2cts test examples'
    with io.open(os.path.join(data_path, '__cts__.xml'),
                 encoding='utf-8',
                 mode='w') as f:
        f.write(str(textgroup))

    for filename in sys.argv[1:]:
        print('Parsing:', filename)
        with io.open(filename, encoding='utf-8') as f:
            with futures.ProcessPoolExecutor() as exe:
                jobs = [exe.submit(convert, atf, data_path)
                        for atf in segmentor(f)]
                for job in futures.as_completed(jobs):
                    s, p, e = job.result()
                    successful += s
                    parse_failures += p
                    export_failures += e
    if parse_failures:
        print('Error:', parse_failures, 'records did not convert.')
    if failed_export:
        print('Error:', export_failures, 'records did not serialize.')
    elapsed = datetime.utcnow() - start
    seconds = elapsed.seconds + elapsed.microseconds*1e-6
    print(f'Successfully converted {successful} records from ATF',
          f'in {seconds:0.3f} seconds.')
