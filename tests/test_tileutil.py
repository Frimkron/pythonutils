from mrf.tileutil import *
import unittest
    
    
class RayCastTest(unittest.TestCase):
    
    def setUp(self):
        self.blocks = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
          ]
        self.root_half = math.sqrt(0.5)
    
    def ray_collide(self, pos, grid_pos):

        if grid_pos[0] < 0 or grid_pos[0] >= 11 or grid_pos[1] < 0 or grid_pos[1] >= 11:
            return True
    
        return self.blocks[grid_pos[1]][grid_pos[0]] == 1 
        
    def testStandardCollision(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (7.5 * 32, 4.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((6 * 32, 5.25 * 32), (6, 5), (-1, 0))     
        self.assertEqual(coll, expected)
        
    def testNonSquareTileSize(self):
        w = 43
        h = 17
        
        start_pos = (5.5 * w, 5.5 * h)
        end_pos = (7.5 * w, 4.5 * h)
        coll = tile_ray_cast(start_pos, end_pos, (w, h), self.ray_collide)
        expected = ((6 * w, 5.25 * h), (6, 5), (-1, 0))     
        self.assertEqual(coll, expected)
        
        start_pos = (7.5 * w, 4.5 * h)
        end_pos = (5.5 * w, 5.5 * h)
        coll = tile_ray_cast(start_pos, end_pos, (w, h), self.ray_collide)
        expected = ((6.5 * w, 5 * h), (6, 5), (0, -1))
        self.assertEqual(coll, expected)
        
    def testIntCoordinates(self):
        
        start_pos = (7*64+32, 4*32+16)
        end_pos = (5*64+32, 5*32+16)
        coll = tile_ray_cast(start_pos, end_pos, (64,32), self.ray_collide)
        expected = ((6*64+32, 5*32), (6, 5), (0, -1))
        self.assertEqual(coll, expected)
        
    def testSameTile(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (5.6 * 32, 5.6 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((5.6 * 32, 5.6 * 32), None, None)
        self.assertEqual(coll, expected)
        
    def testNonCollision(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (4.5 * 32, 7.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((4.5 * 32, 7.5 * 32), None, None)
        self.assertEqual(coll, expected)
        
    def testHorizontal(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (6.5 * 32, 5.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((6 * 32, 5.5 * 32), (6, 5), (-1, 0))
        self.assertEqual(coll, expected)
        
        start_pos = (4.5 * 32, 5.5 * 32)
        end_pos = (6.5 * 32, 5.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((6 * 32, 5.5 * 32), (6, 5), (-1, 0))
        self.assertEqual(coll, expected)
        
    def testVertical(self):
        
        start_pos = (4.5 * 32, 4.5 * 32)
        end_pos = (4.5 * 32, 3.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((4.5 * 32, 4 * 32), (4, 3), (0, 1))
        self.assertEqual(coll, expected)
        
        start_pos = (4.5 * 32, 5.5 * 32)
        end_pos = (4.5 * 32, 3.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((4.5 * 32, 4 * 32), (4, 3), (0, 1))
        self.assertEqual(coll, expected)
        
    def testConcaveCorner(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (3.5 * 32, 3.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((4 * 32, 4 * 32), (3, 4), (self.root_half, self.root_half))
        self.assertEqual(coll, expected)
        
        start_pos = (5.5 * 32, 6.5 * 32)
        end_pos = (6.5 * 32, 7.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((6 * 32, 7 * 32), (6, 6), (-self.root_half, - self.root_half))
        self.assertEqual(coll, expected)
        
    def testConvexCorner(self):
        
        start_pos = (4.5 * 32, 5.5 * 32)
        end_pos = (3.5 * 32, 4.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((4 * 32, 5 * 32), (3, 4), (self.root_half, self.root_half))
        self.assertEqual(coll, expected)
        
    def testVerticalSurfaceCorner(self):
        
        start_pos = (5.5 * 32, 5.5 * 32)
        end_pos = (6.5 * 32, 6.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((6 * 32, 6 * 32), (6, 5), (-1, 0))
        self.assertEqual(coll, expected)
        
    def testHorizontalSurfaceCorner(self):
        
        start_pos = (5.5 * 32, 9.5 * 32)
        end_pos = (4.5 * 32, 10.5 * 32)
        coll = tile_ray_cast(start_pos, end_pos, (32, 32), self.ray_collide)
        expected = ((5 * 32, 10 * 32), (5, 10), (0, - 1)) 
        self.assertEqual(coll, expected)

    def testUnbounded(self):
    
        result = tile_ray_cast((0.5,0.5),(2.5,1.5),(1,1), lambda p,t: False)
        self.assertEqual(((2.5,1.5),None,None),result)
        
        result = tile_ray_cast((0.5,0.5),(-1.5,2.5),(1,1), lambda p,t: False)
        self.assertEqual(((-1.5,2.5),None,None),result)
        
        result = tile_ray_cast((0.5,0.5),(-2.5,-1.5),(1,1), lambda p,t: False)
        self.assertEqual(((-2.5,-1.5),None,None),result)
        
        result = tile_ray_cast((0.5,0.5),(1.5,-2.5),(1,1), lambda p,t: False)
        self.assertEqual(((1.5,-2.5),None,None),result)
        
        result = tile_ray_cast((1.0,1.0),(1.5,0.5),(1,1), lambda p,t: False)
        self.assertEqual(((1.5,0.5),None,None),result)
        
        result = tile_ray_cast((0.5,0.5),(-1.5,0.5),(1,1), lambda p,t: False)
        self.assertEqual(((-1.5,0.5),None,None),result)
        
        result = tile_ray_cast((0.5,0.5),(0.5,1.5),(1,1), lambda p,t: False)
        self.assertEqual(((0.5,1.5),None,None),result)
        
    def add_check(self, checks, tile):
        checks.add(tile)
        return False
        
    def testTilesChecked(self):
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(1.5,0.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((1.5,0.5),None,None), result)
        self.assertEqual(set([(1,0)]), checks)
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(-0.5,0.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((-0.5,0.5),None,None), result)
        self.assertEqual(set([(-1,0)]), checks)
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(1.5,1.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((1.5,1.5),None,None), result)
        self.assertEqual(set([(1,0),(0,1),(1,1)]), checks)
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(-0.5,-0.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((-0.5,-0.5),None,None), result)
        self.assertEqual(set([(-1,0),(0,-1),(-1,-1)]), checks)
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(2.5,1.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((2.5,1.5),None,None), result)
        self.assertEqual(set([(1,0),(1,1),(2,1)]), checks)
        
        checks = set()
        result = tile_ray_cast((0.5,0.5),(-1.5,-0.5),(1,1), lambda p,t: self.add_check(checks,t))
        self.assertEqual(((-1.5,-0.5),None,None), result)
        self.assertEqual(set([(-1,0),(-1,-1),(-2,-1)]), checks)
                    
        
class TestPathfind(unittest.TestCase):
    
    def setUp(self):
        
        self.map = [
                        [0, 8, 8, 8, 8, 0, 0, 0, 0, 0],
                        [0, 8, 0, 0, 8, 0, 8, 8, 8, 0],
                        [0, 8, 0, 0, 0, 0, 1, 1, 1, 0],
                        [0, 8, 0, 0, 8, 0, 8, 8, 8, 8],
                        [0, 8, 8, 8, 8, 0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 8, 0, 0, 8, 0, 0],
                        [8, 8, 8, 1, 8, 0, 0, 0, 8, 0],
                        [0, 0, 0, 1, 8, 0, 0, 0, 0, 8],
                        [0, 0, 8, 1, 8, 0, 8, 8, 8, 8],
                        [0, 0, 8, 1, 0, 0, 8, 0, 0, 0]
                    ]            
        self.search = TilePathfinder(self.costFunc)
        
    def costFunc(self, x, y):
        if x < 0 or x >= 10 or y < 0 or y >= 10:
            return None
        else:
            if self.map[y][x] == 0:
                return 1
            elif self.map[y][x] == 1:
                return 3
            else:
                return None
    
    def testSimple(self):
        path = self.search.search((9, 0), (5, 0))
        self.assertEqual([(9, 0), (8, 0), (7, 0), (6, 0), (5, 0)], path)
      
    def testCost(self):
        path = self.search.search((9, 1), (5, 1))
        self.assertEqual([(9, 1), (9, 0), (8, 0), (7, 0), (6, 0), (5, 0), (5, 1)], path)
        
    def testLong(self):
        path = self.search.search((9, 2), (0, 0))
        self.assertEqual([(9, 2), (9, 1), (9, 0), (8, 0), (7, 0), (6, 0), (5, 0), (5, 1),
                           (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9),
                           (4, 9), (3, 9), (3, 8), (3, 7), (3, 6), (3, 5), (2, 5), (1, 5),
                           (0, 5), (0, 4), (0, 3), (0, 2), (0, 1), (0, 0)], path)
       
    def testBlocked(self):
        path = self.search.search((9, 9), (0, 0))
        self.assertEqual(None, path) 
        
    def testDiagWall(self):
        path = self.search.search((9, 6), (8, 7))
        self.assertEqual([(9, 6), (9, 5), (8, 4), (7, 4), (6, 4), (6, 5), (6, 6), (7, 7), (8, 7)], path)

    def testIterations(self):
        path = self.search.search((9,2),(0,0),2)
        self.assertEqual(False, path)
        while path==False:
            path = self.search.resume(2)
        self.assertEqual([(9, 2), (9, 1), (9, 0), (8, 0), (7, 0), (6, 0), (5, 0), (5, 1),
                           (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7), (5, 8), (5, 9),
                           (4, 9), (3, 9), (3, 8), (3, 7), (3, 6), (3, 5), (2, 5), (1, 5),
                           (0, 5), (0, 4), (0, 3), (0, 2), (0, 1), (0, 0)], path)
    
    def testIsCompleted(self):
        path = self.search.search((9,2),(0,0),2)
        self.assertEqual(False, path)
        self.assertEqual(True, self.search.search_in_progress())
        while path==False:
            path = self.search.resume(2)
        self.assertEqual(False, self.search.search_in_progress())
                    
        path = self.search.search((9,2),(9,1),2)
        self.assertEqual(True, path!=False)
        self.assertEqual(False, self.search.search_in_progress())


class TestTileRender(unittest.TestCase):
    
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.clear_lists()
    
    def clear_lists(self):
        self.requested_lookups = []    
        self.requested_draws = []
    
    def lookup_request(self, pos):
        self.requested_lookups.append(pos)
        if 0 <= pos[0] < 2 and 0 <= pos[1] < 2:
            return 1
        else:
            return None
    
    def draw_request(self, type, rect):
        self.requested_draws.append((type,rect))
    
    def testLookups(self):            
        """    
          +--------------------+
        / | \  /   \  /   \  / | \
          |                    | 
        \ | /  \   /  \   /  \ | /
          |          +         |
        / | \  /   \  /   \  / | \
          |                    |
        \ | /  \   /  \   /  \ | /
          +--------------------+
        """
        # at origin
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (0,0), self.lookup_request, self.draw_request)            
        self.assertEqual([    (-2,-1),(-1,-1),( 0,-1),( 1,-1),
                            (-2, 0),(-1, 0),( 0, 0),( 1, 0),
                            (-2, 1),(-1, 1),( 0, 1),( 1, 1) ], self.requested_lookups)
        
        # scroll south east
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (15,20), self.lookup_request, self.draw_request)
        self.assertEqual([    ( 0, 1),( 1, 1),( 2, 1),( 3, 1),
                            ( 0, 2),( 1, 2),( 2, 2),( 3, 2),
                            ( 0, 3),( 1, 3),( 2, 3),( 3, 3) ], self.requested_lookups)
        
        # scroll north west
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (-20,-15), self.lookup_request, self.draw_request)
        self.assertEqual([    (-4,-3),(-3,-3),(-2,-3),(-1,-3),
                            (-4,-2),(-3,-2),(-2,-2),(-1,-2),
                            (-4,-1),(-3,-1),(-2,-1),(-1,-1)    ], self.requested_lookups)
    
    def testDraws(self):
        
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (0,0), self.lookup_request, self.draw_request)
        self.assertEqual([    (1,(30,30,10,10)), (1,(40,30,10,10)),
                            (1,(30,40,10,10)), (1,(40,40,10,10)) ], self.requested_draws)
        
        # scroll south east
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (15,20), self.lookup_request, self.draw_request)
        self.assertEqual([    (1,(15,20,10,10)), (1,(25,20,10,10)) ], self.requested_draws)
        
        # scroll north west
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (-20,-15), self.lookup_request, self.draw_request)
        self.assertEqual([], self.requested_draws)
        
    def testZoom(self):
        
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (0,0), self.lookup_request, self.draw_request, 0.8)
        self.assertEqual([    (-2,-2),(-1,-2),( 0,-2),( 1,-2),(2,-2),
                            (-2,-1),(-1,-1),( 0,-1),( 1,-1),(2,-1),
                            (-2, 0),(-1, 0),( 0, 0),( 1, 0),(2, 0),
                            (-2, 1),(-1, 1),( 0, 1),( 1, 1),(2, 1) ], self.requested_lookups)
        self.assertEqual([    (1,(30,30,8,8)), (1,(38,30,8,8)), 
                            (1,(30,38,8,8)), (1,(38,38,8,8)) ], self.requested_draws)
        
        # scroll south east
        self.clear_lists()
        render_tilemap((15,20,30,20), (10,10), (15,20), self.lookup_request, self.draw_request, 0.8)
        self.assertEqual([    (-1, 0),( 0, 0),( 1, 0),( 2, 0),( 3, 0),
                            (-1, 1),( 0, 1),( 1, 1),( 2, 1),( 3, 1),
                            (-1, 2),( 0, 2),( 1, 2),( 2, 2),( 3, 2),
                            (-1, 3),( 0, 3),( 1, 3),( 2, 3),( 3, 3) ], self.requested_lookups)
        self.assertEqual([    (1,(18,14,8,8)), (1,(26,14,8,8)),
                            (1,(18,22,8,8)), (1,(26,22,8,8)) ], self.requested_draws)


class TestMapFromAscii(unittest.TestCase):
    
    def test(self):
        
        mapping = {" ":0,"#":1,"~":2,"O":3}
        map = tile_map_from_ascii("""
# # # # 
#   O # 
# ~ ~ # 
# # # # """, mapping)
        self.assertEqual([    [1,1,1,1],
                            [1,0,3,1],
                            [1,2,2,1],
                            [1,1,1,1] ],map)
        
class TestDir4(unittest.TestCase):
    """
    """
    def test_rot(self):
        
        d = Dir4.NORTH
        self.assertEqual(Dir4.EAST, d.turn_cw())
        self.assertEqual(Dir4.WEST, d.turn_acw())
        self.assertEqual(Dir4.SOUTH, d.turn_cw(2))
        self.assertEqual(Dir4.SOUTH, d.turn_180())
        
    def test_str(self):
        self.assertEqual("EAST", str(Dir4.EAST))
        
    def test_repr(self):
        self.assertEqual("Dir4.EAST", repr(Dir4.EAST))
        
    def test_move(self):
        self.assertEqual((2,0), Dir4.EAST.move(rel=(0,2)))
        self.assertEqual((0,1), Dir4.WEST.move(pos=(1,1)))
        self.assertEqual((3,7), Dir4.SOUTH.move((3,2),(0,5)))
        self.assertEqual((3,3), Dir4.EAST.move(pos=(1,2),rel=(1,2)))
    
    def test_get_move_rel(self):
        self.assertEqual((3,2), Dir4.EAST.get_move_rel((0,2),(2,5)))
        self.assertEqual((4,-1), Dir4.WEST.get_move_rel((3,3),(4,-1)))
        self.assertEqual((-1,2), Dir4.SOUTH.get_move_rel((1,2),(2,4)))
        self.assertEqual((1,2), Dir4.NORTH.get_move_rel((3,2),(4,0)))

    
class TestLosMap(unittest.TestCase):
        
    def setUp(self):
        self.lm = LosMap.generate(2,2)
        self.lm2 = LosMap.generate(6,4)
        self.map = [
            [0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0],
            [0,0,0,1,0,0,0],
            [0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0]
        ]            
        
    def test_generate(self):
        """    
           0  1  2
        0 [X][ ][ ]
        1 [ ][ ][ ]
        2 [ ][ ][ ]
        """
        expected = {
            (0,0) : [],
            (1,0) : [(1,0)],
            (2,0) : [(1,0),(2,0)],
            (0,1) : [(0,1)],
            (1,1) : [(1,0),(0,1),(1,1)],
            (2,1) : [(1,0),(1,1),(2,1)],
            (0,2) : [(0,1),(0,2)],
            (1,2) : [(0,1),(1,1),(1,2)],
            (2,2) : [(1,0),(0,1),(1,1),(2,1),(1,2),(2,2)]
        }            
        self.assertEqual(expected, self.lm.data)
    
    def test_get_deps(self):
        
        self.assertEqual([(1,0),(1,1),(2,1)], self.lm.get_deps((2,1)))
        self.assertEqual([(0,1),(-1,1),(-1,2)], self.lm.get_deps((-1,2)))
        self.assertEqual([(-1,0),(-1,-1),(-2,-1)], self.lm.get_deps((-2,-1)))
        self.assertEqual([(0,-1),(1,-1),(1,-2)], self.lm.get_deps((1,-2)))

    def los_callback(self, tile):
        if 0 <= tile[0] < 7 and 0 <= tile[1] < 5:
            return self.map[tile[1]][tile[0]] == 0
        else:
            return False

    def test_tile_vis(self):            
        # across open space
        self.assertEqual(True,self.lm2.is_tile_visible((1,0), (2,4), self.los_callback))
        # through wall
        self.assertEqual(False,self.lm2.is_tile_visible((1,3), (5,1), self.los_callback))
        # across corner
        self.assertEqual(False,self.lm2.is_tile_visible((4,2), (3,3), self.los_callback))
        # into wall
        self.assertEqual(False,self.lm2.is_tile_visible((3,2), (5,2), self.los_callback))
        # out of wall
        self.assertEqual(True,self.lm2.is_tile_visible((5,2), (3,2), self.los_callback))
        
    def test_save_load(self):
        
        filename = "losmaptest.tmp"
        if os.path.exists(filename):
            os.remove(filename)
        try:
            self.lm.save(filename)
            lm3 = LosMap.load(filename)
            self.assertEqual(lm3.data, self.lm.data)
        finally:
            # cleanup
            if os.path.exists(filename):
                os.remove(filename)

def los_timings():

    import time

    def task(size, tests, callback):
        frompos = (size//2,size//2)
        results = []
        for x in range(tests):
            start = time.time()
            cache = {}
            for j in range(size):
                for i in range(size):
                    callback(frompos,(i,j),cache)
            finish = time.time()
            results.append(finish-start)
        return sum(results)/float(tests)
    
    for size in (10,20,30,40,50):
        print("size %d" % size)
        
        lm = LosMap.generate(int(size*0.6),int(size*0.6))
    
        res_losmap = task(size, 10, lambda frompos, topos, cache: lm.is_tile_visible(topos, frompos,
                lambda pos: True, cache))
        res_raycast = task(size, 10, lambda frompos, topos, cache: tile_ray_cast(
                (frompos[0]+0.5,frompos[1]+0.5), (topos[0]+0.5,topos[1]+0.5), (1,1), 
                lambda pos, tile: False)[1]==None)
        
        print("losmap: %f, raycast: %f" % (res_losmap,res_raycast))
        print()




