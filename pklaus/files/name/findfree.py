
def get_available_filename(name, ext='.jpg', tpl='{name}_{i:02d}{ext}'):
    import os.path
    fullname = name + ext
    if not os.path.isfile(fullname):
        return fullname
    for i in range(1,99):
        fullname = tpl.format(name=name, ext=ext, i=i)
        if not os.path.isfile(fullname):
            return fullname
    raise NameError('No path available')
