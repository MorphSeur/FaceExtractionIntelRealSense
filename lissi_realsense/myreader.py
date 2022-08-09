import pickle
import pyrealsense2 as rs
import os
import cv2
import json
import math
from . import utils
import os


class MyReader:

    def __init__(self, root_path):
        if not os.path.exists(f'{root_path}/meta.pkl'):
            from . import convert
            # print('file is not prepared... converting....')
            if os.path.exists(f'{root_path}/a.bag'):
                convert.record(f'{root_path}/a.bag', root_path, rec_image=1, rec_video=1)
            else:
                # print('Warning! no bag files find.... all functionalities may not work! trying other sources')

                if os.path.exists(f'{root_path}/Color.mp4'):
                    color = f'{root_path}/Color.mp4'
                    depth = f'{root_path}/Depth.mp4'
                if os.path.exists(f'{root_path}/Color.avi'):
                    color = f'{root_path}/Color.avi'
                    depth = f'{root_path}/Depth.avi'
                convert.record_from_video(color, depth, root_path)

        with open(f'{root_path}/meta.pkl', 'rb') as f:
            self.meta = pickle.load(f)
        self.root_path = root_path
        # self.path_info = f'{root_path}/{self.meta["path"]}'
        self.intrinsics = utils.intrinsics_from_obj(self.meta['profiles']['Color']['intrinsics'])
        self.max_frame = max([int(d.split('.')[0]) for d in os.listdir(f'{self.root_path}/{self.meta["path"]["Color"]["folder"]}')])
        start_frame = min([int(d.split('.')[0]) for d in os.listdir(f'{self.root_path}/{self.meta["path"]["Color"]["folder"]}')])
        self.seek(start_frame)

    def _get_frames_path(self, frame_id):
        paths = {}
        for s in self.meta['profiles']:
            p = self.meta['path'][s]
            path = f'{self.root_path}/{p["folder"]}/{frame_id}.{p["ext"]}'
            paths[s] = path if os.path.exists(path) else None

        return paths

    def eof(self):
        return self.framen > self.max_frame

    def is_valid(self, frame_types=['Color', 'Depth']):
        for t in frame_types:
            if self.current[t] is None:
                return False
        return True

    def seek(self, frame):
        self.framen = frame
        # self.current_depth = None
        self.current = self._read_frame(self.framen)

    def _read_frame(self, frame_id):
        paths = self._get_frames_path(frame_id)
        return {s: cv2.imread(paths[s], -1) if paths[s] else None for s in paths}

    def next(self):
        self.seek(self.framen + 1)
        while not self.eof() and not self.is_valid(['Color', 'Depth']):
            # print(f'missing frame={self.current_frame}',end='\r')
            self.seek(self.framen + 1)

        # if self.eof():

        #     self.current_color = None
        #     self.current_depth = None
        #     # return False

        return self.current if not self.eof() else False

    def get_depth_frame(self):
        return self.current.get('Depth', None)

    def get_color_frame(self):
        return self.current.get('Color', None)

    def get_infrared_frame(self, i):
        return self.current.get(f'Infrared{i}', None)

    def get_colorized_depth(self):
        absdepth = cv2.convertScaleAbs(self.get_depth_frame(), alpha=0.025)
        return cv2.applyColorMap(absdepth, cv2.COLORMAP_JET)

    def measure_depth(self, x, y):
        return self.get_depth_frame()[y][x] * self.meta['depth_scale']

    def to_3d_point(self, x, y):
        d = self.measure_depth(x, y)
        return rs.rs2_deproject_pixel_to_point(self.intrinsics, [x, y], d)

    def measure_distance(self, x1, y1, x2, y2):
        point1 = self.to_3d_point(x1, y1)
        point2 = self.to_3d_point(x2, y2)

        return math.sqrt(math.pow(point1[0] - point2[0], 2) + math.pow(point1[1] - point2[1], 2) + math.pow(point1[2] - point2[2], 2))

    def to_point_cloud(self):
        pc = rs.pointcloud()
        pc.map_to(self.get_color_frame())
        return pc.calculate(self.get_depth_frame())
