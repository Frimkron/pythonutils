from mrf.namegen import *
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
        
