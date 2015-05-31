from mrf.xml import *
import unittest

    
class NodeTest(unittest.TestCase):
    
    def test_passing_in_node_object_returns_it(self):
        doc = xml.dom.minidom.getDOMImplementation().createDocument(None, None, None)
        n = doc.createElement('foo')
        result = node(doc, n)
        self.assertEqual('foo', result.nodeName)


