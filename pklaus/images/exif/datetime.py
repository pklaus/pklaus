
def datetime_exifread(fullname):
    from datetime import datetime
    from pklaus.images.exif.extract import extract_exif_exifread
    data = extract_exif_exifread(fullname)
    if 'EXIF SubSecDateTimeOriginal' in data:
        date_str = data['EXIF SubSecDateTimeOriginal'].values
    elif 'EXIF DateTimeOriginal' in data:
        date_str = data['EXIF DateTimeOriginal'].values
    elif 'Image DateTime' in data:
        date_str = data['Image DateTime'].values
    else:
    #elif not data:
        raise NameError("Couln't determine the exif datetime for file %s" % fullname)
    dt = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    return dt

def datetime_pillow(fullname):
    from datetime import datetime, timedelta
    from pklaus.images.exif.extract import extract_exif_pillow
    data = extract_exif_pillow(fullname)
    dt = datetime.strptime(data['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')
    #dt = dt + timedelta(milliseconds=(int(data['SubsecTimeOriginal'])*10))
    return dt
