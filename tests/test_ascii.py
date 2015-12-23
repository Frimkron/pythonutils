import unittest
from mrf.ascii import Canvas


class TestCanvas(unittest.TestCase):

    def setUp(self):
        self.canvas = Canvas()

    def test_set_and_get_at_origin(self):
        self.assertEqual(' ', self.canvas.get(0, 0))
        self.canvas.set(0, 0, '@')
        self.assertEqual('@', self.canvas.get(0, 0))

    def test_set_and_get_at_position(self):
        self.assertEqual(' ', self.canvas.get(4, 5))
        self.canvas.set(4, 5, '@')
        self.assertEqual('@', self.canvas.get(4, 5))
        
    def test_write_sets_characters(self):
        self.assertEqual(' ', self.canvas.get(1, 2))
        self.canvas.write(1, 2, 'test')
        self.assertEqual('t', self.canvas.get(1, 2))
        self.assertEqual('e', self.canvas.get(2, 2))
        self.assertEqual('s', self.canvas.get(3, 2))
        self.assertEqual('t', self.canvas.get(4, 2))
        
    def test_render_empty_canvas(self):
        self.assertEqual('', self.canvas.render())
        
    def test_render_single_line_at_origin(self):
        self.canvas.write(0, 0, 'test')
        self.assertEqual('test\n', self.canvas.render())
        
    def test_render_single_line_at_position(self):
        self.canvas.write(1, 2, 'test')
        self.assertEqual('     \n     \n test\n', self.canvas.render())
        
    def test_render_multiple_positions(self):
        self.canvas.set(1, 2, '1')
        self.canvas.set(5, 3, '2')
        self.canvas.set(3, 4, '3')
        self.assertEqual('      \n      \n 1    \n     2\n   3  \n', self.canvas.render())

    def test_clear(self):
        self.canvas.write(5, 6, 'blah')
        self.assertNotEqual('', self.canvas.render())
        self.canvas.clear()
        self.assertEqual('', self.canvas.render())

    def test_rectangle(self):
        self.canvas.rectangle(1, 2, 4, 5)
        self.assertEqual('     \n     \n +--+\n |  |\n |  |\n |  |\n +--+\n', self.canvas.render())
