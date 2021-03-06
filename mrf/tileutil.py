"""    
Copyright (c) 2009 Mark Frimston

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

Tile Utilities Module

Contains utilities for dealing with tile maps:

    tile_ray_cast        - function for calulating where and how a ray intersects
                            tiles on a tile map
    TilePathfinder        - class for performing A* searches on a tile map
    render_tilemap        - function for rendering a tile map
"""

from mrf.search import *
import math
import os
import os.path

def _trc_check_axis(axis, start_pos, diff, dir, grid_size, end_pos, 
        end_grid_pos, collision_callback):
    """    
    Helper function used by tile_ray_cast. Finds collision with cross-cutting boundaries
    along the given axis. Returns tuple containing the squared distance to the collision 
    point and the collision point itself, if a collision is found, or None otherwise.
    """
    oth_ax = 1 if axis == 0 else 0
    
    coll_point = None
    
    # if direction not perpendicular, find collision along this axis
    if diff[axis] != 0:
        
        pos = (start_pos[0], start_pos[1])
        
        # calculate gradient
        grad = float(diff[oth_ax]) / diff[axis]
        
        # work out how far to move to the next boundary on this axis. This will be
        # one of the boundaries enclosing the starting tile.
        offset = pos[axis] % grid_size[axis]
        ax_inc = (grid_size[axis] if diff[axis] >= 0 else 0) - offset
        oth_ax_inc = grad * ax_inc
        inc = { axis : ax_inc , oth_ax : oth_ax_inc }
    
        # move to first boundary and test for collision
        collision = _trc_move_collide(axis, pos, inc, dir, grid_size,
                                      end_pos, end_grid_pos, collision_callback)
        pos = collision[0]
        
        # if ray collided
        if collision[1] != None:
            coll_point = collision[1]
            
        else:
            
            # work out how far to move to the next boundary on this axis. We are
            # now moving a tile's width/height at a time across the tilemap. 
            inc = {axis:grid_size[axis] * dir[axis], oth_ax:grid_size[axis] * dir[axis] * grad}
            
            while collision[1] == None:
                
                collision = _trc_move_collide(axis, pos, inc, dir, grid_size,
                                              end_pos, end_grid_pos, collision_callback)
                pos = collision[0]
                
                if collision[1] != None:
                    coll_point = collision[1]
    else:
        
        # if we dont actually move on the axis, just return a non-collision
        # collision tuple with the end position in it.
        coll_point = (end_pos,None,None)
    
    # Determine distance to this collision point
    sq_dist = math.pow(coll_point[0][0] - start_pos[0], 2) + math.pow(coll_point[0][1] - start_pos[1], 2)
    
    return (sq_dist, coll_point)
    

def _trc_move_collide(axis, pos, inc, dir, grid_size, end_pos, end_grid_pos, collision_callback):
    """    
    Helper function used by tile_ray_cast. Increments position by the given amount
    and checks for boundary collisions using the collision callback. Returns a tuple
    containing the updated position and the collision tuple, if one is found.
    The collision tuple is that which is returned by tile_ray_cast: the collision
    position, grid square and wall normal.
    """
    oth_ax = 0 if axis == 1 else 1
    
    # move
    pos = (pos[0] + inc[0], pos[1] + inc[1])
        
    # Check if we have overshot the end position on this axis. If we have, 
    # return a no-collision collision tuple, indicating the ray ended at the end point.                    
    if pos[axis]*dir[axis] > end_pos[axis]*dir[axis]:
    
        return (pos, (end_pos, None, None))
        
    # determine grid ref(s) to check
    grid_poses = []
    if pos[oth_ax] % grid_size[oth_ax] == 0:
        # if we are on the boundary between 2 tiles, need to check both of these tiles
        # - either could stop the ray and incur a collision.
        # TODO if an axis's dir is 0, this does not check both tiles!
        grid_poses.append({ axis: int(math.floor((pos[axis] + dir[axis] * (grid_size[axis] / 2.0)) / grid_size[axis])),
                           oth_ax : int(math.floor((pos[oth_ax] - dir[oth_ax] * (grid_size[oth_ax] / 2.0)) 
                                        / grid_size[oth_ax])) })
        grid_poses.append({ axis: int(math.floor((pos[axis] + dir[axis] * (grid_size[axis] / 2.0)) / grid_size[axis])),
                           oth_ax : int(math.floor((pos[oth_ax] + dir[oth_ax] * (grid_size[oth_ax] / 2.0)) 
                                        / grid_size[oth_ax])) })
    else:
        grid_poses.append({ axis : int(math.floor((pos[axis] + dir[axis] * (grid_size[axis] / 2.0)) / grid_size[axis])),
                oth_ax : int(math.floor(pos[oth_ax] / grid_size[oth_ax])) })
        
    # call function to determine if the block(s) we're at should stop the ray
    blocked = False
    grid_pos = None
    for gp in grid_poses:
        if collision_callback(pos, (gp[0], gp[1])):
            blocked = True
            grid_pos = gp
            
    if blocked:
            
        norm = { axis : - dir[axis], oth_ax : 0 }
                
        # return the position and collision tuple
        return (pos , (pos, (grid_pos[0], grid_pos[1]), (norm[0], norm[1])))
    
    else:    
        
        # have we ended inside the end tile?
        if grid_pos == end_grid_pos:
            
            # return no-collision collision tuple, indicating the ray reached its
            # end point
            return (pos, (end_pos, None, None))
        
        else:
        
            # return the position and no collision
            return (pos, None)
    

def tile_ray_cast(start_pos, end_pos, grid_size, collision_callback):
    """    
    Function to determine where a ray, projected across a grid of blocking and 
    non-blocking squares, should stop.
    
    Parameters:
        start_pos               Tuple containing the x and y coordinates of the ray's origin
        end_pos                 Tuple containing the x and y coordinates of the ray's end point, 
                                thus specifying the ray's direction and maximum length.                        
        grid_size               Tuple containing the width and height of the grid across which
                                to project the ray.
        collision_callback  Function which will be called to determine whether a square
                                on the grid should stop the ray or not. See section below. 
                                Note that while the squares checked will correspond to those
                                along the path of the ray, they will not be checked in order
                                and squares may be checked more than once.
                                                            
    Returns:
        A tuple containing:
            The coordinates of the stopping point as a 2-item tuple
            The grid position of the square the ray collided with, as a 2-item tuple
                (or None if the ray never collided)
            The normal of the square edge the ray collided with, as a 2-item tuple
                (or None if the ray never collided)
            
    collision_callback:
        Parameters:
            The coordinates of the potential collision point as a 2-item tuple
            The grid position of the square to check, as a 2-item tuple
        Returns:
            True if this square would stop the ray, False otherwise
    """
    
    # Work out grid ref of end pos
    end_grid_pos = (int(math.floor(end_pos[0] / grid_size[0])),
                    int(math.floor(end_pos[1] / grid_size[1])))
    
    # Check if we're in the end grid pos
    grid_pos = (int(math.floor(start_pos[0] / grid_size[0])),
                int(math.floor(start_pos[1] / grid_size[1])))
    
    if grid_pos == end_grid_pos:
        
        # if we start and end on the same tile, report no collision, even if the
        # tile is blocking. The ray must cross a boundary to collide with 
        # something.
        result = (end_pos, None, None)
        
    else:
    
        # distance on each axis between start and end positions
        diff = (end_pos[0] - start_pos[0], end_pos[1] - start_pos[1])
    
        # direction along each axis: -1, 0 or 1
        dir = (diff[0] / math.fabs(diff[0]) if diff[0] != 0 else 0,
               diff[1] / math.fabs(diff[1]) if diff[1] != 0 else 0)
    
        # move along the x axis, finding the verical boundary collision, if any
        x_cand = _trc_check_axis(0, start_pos, diff, dir, grid_size,
                                 end_pos, end_grid_pos, collision_callback)
        # move along the y axis, finding the horizontal boundary collision, if any
        y_cand = _trc_check_axis(1, start_pos, diff, dir, grid_size,
                                 end_pos, end_grid_pos, collision_callback)
        
        if x_cand[1][1]==None and y_cand[1][1]==None:
            
            # No collisions
            result = (end_pos, None, None)
        
        elif x_cand[1][1]!=None and y_cand[1][1]==None:
            
            # X-axis collision only (with vertical boundary)            
            result = x_cand[1]
        
        elif y_cand[1][1]!=None and x_cand[1][1]==None:
            
            # Y-axis collision only (with horizontal boundary)
            result = y_cand[1]
            
        else:
            
            # Compare distances to x and y collisions and use the closest one as the
            # collision point we return.
            if x_cand[0] < y_cand[0]:
                result = x_cand[1]
            elif y_cand[0] < x_cand[0]:
                result = y_cand[1]
            else:
                
                # Special case - we've hit exactly on a corner. Test the surrounding
                # squares to determine the surface direction. 
                # The collision testing counts a boundary as a collision if either 
                # of the tiles are blocking, so we only need to test for combinations of
                # the 2 adjacent blocks - the corner block is irrelevant unless both of
                # these are non-blocking.                
                
                grid_poses = {}
                grid_blocks = {}
                for i in [ - 1, 1]:
                    for j in [ - 1, 1]:
                        grid_poses[(i, j)] = (
                            int(math.floor((x_cand[1][0][0] + grid_size[0] / 2.0 * i) / grid_size[0])),
                            int(math.floor((x_cand[1][0][1] + grid_size[1] / 2.0 * j) / grid_size[1])))
                        grid_blocks[(i, j)] = collision_callback(x_cand[1][0], grid_poses[(i, j)])
                
                root_half = math.sqrt(0.5)
                
                # where dir is 0, i.e. travelling exactly horizontally or vertically, adjust
                # dir to be positive for the following calculations
                if dir[0]==0: dir[0] = 1
                if dir[1]==0: dir[1] = 1
                
                # ??|XX
                # --+--
                #   |\
                # Horizontal surface / side glance                
                if grid_blocks[(dir[0] *- 1, dir[1])] and not grid_blocks[(dir[0], dir[1] *- 1)]:
                    
                    result = (x_cand[1][0], grid_poses[(dir[0] *- 1, dir[1])], (0, dir[1] *- 1))
                
                # ??|
                # --+--    
                # XX|\
                # Vertical surface / side glance
                elif not grid_blocks[(dir[0] *- 1, dir[1])] and grid_blocks[(dir[0], dir[1] *- 1)]:
                    
                    result = (x_cand[1][0], grid_poses[(dir[0], dir[1] *- 1)], (dir[0] *- 1, 0))
                
                # XX|
                # --+--    
                #   |\
                # Convex corner
                elif not grid_blocks[(dir[0] *- 1, dir[1])] and not grid_blocks[(dir[0], dir[1] *- 1)]:
                    
                    result = (x_cand[1][0], grid_poses[(dir[0], dir[1])], (dir[0] * root_half *- 1, dir[1] 
                                * root_half *- 1))
                
                # ??|XX
                # --+--    
                # XX|\
                # Concave corner / squeeze
                else:
                    
                    # Which block do we hit here? Just assume a vertical surface collision but
                    # bounce straight back 
                    result = (x_cand[1][0], grid_poses[(dir[0], dir[1] *- 1)], (dir[0] * root_half *- 1, dir[1] 
                                * root_half *- 1))
                
    return result




class TilePathfinder(AStar):
    """    
    An A* search implementation for navigating a map of square tiles. Uses a 
    callback to determine the cost of moving to different tiles.
    """
    
    DIAG_VAL = math.sqrt(2)
    
    def __init__(self, tilecost_func):
        """    
        tilecost_func should be a function returning the cost of moving to a 
        given tile position. It should take 2 parameters: the x and y positions 
        of a tile respectively, and return the cost value as a float value. If
        a tile should never be moved into, None should be returned
        """
        AStar.__init__(self)
        self.tilecost_func = tilecost_func
        
    def search(self, start, finish, max_iterations=0):
        """    
        Performs the search, taking two 2-item tuples of x and y tile coordinates 
        for the start position and the end position respectively, and returning a 
        list of 2-item tuples representing the pairs of x-y tile coordinates 
        making up the path from the start position to the end position.
        max_iterations may be specified to limit the number of nodes expanded
        for this call. If algorithm has not completed after this many, False is
        returned and search may be resumed by calling the method again. The 
        discard method may be used to abandon a search in progress prior to 
        calling search.
        """
        return AStar.search(self, start, finish, max_iterations)
        
    def cost(self, state):
        diag = False
        # Check the 2 sides of the diagonal move for impossible moves
        if state.previous != None:
            xmove = state.value[0] - state.previous.value[0]
            ymove = state.value[1] - state.previous.value[1]
            diag = xmove != 0 and ymove != 0
            if diag:
                xcheck = (state.previous.value[0] + xmove, state.previous.value[1])
                ycheck = (state.previous.value[0], state.previous.value[1] + ymove)
                if (self.tilecost_func(xcheck[0], xcheck[1]) == None 
                        or self.tilecost_func(ycheck[0], ycheck[1]) == None):
                    return None
        tile_cost = self.tilecost_func(state.value[0], state.value[1])
        if tile_cost != None:
            path_cost = ((state.previous.path_cost if state.previous != None else 0)
                         + tile_cost * (TilePathfinder.DIAG_VAL if diag else 1))
            cost = (path_cost
                        + math.sqrt(math.pow(self.finish[0] - state.value[0], 2) 
                                    + math.pow(self.finish[1] - state.value[1], 2))) 
            return path_cost, cost
        else:
            return None
    
    def expand(self, state):
        expanded = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                if not(i == 0 and j == 0):
                    new_state = AStar.State((state.value[0] + i, state.value[1] + j), state)
                    costs = self.cost(new_state)
                    if costs != None:
                        new_state.path_cost = costs[0]
                        new_state.cost = costs[1]
                        expanded.append(new_state)
        return expanded



def render_tilemap(rect, tile_size, cam_pos, type_callback, draw_callback, zoom=1.0):
    """    
    Function for rendering a 2d square-tiled scrolling tilemap in a rectangular 
    window.
    
    Parameters:
        rect         - a 4-item tuple containing the x, y, width and height of 
                        the screen area in which to draw
        tile_size     - a 2-item tuple containing the width and height of each 
                        tile
        cam_pos        - a 2-item tuple containing the x and y of the camera on the
                        tilemap.
        type_callback - a function to return the type of a given tile in the 
                        tilemap (see description below)
        draw_callback - a function to draw a tile of the given type in the given
                        rect (see description below)
        zoom        - the scaling to apply to the rendered tilemap, resulting in
                        a zoomed-in or zoomed-out effect. A zoom of 2.0 will
                        draw the tiles at double size, 0.5 will draw the tiles
                        at half size, etc. Defaults to 1.0: the standard size.
                                                
    Type Callback:
        
        This function should return the type of the tile at the given position
        in the tilemap. Typically  this will be implemented as some kind of
        array lookup. The type will then be passed into the draw callback. 
        The function should allow for tile positions which fall outside of the 
        tilemap. A value of None can be returned to prevent any tile from being 
        drawn.
        
        Parameters:
            pos - tuple containing the x and y position of the tile in the 
                    tilemap
        Returns:
            The tile type or None if no tile should be drawn
            
    Draw Callback:
        
        This function should draw the given tile type in the given rectangle. 
        The rectangle specifies the x and y coordinates on the screen and the 
        width and height to draw the tile with, thereby scaling the tile.
        
        Parameters:
            type     - the type of tile to draw. This is the type returned by the 
                        tile type callback above
            rect     - the x, y, width and height at which the tile should be 
                        drawn on the screen.
    """
    # find size of a zoomed tile
    stilew = int(tile_size[0] * zoom)
    stileh = int(tile_size[1] * zoom)
    
    # find world coords of top left of viewport
    wtlx = cam_pos[0] - rect[2] / 2 * (1.0 / zoom)
    wtly = cam_pos[1] - rect[3] / 2 * (1.0 / zoom)
    
    # find world coords of top left of the tile this pos sits on
    wtilestartx = math.floor(wtlx / tile_size[0]) * tile_size[0]
    wtilestarty = math.floor(wtly / tile_size[1]) * tile_size[1]
        
    # loop for enough tiles to fill viewport height
    for j in range(int(math.ceil(rect[3] / tile_size[1] / zoom)) + 1):
        
        # loop for enough tiles to fill viewport width
        for i in range(int(math.ceil(rect[2] / tile_size[0] / zoom)) + 1):
            
            # find world coordinates of tile to draw
            wtilex = wtilestartx + i * tile_size[0]
            wtiley = wtilestarty + j * tile_size[1]
            
            # get tile position of tile in tilemap
            ttilex = int(math.floor(wtilex / tile_size[0]))
            ttiley = int(math.floor(wtiley / tile_size[1]))
            
            # look up tile type to draw
            tile_type = type_callback((ttilex, ttiley))
            
            if tile_type != None:
            
                # find screen coordinates of world position of tile
                stilex = rect[0] + rect[2] // 2 + int((wtilex - cam_pos[0]) * zoom)
                stiley = rect[1] + rect[3] // 2 + int((wtiley - cam_pos[1]) * zoom)
                
                # render the tile
                draw_callback(tile_type, (stilex, stiley, stilew, stileh))


def tile_map_from_ascii(ascii, mapping):
    
    tiles = []
    for line in ascii.split("\n")[1:]:
        tile_row = []
        for char in [line[x*2] for x in range(len(line)//2)]:            
            tile_row.append(mapping[char])
        tiles.append(tile_row)
        
    return tiles


class Dir4(object):
    
    dirs = {}
    
    def __init__(self, val, name, fwd_offset, side_offset):
        self._val = val
        self._name = name
        self._fwd_offset = fwd_offset
        self._side_offset = side_offset
        Dir4.dirs[val] = self
        setattr(Dir4, name, self)
    
    def turn_cw(self, amount=1):
        return Dir4.dirs[(self._val + 4 + amount) % 4]
    
    def turn_acw(self, amount=1):
        return self.turn_cw(-amount)
    
    def turn_180(self):
        return self.turn_cw(2)
    
    def __repr__(self):
        return "Dir4.%s" % self._name
    
    def __str__(self):
        return self._name
    
    def move(self, pos=(0,0), rel=(0,1)):
        return (pos[0]+self._fwd_offset[0]*rel[1]+self._side_offset[0]*rel[0], 
                pos[1]+self._fwd_offset[1]*rel[1]+self._side_offset[1]*rel[0])
    
    def get_move_rel(self, pos_a, pos_b):
        """    
        Returns the direction-relative offset used to move from pos_a to pos_b
        """
        return( (pos_b[0]-pos_a[0])*self._side_offset[0]
                + (pos_b[1]-pos_a[1])*self._side_offset[1],
            (pos_b[0]-pos_a[0])*self._fwd_offset[0]
                + (pos_b[1]-pos_a[1])*self._fwd_offset[1] )
    
    def rel(self, dir):
        return self.turn_cw(dir._val)
        
    def get_val(self):
        return self._val
        
    @classmethod
    def from_val(cls, val):
        return cls.dirs[val]

Dir4(0, "NORTH", ( 0,-1), ( 1, 0))
Dir4(1, "EAST",  ( 1, 0), ( 0, 1))
Dir4(2, "SOUTH", ( 0, 1), (-1, 0))
Dir4(3, "WEST",  (-1, 0), ( 0,-1))


class LosMap(object):
    
    @staticmethod
    def generate(xdist, ydist):
        """    
        Generate a new line of sight map which extends horizontally xdist tiles and
        vertically ydist tiles from the player
        """
        data = {}
        for j in range(ydist+1):
            for i in range(xdist+1):
                deps = []
                # cast a ray from top left tile to this tile, recording the tiles passed
                # through using the collision-check callback
                tile_ray_cast((0.5,0.5), (i+0.5,j+0.5), (1,1),
                    lambda chpos,chtile: LosMap._los_callback(deps, chtile))
                # sort the dependencies into ray path order
                deps.sort(key=lambda d: (d[1], d[0]))
                # record the dependencies in the map
                data[(i,j)] = deps
        
        return LosMap(data)        

    @staticmethod
    def _los_callback(deps, tile):
        if not tile in deps:
            deps.append(tile)
        return False
    
    @staticmethod
    def load(filename):
        """    
        Create a line of sight map by loading the map from a file 
        """
        with open(filename,'r') as file:
            data = {}
            for line in file:
                bits = line[:-1].split(":")
                k = tuple(map(int,bits[0].split(",")))
                if len(bits[1]) > 0:
                    deps = [tuple(map(int,x.split(","))) for x in bits[1].split("|")]
                else:
                    deps = []
                data[k] = deps
        
        return LosMap(data)

    def __init__(self, data):
        self.data = data

    def save(self, filename):
        """    
        Save the line of sight map to file
        """
        with open(filename,'w') as file:
            for k in self.data:
                line = "%d,%d:" % k
                line += "|".join([("%d,%d" % x) for x in self.data[k]])
                file.write(line+"\n")

    def is_tile_visible(self, tile, from_tile, seethru_callback, checked=None):
        """    
        Tests whether the centre of tile is in line-of-sight from the centre of 
        from_tile. seethru_callback should be a function to determine if a tile
        in the tile map can be seen through or not. May optionally provide checked
        param - a dictionary in which to cache tile visibility results
        
        seethru_callback
            params:
                tile - a 2-item tuple indicating the tile in the tile 
                    map to check
            return:
                Should return True if a line of sight can pass through 
                this tile, or False if the tile blocks visibility
        """
        relpos = (tile[0]-from_tile[0], tile[1]-from_tile[1])
                
        # check if we have a cached result to use
        if checked!=None and checked.has_key(relpos):
            return checked[relpos]
        
        # use callback to test each dependency's opacity
        visible = True
        for dep in self.get_deps(relpos):
            check_pos = (from_tile[0]+dep[0], from_tile[1]+dep[1])
            dep_vis = seethru_callback(check_pos)
            if checked!=None:
                checked[dep] = dep_vis 
            if not dep_vis:
                visible = False
                break

        return visible

    def get_deps(self, relpos):
        deps = self.data[tuple(map(int,map(math.fabs,relpos)))]
        if relpos[0] < 0:
            deps = [(-d[0],d[1]) for d in deps]
        if relpos[1] < 0:
            deps = [(d[0],-d[1]) for d in deps]
        return deps        
        

