import unittest
from PyVMF import *


class TestImportExport(unittest.TestCase):
    def test_blank(self):
        v = load_vmf("blank.vmf")
        v.export("blank_g.vmf")

        with open("blank.vmf", 'r') as f:
            t = f.readlines()

        with open("blank_g.vmf", 'r') as f:
            t_o = f.readlines()

        self.assertTrue(t.sort() == t_o.sort())

    def test_cube(self):
        v = load_vmf("cube.vmf")
        v.export("cube_g.vmf")

        with open("cube.vmf", 'r') as f:
            t = f.readlines()

        with open("cube_g.vmf", 'r') as f:
            t_o = f.readlines()

        self.assertTrue(t.sort() == t_o.sort())

    def test_varied(self):
        v = load_vmf("varied.vmf")
        v.export("varied_g.vmf")

        with open("varied.vmf", 'r') as f:
            t = f.readlines()

        with open("varied_g.vmf", 'r') as f:
            t_o = f.readlines()

        self.assertTrue(t.sort() == t_o.sort())


if __name__ == '__main__':
    unittest.main()
