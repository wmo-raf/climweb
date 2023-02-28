def get_duplicates(dict_):
    rev_multidict = {}

    for key, value in dict_.items():
        rev_multidict.setdefault(value, set()).add(key)

    dups = [key for key, values in rev_multidict.items() if len(values) > 1]

    return dups