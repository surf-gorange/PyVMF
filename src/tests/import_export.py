import difflib
import unittest
from PyVMF import *


def export_files(f1, f2):
    with open("dump/base.vmf", 'w+') as f:
        f.writelines(f1)

    with open("dump/generated.vmf", 'w+') as f:
        f.writelines(f2)


def stupid_error_check(f1, f2):
    if len(f1) != len(f2):
        return False

    for i in range(len(f1)):
        if f1 != f2:
            for j, s in enumerate(difflib.ndiff(f1[i], f2[i])):
                if s[0] == ' ':
                    continue
                elif s[0] == '-':
                    if s[-1] != "0":
                        return False

    return True


class TestImportExport(unittest.TestCase):
    def test_blank(self):
        v = load_vmf("blank.vmf")
        v.export("blank_g.vmf")

        with open("blank.vmf", 'r') as f:
            t = sorted(f.readlines())

        with open("blank_g.vmf", 'r') as f:
            t_o = sorted(f.readlines())

        try:
            self.assertTrue(t == t_o)
        except AssertionError as e:
            try:
                self.assertTrue(stupid_error_check(t, t_o))
            except AssertionError as e2:
                export_files(t, t_o)
                self.assertTrue(False)

    def test_cube(self):
        v = load_vmf("cube.vmf")
        v.export("cube_g.vmf")

        with open("cube.vmf", 'r') as f:
            t = sorted(f.readlines())

        with open("cube_g.vmf", 'r') as f:
            t_o = sorted(f.readlines())

        try:
            self.assertTrue(t == t_o)
        except AssertionError as e:
            try:
                self.assertTrue(stupid_error_check(t, t_o))
            except AssertionError as e2:
                export_files(t, t_o)
                self.assertTrue(False)

    def test_varied(self):
        v = load_vmf("varied.vmf")
        v.export("varied_g.vmf")

        with open("varied.vmf", 'r') as f:
            t = sorted(f.readlines())

        with open("varied_g.vmf", 'r') as f:
            t_o = sorted(f.readlines())

        try:
            self.assertTrue(t == t_o)
        except AssertionError as e:
            try:
                self.assertTrue(stupid_error_check(t, t_o))
            except AssertionError as e2:
                export_files(t, t_o)
                self.assertTrue(False)

    def test_changed(self):
        v = load_vmf("varied.vmf")
        v.get_solids()[0].move(12, 0, 0)
        v.export("varied_g.vmf")

        with open("varied.vmf", 'r') as f:
            t = sorted(f.readlines())

        with open("varied_g.vmf", 'r') as f:
            t_o = sorted(f.readlines())

        try:
            self.assertFalse(t == t_o)
        except AssertionError as e:
            try:
                self.assertTrue(stupid_error_check(t, t_o))
            except AssertionError as e2:
                export_files(t, t_o)
                self.assertTrue(False)


if __name__ == '__main__':
    unittest.main()
