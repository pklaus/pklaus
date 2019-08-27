
def extract_exif_exifread(fullname):
    from exifread import process_file
    with open(fullname, "rb") as f:
        return process_file(f)

def extract_exif_pillow(fullname):
    """
    Inspired by a comment on http://goo.gl/6WsPi
    Alternative: pyexiv2 http://tilloy.net/dev/pyexiv2/
    """
    from PIL import Image
    from PIL.ExifTags import TAGS
    ret = {}
    i = Image.open(fullname)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        ret[decoded] = value
    return ret
