
def fix_exif_dates(img_path, timedelta, dry_run=True):
    """
    Fix EXIF timestamps if date & time were set incorrectly
    on the camera when capturing the image.
    The file's access and modified times are preserved (restored).

    timedelta : datetime.timedelta applied to the original timestamp.
    """

    # Uses GExiv2
    # A GObject-based wrapper around the Exiv2 library.
    # Ubuntu/Debian: apt-get install gir1.2-gexiv2-0.10 libgexiv2-2
    # Mac OS X: brew install pygobject3 gtk+3 gexiv2
    # Arch Linux: pacman -S libgexiv2
    import gi
    gi.require_version('GExiv2', '0.10')
    from gi.repository import GExiv2
    import os
    from datetime import datetime as dt

    stat_result = os.stat(img_path)
    exif = GExiv2.Metadata()
    exif.open_path(img_path)
    orig_ts = exif.get_tag_string('Exif.Image.DateTime')
    orig_dt = dt.strptime(orig_ts, '%Y:%m:%d %H:%M:%S')
    fixed_dt = orig_dt + timedelta
    fixed_ts = fixed_dt.strftime('%Y:%m:%d %H:%M:%S')
    if not dry_run:
        exif.set_tag_string('Exif.Image.DateTime', fixed_ts)
        exif.set_tag_string('Exif.Photo.DateTimeDigitized', fixed_ts)
        exif.set_tag_string('Exif.Photo.DateTimeOriginal', fixed_ts)
        exif.save_file(img_path)
        os.utime(img_path, (stat_result.st_atime_ns, stat_result.st_mtime_ns))
    return (orig_dt, fixed_dt)

def main():
    """
    Recursively scan a directory tree, fixing the
    EXIF datetime tags on all jpg/png image files.
    Modifications are done in-place.
    """
    import argparse, os
    from datetime import timedelta
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=float, default=0)
    parser.add_argument('--hours', type=int, default=0)
    parser.add_argument('--minutes', type=float, default=0)
    parser.add_argument('--seconds', type=float, default=0)
    parser.add_argument('--add', '-a', action='store_true')
    parser.add_argument('--subtract', '-s', action='store_true')
    parser.add_argument('--dry-run', '-d', action='store_true')
    parser.add_argument('folder', default='.')
    args = parser.parse_args()
    if not args.add and not args.subtract:
        parser.error('Please select --add or --subtract')
    if args.add and args.subtract:
        parser.error('Select either --add or --subtract')
    td = timedelta(days=args.days, hours=args.hours, minutes=args.minutes, seconds=args.seconds)
    if args.subtract:
        td = -td
    if args.dry_run:
        print("Dry run, only stating potential changes without performing them")
    found_something = False
    for root, dirs, file_names in os.walk(args.folder):
        for file_name in file_names:
            if file_name.lower().endswith(('jpg', 'png')):
                found_something = True
                img_path = os.path.join(root, file_name)
                old_dt, new_dt = fix_exif_dates(img_path, td, dry_run=args.dry_run)
                print(f"{old_dt} → {new_dt} {img_path}")
    if not found_something:
        print(f"No image found in '{args.folder}'")
