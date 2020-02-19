from PyVMF import *
from obj import *

v = new_vmf()

for solid in obj_to_solids("test.obj", "gorange/objtest", 14.5):
    v.add_solids(solid)

v.export("ico.vmf")
