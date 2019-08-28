def comfort_delete(files, backup_folder=None, verbose=True, dry=True):
    import os, errno, shutil
    if len(files) == 0: return
    if backup_folder:
        try:
            os.mkdir(backup_folder)
        except OSError as e:
            if not e.errno == errno.EEXIST:
                raise
        for filename in files:
            if verbose: print("Moving %s to %s." % (filename, backup_folder))
            if not dry: shutil.move(filename, os.path.join(backup_folder))
    else:
        for filename in files:
            if verbose: print("Deleting %s." % (filename,))
            if not dry: os.remove(filename)


