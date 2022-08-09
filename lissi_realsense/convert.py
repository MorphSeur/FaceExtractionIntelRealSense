import psutil
from . import utils
import pickle
import sys
import time, threading
from multiprocessing import Process, JoinableQueue
import os

import cv2


def image_recorder(name, frame_number, img, save_path):
    import numpy as np
    import cv2
    try:
        os.makedirs(f"{save_path}/{name}/", exist_ok=True)
        import numpy as np
        target = f'{save_path}/{name}/{frame_number}'
        if name == 'Depth':
            img = img.astype(np.uint16)
            cv2.imwrite(target + ".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 5])
        else:
            cv2.imwrite(target + ".webp", img, [int(cv2.IMWRITE_WEBP_QUALITY), 100])
    except Exception as e:
        import traceback
        print(e)
        print(traceback.format_exc())


def video_recorder(name, q, save_path, profile):
    video = 1
    try:
        # print('video_recorder start')
        # if profile['type'] == 'Color': psutil.Process().cpu_affinity([2, 3])
        # if profile['type'] == 'Depth': psutil.Process().cpu_affinity([4, 5])
        # if 'Infrared' in profile['type']: psutil.Process().cpu_affinity([6, 7])

        # print(f'start recording {name} in cpu={psutil.Process().cpu_affinity()}')
        import numpy as np
        # codec = cv2.VideoWriter.fourcc(*'avc1')
        # codec = cv2.VideoWriter.fourcc(*'MJPG')

        codec = cv2.VideoWriter.fourcc(*'DIVX')
        if video:
            if profile['type'] == 'Depth':
                vw = cv2.VideoWriter(f'{save_path}/{name}.avi', codec, profile['fps'], (1920, 1080), False)
            else:
                vw = cv2.VideoWriter(f'{save_path}/{name}.avi', codec, profile['fps'], (profile['width'], profile['height']), profile['is_color'])

        # vw.write(np.zeros(profile['width'], profile['height'],3))
        while True:

            n, img = q.get()
            # print(name,n)
            if n == -1:
                q.task_done()
                break
            # cv2.imshow(name,img)

            # 	img = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)
            if video:
                if name == 'Depth':
                    img = cv2.convertScaleAbs(img, alpha=0.025)
                vw.write(img)
            # else:
            #     target = f'{save_path}/{name}/{n}'
            #     if name == 'Depth':
            #         img = img.astype(np.uint16)
            #         # if not os.path.exists(target):
            #         cv2.imwrite(target + ".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 5])
            #     else:
            #         cv2.imwrite(target + ".webp", img, [int(cv2.IMWRITE_WEBP_QUALITY), 100])
            # if name=='Depth':
            #     img2=cv2.imread(target, -1)
            #     print(img.shape,img.min(),img.mean(),img.max(),' - ', img2.shape,img2.min(),img2.mean(),img2.max())
            # time.sleep(1)
            q.task_done()
        if video:
            vw.release()
    except Exception as e:
        import traceback
        print(e)
        print(traceback.format_exc())


def record(src, save_path, rec_video=0, rec_image=0):
    if not rec_video and not rec_image:
        # print('please select record video or image or both')
        return
    from .realsensewrapper import RealSense
    import pyrealsense2 as rs
    pool_size = 100
    os.makedirs(f"{save_path}/", exist_ok=True)
    cam = RealSense(src, debug=1, infrared=1, depth=1)
    # cam=RealSense(r"a.bag",debug=1,infrared=0,depth=1)
    streams = cam.selected_profiles

    qs = {s: JoinableQueue(pool_size) for s in streams}
    prcs = {s: Process(name=s, target=video_recorder, args=(s, qs[s], save_path, streams[s])) for s in streams}
    for p in prcs:
        prcs[p].daemon = True
        if rec_video:
            prcs[p].start()

    import multiprocessing as mp
    pool = mp.Pool(mp.cpu_count() - 1)
    cam.start()
    i = 0
    n = 1
    profiles = {
        s: {
            'intrinsics': streams[s]['intrinsics'],
            'width': streams[s]['width'],
            'height': streams[s]['height'],
            'fps': streams[s]['fps'],
        } for s in streams
    }
    meta = {
        'path': {s: {
            'folder': s,
            'ext': 'webp' if s != 'Depth' else 'png'
        } for s in streams},
        'profiles': profiles,
        'version': 1,
        **cam.get_meta_data(),
    }

    start_time = time.time()
    while i < 20000:
        frames = cam.waitForFrame(colorize=0, postprocess=0, align=1)
        if frames == 'eof':
            break
        if frames == None:
            continue
        i += 1
        n = frames['frame']
        info = {
            'recorded_frame': i,
            'camera_frame': n,
            'current_time': int(time.time() - start_time),
            'fps': int(i / (time.time() - start_time + .000001)),
            'frame_in_q': sum([qs[s].qsize() for s in qs]) + len(pool._cache),
            'frame_loss': max(0, (n - i)) * 100 / max(1, n),
            'size': '...'  #utils.get_pretty_folder_size(save_path)
        }

        if i % 10 == 0:
            # print(
            #     f"{info['current_time']:0.0f}s \tframe={i}/{n} \tqueue={info['frame_in_q']} \tframe_loss={info['frame_loss']:.0f}% size={info['size']}             ",
            #     end='\r')
            pass
        for s in streams:
            if info['frame_in_q'] >= pool_size:
                # cam.dev.pause()
                while (qs[s].qsize() + len(pool._cache) > pool_size / 5):
                    # print(f'qsize={qs[s].qsize()+len(pool._cache)}   ', end='\r')
                    time.sleep(1)
                # cam.dev.resume()
            if streams[s]['format'] == rs.format.rgb8:
                fc = cv2.cvtColor(frames[s], cv2.COLOR_RGB2BGR)
            else:
                fc = frames[s].copy()
            if rec_video:
                qs[s].put((n, fc))
            if rec_image:
                pool.apply_async(image_recorder, args=(s, n, fc, save_path))

    # print('finished')
    cam.stop()
    for s in streams:
        qs[s].put((-1, 'eof'))
    pool.close()
    pool.join()
    for s in streams:
        prcs[s].join()

    # print(f'frames: {i}/{n} time: {int(time.time() - start_time)}s size: {utils.get_pretty_folder_size(save_path)}')

    with open(f'{save_path}/meta.pkl', 'wb') as outfile:
        pickle.dump(meta, outfile)


def record_from_video(color, depth, save_path):

    pool_size = 100
    os.makedirs(f"{save_path}/", exist_ok=True)

    import multiprocessing as mp
    pool = mp.Pool(mp.cpu_count() - 1)
    i = 0
    cap_color = cv2.VideoCapture(color)
    cap_depth = cv2.VideoCapture(depth)

    profiles = {
        'Color': {
            'intrinsics': [],
            'width': 1920,
            'height': 1080,
            'fps': 30,
        },
        'Depth': {
            'intrinsics': [],
            'width': 1920,
            'height': 1080,
            'fps': 30,
        }
    }
    meta = {
        'path': {s: {
            'folder': s,
            'ext': 'webp' if s != 'Depth' else 'png'
        } for s in profiles},
        'profiles': profiles,
        'version': 1,
    }

    start_time = time.time()
    while i < 10000:
        i += 1
        color_ret, color_frame = cap_color.read()
        depth_ret, depth_frame = cap_depth.read()

        if color_ret:
            pool.apply_async(image_recorder, args=("Color", i, color_frame, save_path))
        if depth_ret:
            pool.apply_async(image_recorder, args=("Depth", i, depth_frame, save_path))

    # print('finished')

    pool.close()
    pool.join()

    with open(f'{save_path}/meta.pkl', 'wb') as outfile:
        pickle.dump(meta, outfile)


if __name__ == "__main__":
    try:
        record(sys.argv[1], sys.argv[2], rec_image=1, rec_video=1)
    except KeyboardInterrupt:
        pass
