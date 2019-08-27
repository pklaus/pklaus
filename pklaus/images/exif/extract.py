
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

def cli():
    import argparse, pprint, json
    parser = argparse.ArgumentParser()
    parser.add_argument('image')
    parser.add_argument('--backend', '-b', choices=('exifread', 'pillow'), default='exifread')
    args = parser.parse_args()
    if args.backend == 'exifread':
        data = extract_exif_exifread(args.image)
    elif args.backend == 'pillow':
        data = extract_exif_pillow(args.image)
    for key in data:
        if key == 'EXIF MakerNote':
            data[key] = bytes(data[key].values).hex()
        elif type(data[key]).__name__ == 'IfdTag':
            values = data[key].values
            if type(values) in (tuple, list):
                values = [str(value) if type(value).__name__ == 'Ratio' else value for value in values]
            if type(values) in (tuple, list) and len(values) == 1:
                values = values[0]
            data[key] = values
        elif type(data[key]) is dict:
            for subkey in data[key]:
                if type(data[key][subkey]) == bytes:
                    data[key][subkey] = data[key][subkey].hex()
        elif type(data[key]) is bytes:
            data[key] = data[key].hex()
    print(json.dumps(data))
