import yaml, os

__cached_files = {}

def cache_file(file):
    hashed_path = hash(file)

    if hashed_path in __cached_files:
        return __cached_files[hashed_path]
    else:
        with open(file, "r") as fobj:
            __cached_files[hashed_path] = yaml.safe_load(fobj)
        
        return cache_file(file)

def get_file(file):
    return cache_file(os.path.join("other/filedefaults", os.path.basename(file))) | cache_file(file)

def get_attr(file, attr):
    return get_file(file)[attr]