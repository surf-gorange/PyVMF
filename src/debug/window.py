from PyVMF import *

v = load_vmf("window.vmf")

for i in range(15):
    c = Color()
    c.random()
    v.add_entities(EntityGenerator.light(Vertex(i*64, 0, 0), c))

v.export("window_g.vmf")
