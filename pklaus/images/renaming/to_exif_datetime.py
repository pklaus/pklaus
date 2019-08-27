#!/usr/bin/env python

"""
originally found at <https://gist.github.com/3155743>.

Also check <https://gist.github.com/4271012> for a tool to
clean up orphaned RAW image files in your photo dirs.
"""

def rename(fullname, dry_run=True, callback=None):
    from pklaus.images.exif.datetime import datetime_exifread
    from pklaus.files.name.findfree import get_available_filename
    import os, shutil
    dt = datetime_exifread(fullname)

    if callback:
        dt = callback(fullname, dt)

    extension = os.path.splitext(fullname)[1]
    try:
        date_format = dt.strftime('%Y-%m-%d_%H-%M-%S.%f')[:-4]
        dirname = os.path.dirname(fullname)
        fullnewname = get_available_filename(os.path.join(dirname, date_format), extension)
        print("Moving %s to %s." % (fullname, fullnewname))
        if dry_run: return
        shutil.move(fullname, fullnewname)
    except NameError as e:
        print(e)
        print("Cannot move %s; too many files for that date/time." % fullname)

def cli():
    import sys, os, re, argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', default='.')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--break-on-error', action='store_true')
    args = parser.parse_args()
    for filename in os.listdir(args.folder):
        if re.match(r'(.*)\.([jJ][pP][eE]?[gG]|[cC][rR]2)$', filename):
            fullname = os.path.join(args.folder, filename)
            try:
                rename(fullname, dry_run=args.dry_run)
            except NameError as e:
                print(e)
                if args.break_on_error: break

def example_callback(fullname, dt):
    """
    A callback function example showing how to modify the
    datetime determined for a specific picture depending
    on the camera model used to take it.
    """
    from datetime import timedelta
    from pklaus.images.exif.extract import extract_exif_pillow

    #dt = dt + timedelta(milliseconds=(int(data['SubsecTimeOriginal'])*10))

    data = extract_exif_pillow(fullname)

    # correct the EXIF time information (e.g. when time in a specific camera was set incorrectly):
    if data['Model'] == 'Canon EOS 40D':
        #pass # Kim or Ben's camera
        dt = dt + timedelta(minutes=2)
    elif data['Model'] == 'Canon EOS REBEL T3':
        #pass # my camera
        dt = dt - timedelta(minutes=1)
    elif data['Model'] == 'Canon IXUS 130':
        dt = dt + timedelta(hours=1) # someone else's camera
    else:
        print(f"Camera model '{data['Model']}'. "
              f"No special treatment set for this one. "
              f"Using the EXIF information as is.")
    return dt
