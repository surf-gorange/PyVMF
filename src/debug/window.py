from PyVMF import *

v = load_vmf("window.vmf")

s = v.get_solids()[0]

a = s.get_3d_extremity(True)

window = s.naive_subdivide(3, 1, 3)
window.pop(4)

v.add_solids(*window)

v.export("window_g.vmf")
