from PyVMF import *

#######################################################################################################################
### TODO
### YOU CURRENTLY NEED TO FLIP THE TRIGGERS ON THE Y AXIS FOR IT TO FIT THE DISPLACEMENT (DO IT IN HAMMER)
#######################################################################################################################


def trigger_on_displacements(group: list, subdiv: int, base_triangle):
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
            size.divide(disp.matrix_size_fix)

            triangle = base_triangle.copy()

            normal = True
            tris_list = []
            for sy in range(disp.matrix_size_fix):
                normal = not normal
                for sx in range(disp.matrix_size_fix):
                    left_tri = triangle.copy()

                    left_tri.rotate_z(left_tri.center_geo, normal * -90)
                    left_tri.scale(Vertex(0, 0, 0), size.x, size.y, 1)
                    left_tri.move(sx * size.x, sy * -size.y, 0)

                    right_tri = left_tri.copy()
                    right_tri.rotate_z(right_tri.center_geo, 180)

                    tris = [left_tri, right_tri]

                    normal = not normal

                    i = 0
                    for x, y, vert in matrix.rect(sx, sy, 2, 2):
                        for j, side in enumerate(directions):
                            direction = side[not normal][i]
                            if direction is not None:
                                for tri_vert in tris[j].get_3d_extremity(*direction)[1]:
                                    tri_vert.move(0, 0, vert.normal.z * vert.distance)

                        i += 1

                    tris_list.extend(tris)

            export_list.extend(tris_list)
            f = solid.get_3d_extremity(False, True)[0]
            diff = f.diff(tris_list[0].center_geo)
            for trio in tris_list:
                trio.move(*diff)

    return export_list


if __name__ == "__main__":
    v = load_vmf("map.vmf")

    t = trigger_on_displacements(v.get_all_from_visgroup("displacement"), 2, v.get_all_from_visgroup("trigger")[0])
    v.add_solids(*t)

    v.export("triggered_map.vmf")
