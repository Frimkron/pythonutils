from mrf.mathutil import *
import unittest


class AngleTests(unittest.TestCase):

    def test_zero_angles_equal(self):   
        self.assertEqual(Angle(0), Angle(0))
        
    def test_nonzero_angles_equal(self):
        self.assertEqual(Angle(10), Angle(10))
        
    def test_different_angles_not_equal(self):
        self.assertNotEqual(Angle(0), Angle(10))
        
    def test_additional_normalises_to_neg_pi_pos_pi_range(self):
        self.assertEqual(Angle(math.pi/2) + Angle(math.pi), Angle(-math.pi/2))

    def test_subtraction_normalises_to_neg_pi_pos_pi_rang(self):
        self.assertEqual(Angle(-math.pi/2) - Angle(math.pi), Angle(math.pi/2))
        
    def test_conversion_to_degrees(self):
        self.assertAlmostEqual(Angle(math.pi/2).to_deg(), 90, 4) 

    def test_angles_with_same_value_have_same_hash(self):
        self.assertTrue(Angle(10) in set([Angle(10)]))

    def test_angles_with_different_values_have_different_hashes(self):
        self.assertFalse(Angle(10) in set([Angle(11)]))
    
    def test_produces_working_rotation_matrix(self):
        self.assertAlmostEquals((Angle(math.pi/2).matrix() * (4,8))[0], (-8,4)[0], 4)
        self.assertAlmostEquals((Angle(math.pi/2).matrix() * (4,8))[1], (-8,4)[1], 4)


class RotationTests(unittest.TestCase):

    def test_rotations_with_same_values_are_equal(self):
        self.assertEqual(Rotation(0.5,1.5,2.5),Rotation(0.5,1.5,2.5))

    def test_rotations_with_different_values_are_not_equal(self):
        self.assertNotEqual(Rotation(0.5,1.5,2.5),Rotation(0.5,1.5,2.6))
                
    def test_rotation_doesnt_equal_other_type(self):
        self.assertNotEqual(Rotation(0.5,1.5,2.5),0.0)

    def test_normalises_constructor_values(self):
        self.assertEqual(Rotation(0.5,1.5,2.5),Rotation(2*math.pi+0.5, 2*math.pi+1.5, 2*math.pi+2.5))

    def test_addition_increases_roll_value(self):
        self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.1,0.0,0.0), Rotation(0.6,1.5,2.5))

    def test_addition_increases_pitch_value(self):
        self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.0,4*math.pi,0.0), Rotation(0.5,1.5,2.5))

    def test_addition_increases_yaw_value(self):
        self.assertEqual(Rotation(0.5,1.5,2.5) + Rotation(0.0,0.0,0.2), Rotation(0.5,1.5,2.7))

    def test_subtraction_decreases_roll_value(self):
        self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.1,0.0,0.0), Rotation(0.4,1.5,2.5))

    def test_subtraction_decreases_pitch_value(self):            
        self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.0,4*math.pi,0.0), Rotation(0.5,1.5,2.5))

    def test_subtraction_decreases_yaw_value(self):
        self.assertEqual(Rotation(0.5,1.5,2.5) - Rotation(0.0,0.0,0.2), Rotation(0.5,1.5,2.3))

    def test_rotations_with_same_values_have_same_hash(self):
        self.assertTrue(Rotation(1,2,3) in set([Rotation(1,2,3)]))

    def test_rotations_with_different_values_have_different_hashes(self):
        self.assertFalse(Rotation(1,2,3) in set([Rotation(2,3,4)]))

    def test_produces_working_rotation_matrix(self):
        self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[0], (2, 8, 0)[0], 4)
        self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[1], (2, 8, 0)[1], 4)
        self.assertAlmostEquals((Rotation(-math.pi/2,0,math.pi/2).matrix() * (8,0,-2))[2], (2, 8, 0)[2], 4)


class Vector2dTests(unittest.TestCase):

    def test_vectors_with_same_values_are_equal(self):
        self.assertEqual(Vector2d(0,0), Vector2d(0,0))
    
    def test_vectors_with_different_values_are_not_equal(self):
        self.assertNotEqual(Vector2d(0,0), Vector2d(0,1))

    def test_adding_two_vectors_gives_correct_vector(self):
        self.assertEqual(Vector2d(1,2) + Vector2d(2,3), Vector2d(3,5))

    def test_subtracting_two_vectors_gives_correct_vector(self):
        self.assertEqual(Vector2d(1,2) - Vector2d(2,3), Vector2d(-1,-1))

    def test_multiplying_by_scalar_gives_correct_vector(self):        
        self.assertEqual(Vector2d(1,2) * 5, Vector2d(5,10))

    def test_construction_from_direction_and_magnitude(self):
        self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).i, Vector2d(0,2).i, 4)
        self.assertAlmostEqual(Vector2d(dir=math.pi/2,mag=2).j, Vector2d(0,2).j, 4)
        
    def test_get_mag_returns_length_of_vector(self):
        self.assertAlmostEqual(Vector2d(3,4).get_mag(), 5, 4)

    def test_get_dir_returns_angle_of_vector(self):
        self.assertAlmostEqual(Vector2d(3,3).get_dir().val, Angle(math.pi/4).val, 4)

    def test_unit_returns_length_one_vector_with_same_direction(self):
        n = Vector2d(3,4).unit()
        self.assertAlmostEqual(n.get_mag(), 1.0, 4)
        self.assertAlmostEqual(n.get_dir().to_rad(), 0.9273, 4)
                    
    def test_dot_product_returns_correct_scalar_value(self):
        a = Vector2d(2,0)
        b = Vector2d(2,2)
        self.assertAlmostEqual(a.dot(b), 4.0, 4)
        
    def test_indexing_returns_components(self):
        self.assertEqual(Vector2d(1,2)[0], 1.0)
        self.assertEqual(Vector2d(1,2)[1], 2.0)
        
    def test_rotate_returns_correct_rotated_vector(self):
        self.assertAlmostEqual((Vector2d(1,2).rotate(math.pi/2))[0], Vector2d(-2,1)[0], 4)
        self.assertAlmostEqual((Vector2d(1,2).rotate(math.pi/2))[1], Vector2d(-2,1)[1], 4)
        
    def test_rotate_about_returns_correct_rotated_vector(self):
        self.assertAlmostEqual((Vector2d(1,2).rotate_about(math.pi/2,(2,3)))[0], Vector2d(3,2)[0], 4)
        self.assertAlmostEqual((Vector2d(1,2).rotate_about(math.pi/2,(2,3)))[1], Vector2d(3,2)[1], 4)
        
    def test_vectors_with_same_values_have_same_hash(self):
        self.assertTrue(Vector2d(1,2) in set([Vector2d(1,2)]))

    def test_vectors_with_different_values_have_different_hashes(self):
        self.assertFalse(Vector2d(1,2) in set([Vector2d(2,3)]))


class Vector3dTests(unittest.TestCase):

    def test_vectors_with_same_values_are_equal(self):
        self.assertEqual(Vector3d(0,0,0), Vector3d(0,0,0))

    def test_vectors_with_different_values_are_not_equal(self):
        self.assertNotEqual(Vector3d(0,0,0), Vector3d(0,1,2))

    def test_addition_returns_correct_vector(self):
        self.assertEqual(Vector3d(1,2,3) + Vector3d(2,3,4), Vector3d(3,5,7))

    def test_subtraction_returns_correct_vector(self):
        self.assertEqual(Vector3d(1,2,3) - Vector3d(2,3,4), Vector3d(-1,-1,-1))

    def test_multiplication_by_scalar_returns_correct_vector(self):    
        self.assertEqual(Vector3d(1,2,3) * 5, Vector3d(5,10,15))

    def test_construction_from_direction_and_magnitude_gives_correct_vector(self):
        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).i, Vector3d(0,1.4142,1.4142).i, 4)
        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).j, Vector3d(0,1.4142,1.4142).j, 4)
        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).k, Vector3d(0,1.4142,1.4142).k, 4)
        
    def test_get_mag_returns_vector_length(self):
        self.assertAlmostEqual(Vector3d(0,4,3).get_mag(), 5, 4)

    def test_get_dir_returns_vector_direction_as_rotation(self):
        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().roll.val,  Rotation(0.0,math.pi/4,math.pi/2).roll.val,  4)
        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().pitch.val, Rotation(0.0,math.pi/4,math.pi/2).pitch.val, 4)
        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().yaw.val,   Rotation(0.0,math.pi/4,math.pi/2).yaw.val,   4)
        
    def test_unit_returns_length_one_vector_with_same_direction(self):
        v = Vector3d(9,8,7)
        direction = v.get_dir()
        unit = v.unit()
        self.assertAlmostEqual(unit.get_mag(), 1.0, 4)
        self.assertEqual(unit.get_dir(), direction)

    def test_dot_product_returns_correct_scalar_value(self):
        self.assertAlmostEqual(Vector3d(1,2,3).dot(Vector3d(4,5,6)), 1*4+2*5+3*6 ,4)

    def test_cross_product_returns_correct_vector_value(self):
        self.assertEqual(Vector3d(1,2,3).cross(Vector3d(4,5,6)), Vector3d(2*6-3*5,3*4-1*6,1*5-2*4))
                
    def test_indexing_returns_components(self):
        self.assertEqual(Vector3d(9,8,7)[0], 9.0)
        self.assertEqual(Vector3d(9,8,7)[1], 8.0)
        self.assertEqual(Vector3d(9,8,7)[2], 7.0)

    def test_rotate_returns_correctly_rotated_vector(self):
        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[0],Vector3d(0,0,-5)[0], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[1],Vector3d(0,0,-5)[1], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[2],Vector3d(0,0,-5)[2], 4)
        
    def test_rotate_about_returns_correctly_rotated_vector(self):
        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[0], Vector3d(5,-5,-5)[0], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[1], Vector3d(5,-5,-5)[1], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[2], Vector3d(5,-5,-5)[2], 4)
        
    def test_vectors_with_same_values_have_same_hash(self):
        self.assertTrue(Vector3d(1,2,3) in set([Vector3d(1,2,3)]))

    def test_vectors_with_different_values_have_different_hashes(self):
        self.assertFalse(Vector3d(1,2,3) in set([Vector3d(2,3,4)]))


class MeanTests(unittest.TestCase):

    def test_returns_correct_value_for_populated_list(self):
        self.assertEqual(8.0,mean([2,6,4,20]))

    def test_returns_zero_for_empty_list(self):
        self.assertEqual(0.0,mean([])) 

                    
class StandardDeviationTests(unittest.TestCase):

    def test_returns_correct_value_for_populated_list(self):
        self.assertAlmostEquals(7.071,standard_deviation([2,6,4,20]),3)

    def test_returns_zero_for_empty_list(self):
        self.assertEqual(0.0,standard_deviation([]))


class DeviationTest(unittest.TestCase):

    def test_returns_correct_value_for_populated_list(self):
        self.assertAlmostEquals(0.141,deviation([2,6,4,20],9),3)

    def test_returns_zero_for_empty_list(self):
        self.assertEqual(0.0,deviation([],5))


class WeightedRouletteTests(unittest.TestCase):

    def test_returns_results_with_correct_probabilities(self):
        items = {
            "alpha": 1,
            "beta": 2,
            "gamma": 7
        }
        results = {
            "alpha":0,
            "beta":0,
            "gamma":0
        }
        iterations = 10000
        for i in range(iterations):
            result = weighted_roulette(items)
            self.assertTrue(result!=None)
            results[result] += 1
            
        self.assertAlmostEquals(results["alpha"]/float(iterations),1.0/10.0,1)
        self.assertAlmostEquals(results["beta"]/float(iterations),2.0/10.0,1)
        self.assertAlmostEquals(results["gamma"]/float(iterations),7.0/10.0,1)

    def test_returns_none_for_empty_dict(self):
        self.assertIsNone(weighted_roulette({}))


class LeadAngleTests(unittest.TestCase):

    def test_returns_correct_angle_as_float_when_solution_possible(self):
        ang = lead_angle((math.sqrt(2),math.sqrt(2)),math.sqrt(2),math.pi,math.sqrt(2))
        self.assertAlmostEquals(math.pi/2.0,ang,2)
        
    def test_returns_none_when_bullet_and_target_are_already_at_same_position(self):
        self.assertEqual(None,lead_angle((0.0,0.0),1.0,0.0,1.0))

    def test_returns_none_when_bullet_cannot_catch_up_to_target(self):
        self.assertEqual(None,lead_angle((1.0,1.0),1.0,0.0,0.9))


class Line2dTests(unittest.TestCase):

    def test_lines_with_same_values_are_equal(self):
        self.assertEqual(Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0)), Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0)))
        
    def test_lines_with_different_values_are_not_equal(self):
        self.assertNotEqual(Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0)), Line2d(Vector2d(0.0,1.0),Vector2d(1.0,0.0)))

    def test_lines_with_same_values_have_same_hash(self):
        self.assertTrue(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(1,2))]))

    def test_lines_with_different_values_have_different_hashes(self):
        self.assertFalse(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(2,3))]))

    def test_length_returns_length_of_line(self):
        self.assertAlmostEqual(Line2d(Vector2d(1.0,2.0),Vector2d(3.0,4.0)).length(), 2.8284, 4)
        
    def test_dir_returns_correct_direction_vector(self):
        result = Line2d(Vector2d(1.0,2.0),Vector2d(3.0,4.0)).dir()
        self.assertAlmostEqual(result.mag(), 1.0, 4)
        self.assertAlmostEqual(result[0], 0.7071, 4)
        self.assertAlmostEqual(result[1], 0.7071, 4)
    
    
class Line3dTests(unittest.TestCase):

    def test_lines_with_same_values_are_equal(self):
        self.assertEqual(Line2d(Vector2d(0.0,1.0,2.0),Vector2d(1.0,2.0,3.0)), 
                         Line2d(Vector2d(0.0,1.0,2.0),Vector2d(1.0,2.0,3.0)))
    
    def test_lines_with_different_values_are_not_equal(self):
        self.assertNotEqual(Line2d(Vector2d(0.0,1.0,2.0),Vector2d(1.0,2.0,3.0)),
                            Line2d(Vector2d(2.0,1.0,0.0),Vector2d(2.0,1.0,3.0)))
                            
    def test_lines_with_same_values_have_same_hash(self):
        self.assertTrue(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(1,2,3))]))

    def test_lines_with_different_values_have_different_hashes(self):
        self.assertFalse(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(2,3,4))]))

    def test_length_returns_length_of_line_as_float(self):
        self.assertAlmostEqual(Line3d(Vector3d(0.0,1.0,2.0),Vector3d(3.0,4.0,5.0)).length(), 5.1962, 4)
        
    def test_dir_returns_correct_direction_vector(self):
        result = Line3d(Vector3d(0.0,1.0,2.0),Vector3d(3.0,4.0,5.0)).dir()
        self.assertAlmostEqual(result.mag(), 1.0, 4)
        self.assertAlmostEqual(result[0], 0.5774, 4)
        self.assertAlmostEqual(result[1], 0.5774, 4)
        self.assertAlmostEqual(result[2], 0.5774, 4)
    
    
class Polygon2dTests(unittest.TestCase):

    def test_lines_returns_correct_edge_definitions_as_line_objects(self):
        p = Polygon2d([Vector2d(0.0,0.0), Vector2d(1.0,0.0), Vector2d(1.0,1.0)])
        lines = [
            Line2d(Vector2d(0.0,0.0),Vector2d(1.0,0.0)),
            Line2d(Vector2d(1.0,0.0),Vector2d(1.0,1.0)),
            Line2d(Vector2d(1.0,1.0),Vector2d(0.0,0.0))
        ]
        self.assertEqual(lines, p.get_lines())
        
    def test_polygons_with_same_values_have_same_hash(self):        
        self.assertTrue(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
            in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3)))]))
            
    def test_polygons_with_different_values_have_different_hashes(self):
        self.assertFalse(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
            in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(4,5)))]))
        
        
class Polygon3dTests(unittest.TestCase):

    def test_points_returns_correct_vertex_definitions_as_vectors(self):
        p = Polygon3d([
            Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,0.0,0.0)),
            Line3d(Vector3d(1.0,0.0,0.0),Vector3d(0.0,1.0,0.0)),
            Line3d(Vector3d(0.0,1.0,0.0),Vector3d(0.0,0.0,0.0)),
            Line3d(Vector3d(0.0,0.0,0.0),Vector3d(0.0,0.0,1.0)),
            Line3d(Vector3d(1.0,0.0,0.0),Vector3d(0.0,0.0,1.0)),
            Line3d(Vector3d(0.0,1.0,0.0),Vector3d(0.0,0.0,1.0))
        ])
        points = set([
            Vector3d(0.0,0.0,0.0), Vector3d(1.0,0.0,0.0),
            Vector3d(0.0,1.0,0.0), Vector3d(0.0,0.0,1.0)
        ])
        self.assertEqual(points, p.get_points())
        
    def test_polygons_with_same_values_have_same_hash(self):
        self.assertTrue(Polygon3d((
                Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
            ))
            in set([Polygon3d((
                Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
            ))]))
        
    def test_polygons_with_different_values_have_different_hashes(self):
        self.assertFalse(Polygon3d((
                Line3d(Vector3d(0,0,0),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
            ))
            in set([Polygon3d((
                Line3d(Vector3d(0,9,0),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(1,0,0),Vector3d(0,1,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(1,0,0)),
                Line3d(Vector3d(0,0,1),Vector3d(0,1,0))
            ))]))


class RectangleTest(unittest.TestCase):

    def setUp(self):
        self.fiveten = Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,10.0))

    def test_rectangles_with_same_values_are_equal(self):
        self.assertEqual(Rectangle(Vector2d(1.0,2.0),Vector2d(3.0,4.0)), 
                         Rectangle(Vector2d(1.0,2.0),Vector2d(3.0,4.0)))
                         
    def test_rectangles_with_different_values_are_not_equal(self):
        self.assertNotEqual(Rectangle(Vector2d(1.0,2.0),Vector2d(3.0,4.0)),
                            Rectangle(Vector2d(2.0,1.0),Vector2d(4.0,3.0)))
            
    def test_nw_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-4.0,-4.0),Vector2d(-2.0,-2.0)))
        
    def test_n_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(2.0,-4.0),Vector2d(3.0,-2.0)))
        
    def test_ne_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(7.0,-4.0),Vector2d(9.0,-2.0)))

    def test_w_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-4.0,2.0),Vector2d(-2.0,8.0)))
        
    def test_e_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(7.0,2.0),Vector2d(9.0,8.0)))
    
    def test_sw_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-4.0,12.0),Vector2d(-2.0,14.0)))
        
    def test_s_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(2.0,12.0),Vector2d(3.0,14.0)))
        
    def test_se_rect_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(7.0,12.0),Vector2d(9.0,14.0)))

    def test_rect_across_top_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-2.0,-4.0),Vector2d(7.0,-2.0)))
        
    def test_rect_across_bottom_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-2.0,12.0),Vector2d(7.0,14.0)))
        
    def test_rect_down_left_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(-4.0,-2.0),Vector2d(-2.0,12.0)))
        
    def test_rect_down_right_doesnt_intersect(self):
        self._noisec(Rectangle(Vector2d(7.0,-2.0),Vector2d(9.0,12.0)))

    def test_intersects_through_nw(self):
        self._yesisec(Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,2.0)))
        
    def test_intersects_through_n(self):
        self._yesisec(Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,2.0)))
        
    def test_intersects_through_ne(self):
        self._yesisec(Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,2.0)))
        
    def test_intersects_through_w(self):
        self._yesisec(Rectangle(Vector2d(-2.0,2.0),Vector2d(2.0,8.0)))
        
    def test_intersects_inside(self):
        self._yesisec(Rectangle(Vector2d(2.0,2.0),Vector2d(3.0,8.0)))
        
    def test_intersects_through_e(self):
        self._yesisec(Rectangle(Vector2d(3.0,2.0),Vector2d(7.0,8.0)))
        
    def test_intersects_through_sw(self):
        self._yesisec(Rectangle(Vector2d(-2.0,8.0),Vector2d(2.0,12.0)))

    def test_intersects_through_s(self):
        self._yesisec(Rectangle(Vector2d(2.0,8.0),Vector2d(3.0,12.0)))
        
    def test_intersects_through_se(self):
        self._yesisec(Rectangle(Vector2d(3.0,8.0),Vector2d(7.0,12.0)))

    def test_intersects_through_top(self):
        self._yesisec(Rectangle(Vector2d(-2.0,-2.0),Vector2d(7.0,2.0)))
        
    def test_intersects_through_middle_horizontally(self):
        self._yesisec(Rectangle(Vector2d(-2.0,2.0),Vector2d(7.0,8.0)))
        
    def test_intersects_through_bottom(self):
        self._yesisec(Rectangle(Vector2d(-2.0,8.0),Vector2d(7.0,12.0)))
        
    def test_intersects_through_left(self):
        self._yesisec(Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,12.0)))

    def test_intersects_through_middle_vertically(self):
        self._yesisec(Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,12.0)))
        
    def test_intersects_through_right(self):
        self._yesisec(Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,12.0)))

    def test_intersects_when_surrounded(self):
        self._yesisec(Rectangle(Vector2d(-2.0,-2.0),Vector2d(6.0,12.0)))

    def test_intersection_returns_correct_rectangle_for_overlap(self):
        self.assertEqual(Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,5.0)),
                         Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,10.0)).intersection(
                            Rectangle(Vector2d(-2.0,-3.0),Vector2d(5.0,5.0))))
                            
    def test_intersection_returns_same_rect_for_identical_rectangles(self):
        self.assertEqual(Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,10.0)),
                         Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,10.0)).intersection(
                            Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,10.0))))
                            
    def test_intersection_returns_none_when_rects_dont_intersect(self):
        self.assertIsNone(Rectangle(Vector2d(-5.0,-5.0),Vector2d(5.0,5.0)).intersection(
                            Rectangle(Vector2d(6.0,6.0),Vector2d(7.0,7.0))))

    def _noisec(self,rect):
        self.assertFalse(self.fiveten.intersects(rect))
        
    def _yesisec(self,rect):
        self.assertTrue(self.fiveten.intersects(rect))


class MatrixTest(unittest.TestCase):

    def test_matrices_with_same_values_are_equal(self):
        self.assertEqual(Matrix(((1,2),(3,4))),Matrix(((1,2),(3,4))))

    def test_matrices_with_different_values_are_not_equal(self):
        self.assertNotEqual(Matrix(((1,2),(3,4))),Matrix(((5,6,7),(8,9,10))))

    def test_addition_returns_correct_matrix(self):
        self.assertEqual( Matrix(((1,2,3),(4,5,6)))+Matrix(((3,4,5),(6,7,8))), 
            Matrix(((4,6,8),(10,12,14))) )
            
    def test_subtraction_returns_correct_matrix(self):
        self.assertEqual( Matrix(((1,2,3),(4,5,6)))-Matrix(((3,4,5),(6,7,8))),
            Matrix(((-2,-2,-2),(-2,-2,-2))) )        
            
    def test_additional_of_different_sized_matrices_raises_typeerror(self):
        self.assertRaises(TypeError, 
            lambda: Matrix(((1,2,3),(4,5,6))) + Matrix(((1,2),(3,4),(5,6))) )
            
    def test_substraction_of_different_sized_matrices_raises_typeerror(self):
        self.assertRaises(TypeError,
            lambda: Matrix(((1,2,3),(4,5,6))) - Matrix(((1,2),(3,4),(5,6))) )
    
    def test_addition_with_tuple_returns_correct_matrix(self):
        self.assertEqual( Matrix((2,3,4)) + (1,2,3), Matrix((3,5,7)) )
        
    def test_subtraction_with_tuple_returns_correct_matrix(self):
        self.assertEqual( Matrix((2,3,4)) - (1,2,3), Matrix((1,1,1)) )

    def test_multiplication_with_scalar_on_rhs_returns_correct_matrix(self):            
        self.assertEqual( Matrix(((1,2,3),(4,5,6))) * 2.0, Matrix(((2,4,6),(8,10,12))) )

    def test_multiplication_with_scalar_on_lhs_returns_correct_matrix(self):
        self.assertEqual( 2.0 * Matrix(((1,2,3),(4,5,6))), Matrix(((2,4,6),(8,10,12))) )

    def test_division_by_scalar_returns_correct_matrix(self):
        self.assertEqual( Matrix(((1,2,3),(4,5,6))) / 2.0, Matrix(((0.5,1,1.5),(2,2.5,3))) )

    def test_multiplication_with_matrix_returns_correct_matrix(self):
        self.assertEqual( Matrix(((1,2,3),(4,5,6))) * Matrix(((1,2),(3,4),(5,6))),
            Matrix(((1*1+2*3+3*5, 1*2+2*4+3*6),(4*1+5*3+6*5, 4*2+5*4+6*6))) )
            
    def test_multiplication_with_sequence_on_lhs_returns_correct_matrix(self):
        self.assertEqual( [[1,2,3],[4,5,6]] * Matrix([9,8,7]),
            Matrix([1*9+2*8+3*7,4*9+5*8+6*7]) )            

    def test_multiplication_with_sequence_on_rhs_returns_correct_sequence(self):
        self.assertEqual( Matrix(((1,2,3),(4,5,6))) * [[9],[8],[7]],
             [1*9+2*8+3*7, 4*9+5*8+6*7] )            
             
    def test_identity_returns_correct_identity_matrix(self):
        self.assertEqual(Matrix.identity(2), Matrix(((1,0),(0,1))))

    def test_transpose_returns_correctly_transposed_matrix(self):
        self.assertEqual(Matrix(((1,2),(3,4),(5,6))).transpose(), Matrix(((1,3,5),(2,4,6))))

    def test_matrices_with_same_values_have_same_hash(self):            
        self.assertTrue(Matrix(((1,2),(3,4))) in set([Matrix(((1,2),(3,4)))]))

    def test_matrices_with_different_values_have_different_hashes(self):
        self.assertFalse(Matrix(((1,2),(3,4))) in set([Matrix(((9,8),(7,6)))]))
        
             
class PlaneTests(unittest.TestCase):
        
    def test_planes_with_same_values_are_equal(self):
        self.assertEqual(Plane(Vector3d(1.0,2.0,3.0),Vector3d(4.0,5.0,6.0)),
                         Plane(Vector3d(1.0,2.0,3.0),Vector3d(4.0,5.0,6.0)))    

    def test_planes_with_equivalent_values_are_equal(self):
        self.assertEqual(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0)),
                         Plane(Vector3d(1.0,2.0,40.0),Vector3d(2.0,2.0,0.0)))    

    def test_planes_with_non_equivalent_values_are_not_equal(self):
        self.assertNotEqual(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0)),
                            Plane(Vector3d(1.0,10.0,40.0),Vector3d(2.0,2.0,0.0)))    
                            
    def test_planes_with_equivalent_values_have_same_hash(self):
        self.assertTrue(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0)) 
            in set([Plane(Vector3d(1.0,2.0,40.0),Vector3d(2.0,2.0,0.0))]))
            
    def test_planes_with_non_equivalent_values_have_different_hashes(self):
        self.assertFalse(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0)) 
            in set([Plane(Vector3d(1.0,10.0,40.0),Vector3d(2.0,2.0,0.0))]))
    
    def test_point_on_plane_returns_true_if_point_on_plane(self):
        self.assertTrue(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .point_on_plane(Vector3d(2.0,1.0,3.0)))
            
    def test_point_on_plane_returns_false_if_point_not_on_plane(self):
        self.assertFalse(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .point_on_plane(Vector3d(2.0,2.0,3.0)))
    
    def test_is_parallel_returns_true_for_parallel_vector(self):
        self.assertTrue(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .is_parallel(Vector3d(-0.5,0.5,1.0)))
                
    def test_is_parallel_returns_false_for_non_parallel_vector(self):
        self.assertFalse(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .is_parallel(Vector3d(-0.5,0.75,1.0)))
    
    def test_line_intersection_returns_correct_point_when_segment_intersects(self):
        self.assertEqual(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .line_intersection(Line3d(Vector3d(-2.0,1.0,-4.0),Vector3d(2.0,5.0,2.0))), 
            Vector3d(0.0,3.0,-1.0))
        
    def test_line_intersection_returns_none_if_segment_is_parallel(self):
        self.assertIsNone(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .line_intersection(Line3d(Vector3d(2.0,3.0,-1.0),Vector3d(1.5,3.5,0.0))))
    
    def test_line_intersection_returns_none_if_segment_doesnt_reach_plane(self):
        self.assertIsNone(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .line_intersection(Line3d(Vector3d(-2.0,1.0,-4.0),Vector3d(-1.0,2.0,2.0))))
    
    def test_line_intersection_returns_none_if_segment_is_beyond_plane(self):
        self.assertIsNone(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .line_intersection(Line3d(Vector3d(1.0,4.0,-4.0),Vector3d(2.0,5.0,2.0))))
    
    def test_line_intersection_returns_none_if_segment_lies_on_plane(self):
        self.assertIsNone(Plane(Vector3d(1.0,2.0,3.0),Vector3d(1.0,1.0,0.0))
            .line_intersection(Line3d(Vector3d(0.0,3.0,-4.0),Vector3d(2.0,1.0,2.0))))
    
    
class CuboidTests(unittest.TestCase):
    # TODO
    pass
