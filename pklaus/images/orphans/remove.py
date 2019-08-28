RAW_EXTENSIONS = (
    '.CR2', # for Canon
    '.RAF', # for Fuji
    '.NEF', # for Nikon
    '.RW2', # for Lumix
)

def main():
    global RAW_EXTENSIONS
    import argparse, re, sys, os
    from pklaus.files.removal.delete import comfort_delete

    def stderr(line):
        import sys
        sys.stderr.write(line + '\n')
        sys.stderr.flush()

    parser = argparse.ArgumentParser(description='Cleanup of leftover raw image files (*.CR2).')
    parser.add_argument('--no-backup', '-n', action='store_true',
            help='Don\'t backup orphaned raw images  -  delete them immediately.')
    parser.add_argument('--backup-folder', '-b', default='raw_orphans',
            help='Folder to move orphaned raw images to.')
    parser.add_argument('--tolerant', '-t', action='store_true',
            help='Accept JPEGs that just start with the name of the raw image as a match too.')
    parser.add_argument('--raw', '-r',
            help='Comma separated list of extensions considered a RAW image. Default: %s' % ','.join(RAW_EXTENSIONS))
    parser.add_argument('--quiet', '-q', action='store_true',
            help='Silence the less important output of this tool.')
    parser.add_argument('--dry', '-d', action='store_true',
            help='Dry run: Only show what the tool would do without actually executing.')
    parser.add_argument('folder', metavar='CHECK_FOLDER', default='./', nargs='?',
            help='Folder to check for raw images. Defaults to the current working directory')
    args = parser.parse_args()
    verbose = not args.quiet
    if args.raw:
        RAW_EXTENSIONS = args.raw.split(',')

    ext_patterns = (ext.lower().replace('.', r'\.') for ext in RAW_EXTENSIONS)
    full_pattern = r'(.*)(' + r'|'.join(ext_patterns) + r')$'
    if verbose: print('Regular expression match pattern for RAW images:', full_pattern)


    raw_images, jpeg_images_bare_names = [], []
    all_files = list(os.listdir(args.folder))
    # sort files into raw and jpeg files
    for filename in all_files:
        # The file name of raw image ends with
        if re.match(full_pattern, filename.lower()):
            raw_images.append(filename)
        if re.match(r'(.*)\.[jJ][pP][eE]?[gG]$', filename):
            jpeg_images_bare_names.append(os.path.splitext(filename)[0])
    # Check if there is a jpeg for each raw image
    orphans = []
    for raw_image in raw_images:
        if args.tolerant:
            is_orphan = True
            for jpg in jpeg_images_bare_names:
                if jpg.startswith(os.path.splitext(raw_image)[0]):
                    is_orphan = False
            if is_orphan:
                orphans.append(raw_image)
        elif os.path.splitext(raw_image)[0] not in jpeg_images_bare_names:
            orphans.append(raw_image)
    if len(raw_images) + len(jpeg_images_bare_names) == 0:
        if verbose: stderr("No images found. No use checking '%s' for orphaned RAW images." %
                (args.folder,))
        sys.exit(2)
    elif len(raw_images) == 0:
        if verbose: print("No RAW images found, but %i JPEGs. Won't do anything now." % (
                len(jpeg_images_bare_names),))
        sys.exit(0)
    elif len(orphans) == 0:
        if verbose: print("%i RAW images found, and %i JPEGs but no orphans. Won't do anything now." % (
                len(raw_images), len(jpeg_images_bare_names)))
        sys.exit(0)
    else:
        print("Found %i JPEGs and %i .CR2s. Of those RAW images, %i are orphans and will be removed." % (
                len(jpeg_images_bare_names), len(raw_images), len(orphans)))
    backup_folder = None if args.no_backup else os.path.join(args.folder,args.backup_folder)
    comfort_delete([os.path.join(args.folder,orphan) for orphan in orphans], backup_folder=backup_folder, verbose=verbose, dry=args.dry)
