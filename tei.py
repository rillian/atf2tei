'''Models for generating Epidoc Text Encoding Initiative xml files.'''

import io
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

namespace = 'http://www.tei-c.org/ns/1.0'


class XMLSerializer:
    '''Mixin for XML serialization.

    Override the xml property to return an ElementTree representation
    of the object's data. This class will provide a __str__ method
    to serialize it in a uniform way.'''
    xml = None

    def __str__(self):
        'Serialized XML representation as a string.'
        serialized = ET.tostring(self.xml, encoding='unicode')
        # Run the xml through minidom to control the indent.
        return parseString(serialized).toprettyxml(indent='  ')

    def write(self, filename):
        'Write a serialized representation to the given file path.'
        with io.open(filename, encoding='utf-8', mode='w') as f:
            f.write(str(self))


class Document(XMLSerializer):
    '''Represents a TEI document.'''

    def __init__(self):
        self.header = None
        self.parts = []
        self.language = None

    @property
    def xml(self):
        'Construct an XML representation of member data.'
        xml = ET.Element('TEI')
        xml.set('xmlns', namespace)
        if self.header:
            xml.append(self.header.xml)
        text = ET.SubElement(xml, 'text')
        body = ET.SubElement(text, 'body')
        for part in self.parts:
            body.append(part.xml)
        return xml


class Header(XMLSerializer):
    '''Represents a TEI Header.'''

    def __init__(self):
        self.title = None
        self.publication = 'Converted from ATF by atf2tei.'
        self.cdli_code = None
        self.encodingDesc = None

    @property
    def xml(self):
        'Construct an XML ElementTree representation of member data.'
        xml = ET.Element('teiHeader')
        fileDesc = ET.SubElement(xml, 'fileDesc')
        titleStmt = ET.SubElement(fileDesc, 'titleStmt')
        title = ET.SubElement(titleStmt, 'title')
        title.text = self.title
        if self.publication:
            publicationStmt = ET.SubElement(fileDesc, 'publicationStmt')
            p = ET.SubElement(publicationStmt, 'p')
            p.text = self.publication
        if self.cdli_code:
            sourceDesc = ET.SubElement(fileDesc, 'sourceDesc')
            bibl = ET.SubElement(sourceDesc, 'bibl')
            title = ET.SubElement(bibl, 'title')
            title.text = 'CDLI'
            idno = ET.SubElement(title, 'idno')
            idno.set('type', 'CDLI')
            idno.text = self.cdli_code
        if self.encodingDesc:
            xml.append(self.encodingDesc)
        return xml


class TextPart(XMLSerializer):
    '''Represents an Epidoc text division.

    Set the name attribute to book, chapter, obverse, etc.,
    whatever describes the division.'''

    def __init__(self, name=None):
        self.name = name
        self.type = 'textpart'
        self.language = None
        self.children = []
        # Attributes for CTS metadata.
        self.label = None
        self.description = None

    def append(self, obj):
        'Append a sub-element to the list of children.'
        self.children.append(obj)

    @property
    def xml(self):
        'Construct an XML ElementTree representation.'
        xml = ET.Element('div')
        xml.set('type', self.type)
        if self.name:
            xml.set('n', self.name)
        if self.language:
            xml.set('xml:lang', self.language)
        for child in self.children:
            xml.append(child.xml)
        return xml


class Edition(TextPart):
    '''Represents an Epidoc text edition.

    Set the name attribute to the CTS urn.'''

    def __init__(self):
        super().__init__()
        self.type = 'edition'


class Translation(TextPart):
    '''Represents an Epidoc text translation.

    Set the name attribute to the CTS urn.
    Set the language attribute to the language of the translation.'''

    def __init__(self):
        super().__init__()
        self.type = 'translation'


class Line(XMLSerializer):
    '''Represents a line of text.'''
    def __init__(self, ref, content):
        self.ref = ref
        self.content = content

    @property
    def xml(self):
        'Construct an XML ElementTree representation.'
        xml = ET.Element('l')
        xml.set('n', self.ref)
        xml.text = self.content
        return xml


class Note(XMLSerializer):
    '''Represents an annotation.'''
    def __init__(self, text):
        self.text = text

    @property
    def xml(self):
        'Construct an XML ElementTree representation.'
        xml = ET.Element('note')
        xml.text = self.text
        return xml
