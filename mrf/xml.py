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


def xhtml(*child_specs):
    return doc(('html', '-//W3C//DTD XHTML 1.0 Strict//EN', 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'), 
               None, ['html']+list(child_specs))


def doc(doctype=None, ns_map=None, root_spec=None):
    """Create and return a new DOM document with the given doctype, and nodes.
       doctype is a 3-tuple consisting of the name, publicid and systemid.
       ns_map is an optional dictionary of prefixes to namespace uris
       root_spec is either a Node object, or a sequence decribing the root element, consisting of:
         Name as a string, optionally prefixed with a key from ns_map followed by a colon, to specify namespace
         Optional attribute set as a dictionary, each key optionally prefixed with namespace key and colon
         Optional further sequences and strings describing nested elements and text nodes, respectively
       Note, the doctype cannot be set without also specifying root_spec"""
         
    dom = xml.dom.minidom.getDOMImplementation()
    if root_spec:
        namespace, name, attributes, child_specs = _expand_args(root_spec, ns_map)
        dt = dom.createDocumentType(*doctype) if doctype else None   
        doc = dom.createDocument(namespace, name, dt)
        _add_attrs_and_children(doc, doc.documentElement, ns_map, attributes, child_specs)
    else:
        doc = dom.createDocument(None, None, None)
    return doc 
    

def node(doc, ns_map, spec):
    """Returns a Node object for the given DOM document.
       ns_map is an optional dictionary of prefixes to namespace uris
       spec is either a Node object, a string to become a TextNode, or a sequence describing an element, consisting of:
         Name as a string, optionally prefixed with key from ns_map followed by a colon, to specify the namespace
         Optional attribute set as a dictionary, each key optionally prefixed with namespace key and colon
         Optional further sequences and strings describing nested elements and text nodes, respectively"""
         
    if isinstance(spec, xml.dom.Node):
        return spec
        
    elif isinstance(spec, basestring):
        return doc.createTextNode(spec)
        
    else:
        namespace, name, attributes, child_specs = _expand_args(spec, ns_map)
        
        if namespace is not None:
            n = doc.createElementNS(namespace, name)
        else:
            n = doc.createElement(name)
            
        _add_attrs_and_children(doc, n, ns_map, attributes, child_specs)
            
        return n


def _add_attrs_and_children(doc, n, ns_map, attributes, child_specs):

    for (atnamespace, atname), atval in attributes.items():
        if atnamespace is not None:
            at = doc.createAttributeNS(atnamespace, atname)
        else:
            at = doc.createAttribute(atname)

        at.value = atval
        if atnamespace is not None:
            n.setAttributeNodeNS(at)
        else:
            n.setAttributeNode(at)
        
    for child_spec in child_specs:
        child_node = node(doc, ns_map, child_spec)
        n.appendChild(child_node)
                
        
def _expand_args(args, ns_map):
    namespace = None
    name = None
    attributes = {}
    children = []
    
    args = list(args)
    
    a = _pop_arg(args)
    if ':' in a:
        key, name = a.split(':')
        namespace = ns_map[key]
    else:
        name = a
       
    if isinstance(_peek_arg(args), dict):
        for key, val in _pop_arg(args).items():
            if ':' in key:
                nkey, aname = key.split(':')
                ans = ns_map[nkey]
            else:
                aname = key
                ans = None
            attributes[(ans, aname)] = val
        
    while True:
        child = _pop_arg(args)
        if child is None: break
        children.append(child)
        
    return namespace, name, attributes, children
        
        
def _peek_arg(args):
    return args[0] if len(args) > 0 else None
        
        
def _pop_arg(args):
    return args.pop(0) if len(args) > 0 else None



