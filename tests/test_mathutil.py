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
                

class Test(unittest.TestCase):

    def testVector3dMath(self):
        self.assertEqual(Vector3d(0,0,0), Vector3d(0,0,0))
        self.assertNotEqual(Vector3d(0,0,0), Vector3d(0,1,2))

        self.assertEqual(Vector3d(1,2,3) + Vector3d(2,3,4), Vector3d(3,5,7))
        self.assertEqual(Vector3d(1,2,3) - Vector3d(2,3,4), Vector3d(-1,-1,-1))
        self.assertEqual(Vector3d(1,2,3) * 5, Vector3d(5,10,15))

        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).i, Vector3d(0,1.4142,1.4142).i, 4)
        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).j, Vector3d(0,1.4142,1.4142).j, 4)
        self.assertAlmostEqual(Vector3d(dir=Rotation(0.5,math.pi/4,math.pi/2),mag=2).k, Vector3d(0,1.4142,1.4142).k, 4)

        self.assertAlmostEqual(Vector3d(0,4,3).get_mag(), 5, 4)

        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().roll.val,  Rotation(0.0,math.pi/4,math.pi/2).roll.val,  4)
        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().pitch.val, Rotation(0.0,math.pi/4,math.pi/2).pitch.val, 4)
        self.assertAlmostEqual(Vector3d(0,4,4).get_dir().yaw.val,   Rotation(0.0,math.pi/4,math.pi/2).yaw.val,   4)

        self.assertAlmostEqual(Vector3d(9,8,7).unit().get_mag(), 1.0, 4)

        self.assertAlmostEqual(Vector3d(1,2,3).dot(Vector3d(4,5,6)), 1*4+2*5+3*6 ,4)
        self.assertEqual(Vector3d(1,2,3).cross(Vector3d(4,5,6)), Vector3d(2*6-3*5,3*4-1*6,1*5-2*4))

        self.assertEqual(Vector3d(9,8,7)[0], 9.0)
        self.assertEqual(Vector3d(9,8,7)[1], 8.0)
        self.assertEqual(Vector3d(9,8,7)[2], 7.0)

        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[0],Vector3d(0,0,-5)[0], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[1],Vector3d(0,0,-5)[1], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate((-math.pi/2,math.pi/2,math.pi/2)))[2],Vector3d(0,0,-5)[2], 4)

        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[0], Vector3d(5,-5,-5)[0], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[1], Vector3d(5,-5,-5)[1], 4)
        self.assertAlmostEqual((Vector3d(5,0,0).rotate_about((-math.pi/2,0,0),(5,-5,0)))[2], Vector3d(5,-5,-5)[2], 4)

        self.assertTrue(Vector3d(1,2,3) in set([Vector3d(1,2,3)]))
        self.assertFalse(Vector3d(1,2,3) in set([Vector3d(2,3,4)]))

    def testStandardDeviation(self):
        self.assertEquals(8.0,mean([2,6,4,20]))
        self.assertEquals(0.0,mean([])) 
        self.assertAlmostEquals(7.071,standard_deviation([2,6,4,20]),3)
        self.assertEquals(0.0,standard_deviation([]))
        self.assertAlmostEquals(0.141,deviation([2,6,4,20],9),3)
        self.assertEquals(0.0,deviation([],5))

    def testRoulette(self):
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
        for i in range(1000):
            result = weighted_roulette(items)
            self.assert_(result!=None)
            results[result] += 1
            
        self.assertAlmostEquals(results["alpha"]/1000.0,1.0/10.0,1)
        self.assertAlmostEquals(results["beta"]/1000.0,2.0/10.0,1)
        self.assertAlmostEquals(results["gamma"]/1000.0,7.0/10.0,1)

    def testLeadAngle(self):
        ang = lead_angle((math.sqrt(2),math.sqrt(2)),math.sqrt(2),math.pi,math.sqrt(2))
        self.assertAlmostEquals(math.pi/2.0,ang,2)
        self.assertEquals(None,lead_angle((0.0,0.0),1.0,0.0,1.0))
        self.assertEquals(None,lead_angle((1.0,1.0),1.0,0.0,0.9))

    
    def testLine2d(self):
        line1 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
        line2 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,1.0))
        line3 = Line2d(Vector2d(0.0,0.0),Vector2d(1.0,0.0))
        self.assertEquals(line1, line2)
        self.assertNotEquals(line2, line3)
        self.assertNotEquals(line3, line1)

        self.assertTrue(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(1,2))]))
        self.assertFalse(Line2d(Vector2d(0,0),Vector2d(1,2)) in set([Line2d(Vector2d(0,0),Vector2d(2,3))]))
        
    def testLine3d(self):
        line1 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,1.0,1.0))
        line2 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,1.0,1.0))
        line3 = Line3d(Vector3d(0.0,0.0,0.0),Vector3d(1.0,0.0,1.0))
        self.assertEquals(line1, line2)
        self.assertNotEquals(line2, line3)
        self.assertNotEquals(line3, line1)

        self.assertTrue(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(1,2,3))]))
        self.assertFalse(Line3d(Vector3d(0,0,0),Vector3d(1,2,3)) in set([Line3d(Vector3d(0,0,0),Vector3d(2,3,4))]))

    def testPolygon2d(self):
        p = Polygon2d([Vector2d(0.0,0.0), Vector2d(1.0,0.0), Vector2d(1.0,1.0)])
        lines = [
            Line2d(Vector2d(0.0,0.0),Vector2d(1.0,0.0)),
            Line2d(Vector2d(1.0,0.0),Vector2d(1.0,1.0)),
            Line2d(Vector2d(1.0,1.0),Vector2d(0.0,0.0))
        ]
        self.assertEquals(lines, p.get_lines())

        self.assertTrue(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
            in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3)))]))
        self.assertFalse(Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(2,3))) 
            in set([Polygon2d((Vector2d(0,0),Vector2d(1,2),Vector2d(4,5)))]))

    def testPolygon3d(self):
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
        self.assertEquals(points, p.get_points())

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

    def testRectangle(self):
        r1 = Rectangle(Vector2d(0.0,0.0), Vector2d(5.0,10.0))
        r2 = Rectangle(Vector2d(0.0,0.0), Vector2d(5.0,10.0))
        r3 = Rectangle(Vector2d(-2.0,-3.0),Vector2d(5.0,5.0))

        self.assertEqual(r1, r2)
        self.assertNotEqual(r2, r3)
        self.assertNotEqual(r3, r1)

        noisec = [
            Rectangle(Vector2d(-4.0,-4.0),Vector2d(-2.0,-2.0)),
            Rectangle(Vector2d(2.0,-4.0),Vector2d(3.0,-2.0)),
            Rectangle(Vector2d(7.0,-4.0),Vector2d(9.0,-2.0)),
            Rectangle(Vector2d(-4.0,2.0),Vector2d(-2.0,8.0)),
            Rectangle(Vector2d(7.0,2.0),Vector2d(9.0,8.0)),
            Rectangle(Vector2d(-4.0,12.0),Vector2d(-2.0,14.0)),
            Rectangle(Vector2d(2.0,12.0),Vector2d(3.0,14.0)),
            Rectangle(Vector2d(7.0,12.0),Vector2d(9.0,14.0)),    

            Rectangle(Vector2d(-2.0,-4.0),Vector2d(7.0,-2.0)),
            Rectangle(Vector2d(-2.0,12.0),Vector2d(7.0,14.0)),
            Rectangle(Vector2d(-4.0,-2.0),Vector2d(-2.0,12.0)),
            Rectangle(Vector2d(7.0,-2.0),Vector2d(9.0,12.0))
        ]
        yesisec = [
            Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,2.0)),
            Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,2.0)),
            Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,2.0)),
            Rectangle(Vector2d(-2.0,2.0),Vector2d(2.0,8.0)),
            Rectangle(Vector2d(2.0,2.0),Vector2d(3.0,8.0)),
            Rectangle(Vector2d(3.0,2.0),Vector2d(7.0,8.0)),
            Rectangle(Vector2d(-2.0,8.0),Vector2d(2.0,12.0)),
            Rectangle(Vector2d(2.0,8.0),Vector2d(3.0,12.0)),
            Rectangle(Vector2d(3.0,8.0),Vector2d(7.0,12.0)),

            Rectangle(Vector2d(-2.0,-2.0),Vector2d(7.0,2.0)),
            Rectangle(Vector2d(-2.0,2.0),Vector2d(7.0,8.0)),
            Rectangle(Vector2d(-2.0,8.0),Vector2d(7.0,12.0)),
            Rectangle(Vector2d(-2.0,-2.0),Vector2d(2.0,12.0)),
            Rectangle(Vector2d(2.0,-2.0),Vector2d(3.0,12.0)),
            Rectangle(Vector2d(3.0,-2.0),Vector2d(7.0,12.0))
        ]

        for r in yesisec:
            self.assertTrue(r1.intersects(r))
        for r in noisec:
            self.assertFalse(r1.intersects(r))

        isect = Rectangle(Vector2d(0.0,0.0),Vector2d(5.0,5.0))
        self.assertEqual(isect, r1.intersection(r3))
        self.assertEqual(r1, r1.intersection(r2))

    def testMatrix(self):
    
        self.assertEqual(Matrix(((1,2),(3,4))),Matrix(((1,2),(3,4))))
        self.assertNotEqual(Matrix(((1,2),(3,4))),Matrix(((5,6,7),(8,9,10))))
        
        self.assertEquals( Matrix(((1,2,3),(4,5,6)))+Matrix(((3,4,5),(6,7,8))), 
            Matrix(((4,6,8),(10,12,14))) )
        self.assertEquals( Matrix(((1,2,3),(4,5,6)))-Matrix(((3,4,5),(6,7,8))),
            Matrix(((-2,-2,-2),(-2,-2,-2))) )
            
        self.assertRaises(TypeError, 
            lambda: Matrix(((1,2,3),(4,5,6))) + Matrix(((1,2),(3,4),(5,6))) )
        self.assertRaises(TypeError,
            lambda: Matrix(((1,2,3),(4,5,6))) - Matrix(((1,2),(3,4),(5,6))) )

        self.assertEquals( Matrix((2,3,4)) + (1,2,3), Matrix((3,5,7)) )
        self.assertEquals( Matrix((2,3,4)) - (1,2,3), Matrix((1,1,1)) )

        self.assertEquals( Matrix(((1,2,3),(4,5,6))) * 2.0, Matrix(((2,4,6),(8,10,12))) )
        self.assertEquals( 2.0 * Matrix(((1,2,3),(4,5,6))), Matrix(((2,4,6),(8,10,12))) )

        self.assertEquals( Matrix(((1,2,3),(4,5,6))) / 2.0, Matrix(((0.5,1,1.5),(2,2.5,3))) )
        
        self.assertEquals( Matrix(((1,2,3),(4,5,6))) * Matrix(((1,2),(3,4),(5,6))),
            Matrix(((1*1+2*3+3*5, 1*2+2*4+3*6),(4*1+5*3+6*5, 4*2+5*4+6*6))) )
            
        self.assertEquals( [[1,2,3],[4,5,6]] * Matrix([9,8,7]),
            Matrix([1*9+2*8+3*7,4*9+5*8+6*7]) )
            
        self.assertEquals( Matrix(((1,2,3),(4,5,6))) * [[9],[8],[7]],
             [1*9+2*8+3*7, 4*9+5*8+6*7] )
            
        self.assertEquals(Matrix.identity(2), Matrix(((1,0),(0,1))))
        
        self.assertEquals(Matrix(((1,2),(3,4),(5,6))).transpose(), Matrix(((1,3,5),(2,4,6))))
        
        self.assertTrue(Matrix(((1,2),(3,4))) in set([Matrix(((1,2),(3,4)))]))
        self.assertFalse(Matrix(((1,2),(3,4))) in set([Matrix(((9,8),(7,6)))]))
        
        







