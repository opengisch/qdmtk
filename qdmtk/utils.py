def string_to_fid(string):
    """
    Converts a string to a longlong, matching QGIS's STRING_TO_FID macro
    """
    try:
        return int(string)
    except ValueError:
        return 0
