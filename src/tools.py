

def num(s):  # Tries to turn string into int, then float, if all fails returns string
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return str(s)