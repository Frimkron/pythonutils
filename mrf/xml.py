"""    
Copyright (c) 2015 Mark Frimston

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

---------------------

XML Module

Utilities for manipulating XML documents
"""

from __future__ import absolute_import
import xml.dom.minidom


def doc(namespace_uri=None, doctype=None, root_spec=None):
    """Create and return a new DOM document with the given namespace_uri, doctype, and nodes.
       doctype is a 3-tuple consisting of the name, publicid and systemid.
       root_spec is either a Node object, or a sequence decribing the root element, consisting of:
         Optional namespace uri as a string
         Name as a string
         Optional attribute set as a dictionary, each key either the name as a string or both a namespace uri and the
           name as a 2-tuple
         Optional further sequences and strings describing nested elements and text nodes, respectively"""
    dom = xml.dom.minidom.getDOMImplementation()
    dt = dom.createDocumentType(*doctype) if doctype else None
    doc = dom.createDocument(namespace_uri, None, dt)
    if root_spec:
        doc.appendChild(node(doc, root_spec))
    return doc 
    

def node(doc, spec):
    """Returns a Node object for the given DOM document.
       spec is either a Node object, a string to become a TextNode, or a sequence describing an element, consisting of:
         Optional namespace uri as a string
         Name as a string
         Optional attribute set as a dictionary, each key either the name as a string or both a namespace uri and the
           name as a 2-tuple
         Optional further sequences and strings describing nested elements and text nodes, respectively"""
         
    if isinstance(spec, xml.dom.Node):
        return spec
        
    elif isinstance(spec, basestring):
        return doc.createTextNode(spec)
        
    else:
        namespace, name, attributes, child_specs = _expand_args(spec)
        
        if namespace is not None:
            n = doc.createElementNS(namespace, name)
        else:
            n = doc.createElement(name)
            
        for atname, atval in attributes.items():
            if isinstance(atname, basestring):
                atnamespace = None
            else:
                atnamespace, atname = atname
                
            if atnamespace is not None:
                at = doc.createAttributeNS(atnamespace, atname)
            else:
                at = doc.createAttribute(atname)
                
            at.appendChild(doc.createTextNode(atval))
            if atnamespace is not None:
                n.setAttributeNodeNS(at)
            else:
                n.setAttributeNode(at)
            
        for child_spec in child_specs:
            child_node = node(doc, child_spec)
            n.appendChild(child_node)
            
        return n
                
        
def _expand_args(args):
    namespace = None
    name = None
    attributes = {}
    children = []
    
    args = list(args)
    
    a = _pop_arg(args)
    if isinstance(_peek_arg(args), basestring):
        namespace = a
        name = _pop_arg(args)
    else:
        name = a
    
    if isinstance(_peek_arg(args), dict):
        attributes = _pop_arg(args)
        
    if _peek_arg(args) is not None:
        children = _pop_arg(args)
        
    return namespace, name, attributes, children
        
        
def _peek_arg(args):
    return args[0] if len(args) > 0 else None
        
        
def _pop_arg(args):
    return args.pop(0) if len(args) > 0 else None

