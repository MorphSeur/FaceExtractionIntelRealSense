import os

def get_pretty_folder_size(path):
    return convert_bytes(get_folder_size(path))

def get_folder_size(start_path):
    total_size = 0
    total_size += os.path.getsize(start_path)
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
def convert_bytes(num):
	"""
	this function will convert bytes to MB.... GB... etc
	"""
	for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
		if num < 1024.0:
			return "%3.1f %s" % (num, x)
		num /= 1024.0




def intrinsics_to_obj(depth_intrinsic):
        return {'width':depth_intrinsic.width,
        'height':depth_intrinsic.height,
        'ppx':depth_intrinsic.ppx,
        'ppy':depth_intrinsic.ppy,
        'fx':depth_intrinsic.fx,
        'fy':depth_intrinsic.fy,
        'model':depth_intrinsic.model,
        'coeffs':depth_intrinsic.coeffs,
        }
def intrinsics_from_obj(obj):
        import pyrealsense2 as rs
        depth_intrinsic = rs.intrinsics()

        depth_intrinsic.width=obj['width']
        depth_intrinsic.height=obj['height']
        depth_intrinsic.ppx=obj['ppx']
        depth_intrinsic.ppy=obj['ppy']
        depth_intrinsic.fx=obj['fx']
        depth_intrinsic.fy=obj['fy']
        depth_intrinsic.model=obj['model']
        depth_intrinsic.coeffs=obj['coeffs']
        return depth_intrinsic
        

def in_notebook():
    try:
        from IPython import get_ipython
        if 'IPKernelApp' not in get_ipython().config:  # pragma: no cover
            return False
    except ImportError:
        return False
    except AttributeError:
        return False
    return True