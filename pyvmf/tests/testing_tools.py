import difflib


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
