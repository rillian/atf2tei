#!/usr/bin/env python3

# -*- coding: utf-8 -*-

import re
from xml.sax.saxutils import escape

from pyoracc.atf.common.atffile import AtfFile
from pyoracc.model.line import Line
from pyoracc.model.oraccobject import OraccObject
from pyoracc.model.translation import Translation

verbose = False


def convert(atf_text):
    """
    Create a TEI representation of a file-like object containing ATF.
    """
    atf = AtfFile(atf_text, 'cdli', False)
    if verbose:
        print("Parsed {} -- {}".format(atf.text.code, atf.text.description))
    result = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">

<teiHeader>
<fileDesc>
  <titleStmt>
    <title>{description}</title>
  </titleStmt>
  <publicationStmt>
    <p>Converted from ATF by atf2tei.</p>
  </publicationStmt>
  <sourceDesc>
    <idno type="CDLI">{code}</idno>
  </sourceDesc>
</fileDesc>
<encodingDesc>
  <refsDecl n="CTS">
    <cRefPattern n="line"
                 matchPattern="(\\w+)\\.(\\w+)\\.(\\w+)"
                 replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\'$1\']/tei:div[@n=\'$2\']/tei:l[@n=\'$3\'])">
      <p>This pointer pattern extracts a specific line.</p>
    </cRefPattern>
    <cRefPattern n="surface"
                 matchPattern="(\\w+)\\.(\\w+)"
                 replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\'$1\']/tei:div[@n=\'$2\'])">
      <p>This pointer pattern extracts an inscribed surface.</p>
    </cRefPattern>
    <cRefPattern n="object"
                 matchPattern="(\\w+)"
                 replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\'$1\'])">
      <p>This pointer pattern extracts a specific artefact,
         usually a tablet.</p>
    </cRefPattern>
  </refsDecl>
</encodingDesc>
</teiHeader>
'''.format(description=escape(atf.text.description),
           code=escape(atf.text.code))
    urn = f'urn:cts:cdli:test.{atf.text.code}'
    result += f'<text n="{urn}"'
    if atf.text.language:
        result += f' xml:lang="{atf.text.language}"'
    result += '>\n'
    result += '<body>\n'
    translations = {}
    objects = [item for item in atf.text.children
               if isinstance(item, OraccObject)]
    result += '''  <div type="edition">\n'''
    for item in objects:
        result += f'  <div type="textpart" n="{item.objecttype}">\n'
        for section in item.children:
            if isinstance(section, OraccObject):
                result += '    <div type="textpart"' \
                          f' n="{section.objecttype}">\n'
            elif isinstance(section, Translation):
                # Handle in another pass.
                continue
            else:
                result += '    <div>\n' \
                         f'<!-- {type(section).__name__}: {section} -->\n'
            for line in section.children:
                if isinstance(line, Line):
                    text = normalize_transliteration(line.words)
                    result += f'      <l n="{line.label}">{text}</l>\n'
                    # Older pyoracc parses interlinear translatsions
                    # as notes. Remember them for serialization below.
                    for note in line.notes:
                        if note.content.startswith('tr.'):
                            lang, text = note.content.split(':', maxsplit=1)
                            _, lang = lang.split('.')
                            # tr.ts is used for normalization, so mark
                            # this with the primary object's language.
                            if lang == 'ts':
                                lang == atf.text.language
                            tr_line = Line(line.label)
                            tr_line.words = text.strip().split()
                            if lang not in translations:
                                translations[lang] = []
                            translations[lang].append(tr_line)
                else:
                    result += f'      <!-- {type(line).__name__}: {line} -->\n'
            result += '    </div>\n'
        result += '  </div>\n'
    result += '  </div>\n'
    objects = [item for item in atf.text.children
               if isinstance(item, OraccObject)]
    result += '  <div type="translation">\n'
    for item in objects:
        result += f'    <div type="textpart" n="{item.objecttype}">\n'
        for section in item.children:
            # Skip anything which is not a translation for this pass.
            if not isinstance(section, Translation):
                continue
            for surface in section.children:
                result += f'      <div type="textpart" ' \
                          f'n="{surface.objecttype}">\n'
                if isinstance(surface, OraccObject):
                    for line in surface.children:
                        if isinstance(line, Line):
                            text = ' '.join(line.words)
                            result += '        ' \
                                      f'<l n="{line.label}">{text}</l>\n'
                        else:
                            result += '        <!-- ' \
                                      f'{type(line).__name__}: {line} -->\n'
                    result += '      </div>\n'
        result += '    </div>\n'
    result += '  </div>\n'
    for lang, translation in translations.items():
        result += f'  <div type="translation" xml:lang="{lang}">\n'
        for line in translation:
            text = ' '.join(line.words)
            result += f'    <l n="{line.label}">{escape(text)}</l>\n'
        result += '  </div>\n'
    result += '''
</body>
</text>
</TEI>'''
    return result


def normalize_transliteration(words):
    '''Convert a sequence of words from atf to standard formatting.'''
    # See http://oracc.org/doc/help/editinginatf/primer/inlinetutorial/
    result = []
    for word in words:
        '''Convert digraphs to corresponding unicode characters.'''
        word = re.sub(r'sz', 'š', word)     # \u0161
        word = re.sub(r'SZ', 'Š', word)     # \u0160
        word = re.sub(r's,', 'ṣ', word)     # \u1E63
        word = re.sub(r'S,', 'Ṣ', word)     # \u1E62
        word = re.sub(r't,', 'ṭ', word)     # \u1E6D
        word = re.sub(r'T,', 'Ṭ', word)     # \u1E6C
        word = re.sub(r's\'', 'ś', word)    # \u015B
        word = re.sub(r'S\'', 'Ś', word)    # \u015A
        word = re.sub(r'h,', 'ḫ', word)     # \u1E2B
        word = re.sub(r'H,', 'Ḫ', word)     # \u1E2A
        word = re.sub(r'j', 'ŋ', word)      # \u014B
        word = re.sub(r'J', 'Ŋ', word)      # \u014A
        '''XML-escape the result.'''
        word = escape(word)
        '''Convert markup to tei elements.'''
        word = re.sub(r'{([^{}]+)}',
                      r'<c type="determinative">\1</c>',
                      word)
        word = re.sub(r'_([\w<{([\|.]+)',
                      r'<c type="sign" subtype="logo">\1',
                      word)
        word = re.sub(r'([\w)}>\|\.#\?]+)_', r'\1</c>', word)
        result.append(word)
    return ' '.join(result)


if __name__ == '__main__':
    import io
    import sys
    for filename in sys.argv[1:]:
        with io.open(filename, encoding='utf-8') as f:
            xml = convert(f.read())
            print(xml)
