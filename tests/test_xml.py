from mrf.xml import *
import unittest
import xml.dom.minidom

    
class NodeTest(unittest.TestCase):
    
    def setUp(self):
        self.doc = xml.dom.minidom.getDOMImplementation().createDocument(None, None, None)
    
    def test_passing_in_node_object_returns_it(self):
        n = self.doc.createElement('foo')
        result = node(self.doc, None, n)
        self.assertEqual('foo', result.nodeName)

    def test_passing_in_string_returns_textnode(self):
        result = node(self.doc, None, 'hello')
        self.assertTrue(isinstance(result, xml.dom.minidom.Text))
        self.assertEqual('hello', result.nodeValue)
        
    def test_element_spec_with_name_only(self):
        result = node(self.doc, None, ('hello',))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual(None, result.namespaceURI)
        self.assertEqual('hello', result.nodeName)
        self.assertEqual(False, result.hasAttributes())
        self.assertEqual(0, len(result.childNodes))
        
    def test_element_spec_with_namespace_and_name(self):
        result = node(self.doc, {'tst': 'foobar'}, ('tst:blah',))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual('foobar', result.namespaceURI)
        self.assertEqual('blah', result.nodeName)
        self.assertEqual(False, result.hasAttributes())
        self.assertEqual(0, len(result.childNodes))
        
    def test_element_spec_with_non_namespaced_attributes(self):
        result = node(self.doc, None, ('test', {'alpha': 'apple', 'beta': 'banana'}))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual(None, result.namespaceURI)
        self.assertEqual('test', result.nodeName)
        self.assertEqual(True, result.hasAttributes())
        self.assertEqual('apple', result.getAttribute('alpha'))
        self.assertEqual('banana', result.getAttribute('beta'))
        self.assertEqual(0, len(result.childNodes))
    
    def test_element_spec_with_namespaced_attributes(self):
        result = node(self.doc, {'c': 'cakes', 'b': 'biscuits'}, 
            ('test', {'c:battenberg': 'apple', 'b:bourbon': 'banana'}))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual(None, result.namespaceURI)
        self.assertEqual('test', result.nodeName)
        self.assertEqual(True, result.hasAttributes())
        self.assertEqual('apple', result.getAttributeNS('cakes', 'battenberg'))
        self.assertEqual('banana', result.getAttributeNS('biscuits', 'bourbon'))
        self.assertEqual(0, len(result.childNodes))

    def test_element_spec_with_child_elements(self):
        result = node(self.doc, None, ('test', ('foo', ), ('bar', )))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual(None, result.namespaceURI)
        self.assertEqual('test', result.nodeName)
        self.assertEqual(False, result.hasAttributes())
        self.assertEqual(2, len(result.childNodes))
        self.assertEqual('foo', result.childNodes[0].nodeName) 
        self.assertEqual('bar', result.childNodes[1].nodeName)
        
    def test_element_spec_with_child_text_nodes(self):
        result = node(self.doc, None, ('test', 'foo', 'bar'))
        self.assertTrue(isinstance(result, xml.dom.minidom.Element))
        self.assertEqual(None, result.namespaceURI)
        self.assertEqual('test', result.nodeName)
        self.assertEqual(False, result.hasAttributes())
        self.assertEqual(2, len(result.childNodes))
        self.assertEqual('foo', result.childNodes[0].nodeValue)
        self.assertEqual('bar', result.childNodes[1].nodeValue)


class DocTest(unittest.TestCase):

    def test_creates_doc_without_doctype(self):
        result = doc()
        self.assertTrue(isinstance(result, xml.dom.minidom.Document))

    def test_creates_doc_with_root(self):
        result = doc(root_spec=('cake',))
        self.assertTrue(isinstance(result, xml.dom.minidom.Document))
        self.assertTrue(isinstance(result.documentElement, xml.dom.minidom.Element))
        self.assertEqual('cake', result.documentElement.nodeName)
        self.assertEqual(None, result.documentElement.namespaceURI)
        
    def test_creates_doc_with_root_and_doctype(self):
        result = doc(('foo', 'bar', 'meh'), root_spec=('cake',))
        self.assertTrue(isinstance(result, xml.dom.minidom.Document))
        self.assertEqual('foo', result.doctype.name)
        self.assertEqual('bar', result.doctype.publicId)
        self.assertEqual('meh', result.doctype.systemId)
        
    def test_creates_doc_with_namespaced_root(self):
        result = doc(ns_map={'c': 'lovely'}, root_spec=('c:cake',))
        self.assertTrue(isinstance(result, xml.dom.minidom.Document))
        self.assertTrue(isinstance(result.documentElement, xml.dom.minidom.Element))
        self.assertEqual('cake', result.documentElement.nodeName)
        self.assertEqual('lovely', result.documentElement.namespaceURI)


class XhtmlTest(unittest.TestCase):

    def test_creates_document(self):
        result = xhtml()
        self.assertTrue(isinstance(result, xml.dom.minidom.Document))
        
    def test_sets_doctype(self):
        result = xhtml()
        self.assertEqual('html', result.doctype.name)
        self.assertEqual('-//W3C//DTD XHTML 1.0 Strict//EN', result.doctype.publicId)
        self.assertEqual('http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd', result.doctype.systemId)

    def test_creates_root(self):
        result = xhtml()
        self.assertTrue(isinstance(result.documentElement, xml.dom.minidom.Element))
        self.assertEqual('html', result.documentElement.nodeName)

    def test_creates_child_elements(self):
        result = xhtml(('head',), ('body',))
        self.assertEqual(2, len(result.documentElement.childNodes))
        self.assertEqual('head', result.documentElement.childNodes[0].nodeName)
        self.assertEqual('body', result.documentElement.childNodes[1].nodeName)
        
    def test_creates_child_text_nodes(self):
        result = xhtml('this is', 'a test')
        self.assertEqual(2, len(result.documentElement.childNodes))
        self.assertEqual('this is', result.documentElement.childNodes[0].nodeValue)
        self.assertEqual('a test', result.documentElement.childNodes[1].nodeValue)
        
        
        
        

