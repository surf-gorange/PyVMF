from PyVMF import *
from random import randint


def trigger_on_displacements(group: list, base_triangle, resolution=1):
    if resolution != 1 and resolution%2==1:
        raise ValueError("Resolution must either be 1 or a multiple of 2")

    l_extremities = [[(False, True), None, (False, False), (True, False)],
                     [(False, True), (True, True), (False, False), None]]
    r_extremities = [[(False, True), (True, True), None, (True, False)],
                     [None, (True, True), (False, False), (True, False)]]
    directions = (l_extremities, r_extremities)

    export_list = []

    for solid in group:
        disp = solid.get_displacement_sides()[0].get_displacement()
        if disp:
            matrix = disp.matrix

            size = solid.get_size()
            size.divide(disp.matrix_size_fix/resolution)

            triangle = base_triangle.copy()

            normal = True
            tris_list = []
            for sy in range(0, disp.matrix_size_fix, resolution):
                normal = not normal
                for sx in range(0, disp.matrix_size_fix, resolution):
                    left_tri = triangle.copy()

                    left_tri.rotate_z(left_tri.center_geo, normal * -90)
                    left_tri.scale(Vertex(0, 0, 0), size.x, size.y, 1)
                    left_tri.move(sx * size.x / resolution, sy * -size.y / resolution, 0)

                    right_tri = left_tri.copy()
                    right_tri.rotate_z(right_tri.center_geo, 180)

                    #--------------------------------- Change the values here for some cool geometry
                    left_tri.move(0, 0, 0)
                    right_tri.move(0, 0, 0)
                    #---------------------------------

                    tris = [left_tri, right_tri]

                    normal = not normal

                    i = 0
                    for x, y, vert in matrix.inv_rect(sx, sy, 2*resolution, 2*resolution, resolution):
                        for j, side in enumerate(directions):
                            direction = side[not normal][i]
                            if direction is not None:
                                for tri_vert in tris[j].get_3d_extremity(*direction)[1]:
                                    tri_vert.move(0, 0, vert.normal.z * vert.distance)

                        i += 1

                    tris_list.extend(tris)

            export_list.extend(tris_list)
            f = solid.get_3d_extremity(False, True, True)[0]
            diff = f.diff(tris_list[0].get_3d_extremity(False, True, True)[0])
            diff.z = f.diff(Vertex(0, 0, 0)).z
            for trio in tris_list:
                trio.move(*diff.export())

    return export_list


if __name__ == "__main__":
    v = load_vmf("trigger_example.vmf")

    d = v.get_all_from_visgroup("displacement")

    # m = d[0].get_displacement_sides(matrix_instead_of_side=True)[0]
    # for x, y, vert in m.rect(0, 0, m.size, m.size):
    #     vert.set((0, 0, 1), x*x*6)

    t = trigger_on_displacements(d, v.get_all_from_visgroup("trigger")[0], 2) # Set to 1 for perfect trigger coverage
    v.add_solids(*t)

    v.export("triggered_example.vmf")
