"""    
Copyright (c) 2010 Mark Frimston

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

------------------------

Name Generation Tools

"""

import pickle
import os
import mrf.markov as markov


class NameGenerator(object):
    """    
    Class for generating names using markov chains. Maintains a
    set of the names already generated to ensure the same one is
    not generated twice.
    """
    def __init__(self, mkv_order=1):
        self.mkv = markov.Markov(order=mkv_order)
        self.generated = set()
        
    def add_example_names(self, names, allow_originals=False):
        for name in names:            
            self.mkv.add_seq(list(name))
            if not allow_originals:
                self.generated.add(name)
    
    def make_name(self, filter=None):
        while True:
            name = "".join(self.mkv.random_chain())
            if not name in self.generated:
                if filter==None or filter(name):
                    self.generated.add(name)
                    return name        
    
    def save(self, filename):
        with open(filename,"wb") as file:
            pickle.dump((self.mkv.order,self.mkv.graph),file)
        
    @staticmethod
    def load(filename):
        ng = NameGenerator()
        order,graph = None,None        
        with open(filename,"rb") as file:
            order, graph = pickle.load(file)
        ng.mkv.order = order
        ng.mkv.graph = graph
        return ng
        
    @staticmethod
    def from_list_file(filename, allow_originals=False, mkv_order=1):
        ng = NameGenerator(mkv_order)
        with open(filename,"rb") as file:
            ng.add_example_names(file, allow_originals)
        return ng
                

if __name__ == "__main__":
    import unittest
    
    class TestNameGenerator(unittest.TestCase):
    
        def test_make_name(self):            
            ng = NameGenerator()
            ng.add_example_names(["dave","fred","john","susan","kimberly","sarah"])
            name = ng.make_name()
            self.assertTrue(isinstance(name,str))
            self.assertTrue(len(name)>0)
            
        def test_save_load(self):
            filename = "namegentest.tmp"
            if os.path.exists(filename):
                os.remove(filename)
            try:
                ng = NameGenerator()
                ng.add_example_names(["dave","fred","john"])
                order, graph = ng.mkv.order, ng.mkv.graph
                ng.save(filename)    
                
                ng2 = NameGenerator.load(filename)
                self.assertEquals(ng2.mkv.order, order)
                self.assertEquals(ng2.mkv.graph, graph)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                    
        def test_list_file(self):
            filename = "namegentest2.tmp"
            if os.path.exists(filename):
                os.remove(filename)
            try:
                with open(filename,"w") as file:
                    for name in ["darth","luke","leia","han","chewy","r2","3po"]:
                        file.write(name+"\n")
                ng = NameGenerator.from_list_file(filename)
                name = ng.make_name()
                self.assertTrue(isinstance(name,str))
                self.assertTrue(len(name)>0)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
        
        def test_filter(self):
            ng = NameGenerator()
            ng.add_example_names(["pat","pot","bo","ba","aa","ao","tab","tob"])
            for i in range(5):
                name = ng.make_name(lambda x: len(x)==3)
                self.assertTrue(len(name)==3)

        def test_allow_originals(self):
            ng = NameGenerator()
            names = ["abc","def","ghi"]
            ng.add_example_names(names, True)
            for i in range(3):
                self.assertTrue(ng.make_name() in names)
            
            ng = NameGenerator()
            names = ["abc","cde","efg"]
            ng.add_example_names(names, False)
            for i in range(3):
                self.assertTrue(not ng.make_name() in names)
            
    unittest.main()
