import pyrealsense2 as rs
import os
from . import utils
import numpy as np


class RealSense:

    def __init__(self, src, debug=0, infrared=0, depth=0, save_to_file=None):
        self.debug = debug
        self.src = src
        self.infrared = infrared
        self.depth = depth
        self.save_to_file = save_to_file
        self.current_frame = 0
        self.is_file = False
        self.connect()

    def connect(self):
        ctx = rs.context()

        debug = self.debug
        src = self.src

        if debug:
            # print('Connecting to ' + src)
            pass
        if (src == 'webcam'):
            import cv2
            self.cam = cv2.VideoCapture(0)
            # self.cam=cv2.VideoCapture("C:/data-ar/kmoulouel/walking/06-04-2022-16-23-07/cam2/Color.mp4")
            _, f = self.cam.read()
            w = f.shape[1]
            h = f.shape[0]

            self.selected_profiles = {'Color': {'width': w, 'height': h, 'fps': 30, 'format': 0, 'res': w * h, 'type': 'Color', 'is_color': True}}
            # print(self.selected_profiles)
            return
        elif (src == 'usb'):
            if debug:
                print(list(ctx.query_devices()))
            self.dev = ctx.query_devices()[0]
        elif (os.path.isfile(src)):
            self.is_file = True
            if debug:
                # print(f"reading bag file {src}")
                pass
            self.dev = ctx.load_device(src)

        else:
            import pyrealsense_net as rsnet
            self.dev = rsnet.net_device(src)
            self.dev.add_to(ctx)

        self.selected_profiles = self.find_profiles(self.dev)
        if debug:
            # print('Connected')
            pass
        if debug:
            # print('Using device 0,', self.dev.get_info(rs.camera_info.name), ' Serial number: ', self.dev.get_info(rs.camera_info.serial_number))
            pass
        if debug:
            # print(f'selected profiles: {self.selected_profiles}')
            pass

    def start(self):
        if self.src == "webcam":
            return
        ctx = rs.context()

        self.pipeline = rs.pipeline(ctx)
        config = rs.config()
        if self.is_file:
            rs.config.enable_device_from_file(config, self.src, repeat_playback=False)

        color_profile = self.selected_profiles['Color']
        if self.depth:
            depth_profile = self.selected_profiles['Depth']

        config.enable_stream(rs.stream.color, color_profile['width'], color_profile['height'], color_profile['format'], color_profile['fps'])

        if self.depth:
            config.enable_stream(rs.stream.depth, depth_profile['width'], depth_profile['height'], depth_profile['format'], depth_profile['fps'])
        if self.infrared:
            for i in [1, 2]:
                infrared_profile1 = self.selected_profiles.get(f'Infrared{i}', None)
                if infrared_profile1 != None:
                    config.enable_stream(rs.stream.infrared, i, infrared_profile1['width'], infrared_profile1['height'], infrared_profile1['format'],
                                         infrared_profile1['fps'])

        if self.save_to_file:
            config.enable_record_to_file(self.save_to_file)

        # self.queue = rs.frame_queue(300, keep_frames=True)
        # self.profile= self.pipeline.start(config,self.queue)
        self.profile = self.pipeline.start(config)
        sensor_color = self.profile.get_device().first_color_sensor()
        sensor_depth = self.profile.get_device().first_depth_sensor()
        self.align = rs.align(rs.stream.color)
        if self.is_file:
            self.dev = self.profile.get_device().as_playback()
            self.dev.set_real_time(False)  #Needed so frames don't get dropped during processing:
            # self.dev.resume()
        try:
            sensor_color.set_option(rs.option.enable_auto_exposure, 0)
            sensor_depth.set_option(rs.option.enable_auto_exposure, 0)
            sensor_color.set_option(rs.option.enable_auto_white_balance, 0)
            sensor_color.set_option(rs.option.exposure, 312)
            sensor_depth.set_option(rs.option.exposure, 8000)
            sensor_depth.set_option(rs.option.laser_power, 360)

        except Exception as e:
            # print(e)
            # raise e
            pass
        # sensor_depth.set_option(rs.option.enable_auto_white_balance, 0)
        self.colorizer = rs.colorizer()
        holefilter = rs.temporal_filter()
        holefilter.set_option(rs.option.holes_fill, 1)
        self.filters = [
            # rs.decimation_filter (),
            rs.spatial_filter(),
            rs.temporal_filter(),
            holefilter
        ]

    def get_meta_data(self):
        return {'depth_scale': self.profile.get_device().first_depth_sensor().get_depth_scale()}

    def waitForFrame(self, colorize=True, postprocess=False, align=0):
        if self.src == 'webcam':
            _, c = self.cam.read()
            return {'Color': c, 'frame': 1}

        try:
            if self.is_file:
                # self.dev.resume()
                # success,frames = self.queue.try_wait_for_frame(5000)
                success, frames = self.pipeline.try_wait_for_frames(5000)
                if not success:  # or self.current_frame-50>frames.get_frame_number():
                    return 'eof'
                # frames=frames.as_frameset() #for queue
                # self.dev.pause()
            else:
                # frames = self.queue.wait_for_frame(100).as_frameset()
                frames = self.pipeline.wait_for_frames(100)
        except:
            return
        self.current_frame = frames.get_frame_number()
        if align:
            frames = self.align.process(frames)

        # print(f"{frames}")
        if self.depth:
            depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if self.infrared:
            infrared_frame = {i: frames.get_infrared_frame(i) for i in [1, 2]}

        if self.depth and not depth_frame:
            if self.debug:
                # print(f'error depth {depth_frame} frame not received')
                pass
        if not color_frame:
            if self.debug:
                # print(f'error color {color_frame} frame not received')
                pass
            return

        if self.depth:
            if postprocess:
                # print(np.asanyarray(depth_frame.get_data()).shape, end=' > ')
                depth_frame = self.post_processing_depth(depth_frame)
                # print(np.asanyarray(depth_frame.get_data()).shape)
            if colorize:
                depth_color_frame = self.colorizer.colorize(depth_frame)
            else:
                depth_color_frame = depth_frame

        res = {}
        if self.depth:
            res['Depth'] = np.asanyarray(depth_color_frame.get_data())
            # print(res['Depth'].shape)

        res['Color'] = np.asanyarray(color_frame.get_data())
        if self.infrared:
            for i in [1, 2]:
                infrared_profile1 = self.selected_profiles.get(f'Infrared{i}', None)
                if not (infrared_profile1 is None):
                    res[f'Infrared{i}'] = np.asanyarray(infrared_frame[i].get_data())

        res['frame'] = frames.get_frame_number()

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        return res

    def post_processing_depth(self, input):
        processed = input
        for f in self.filters:
            processed = f.process(processed)

        return processed

    def stop(self):
        if self.src == 'webcam':
            self.cam.release()
        else:
            self.pipeline.stop()
        # rs.context().close();

    def find_profiles(self, dev=None, pipeline=None):
        if pipeline is None:
            raw_profiles = [p.as_video_stream_profile() for s in dev.query_sensors() for p in s.get_stream_profiles()]
        else:
            raw_profiles = [p.as_video_stream_profile() for p in pipeline.get_active_profile().get_streams()]
        all_profiles = []

        for p in raw_profiles:
            prof = {
                'width': p.width(),
                'height': p.height(),
                'fps': p.fps(),
                'format': p.format(),
                'res': p.height() * p.width(),
                'type': p.stream_name(),
                'is_color': 'Infrared' not in p.stream_name(),
            }
            try:
                intrinsics = utils.intrinsics_to_obj(p.intrinsics)
                prof['intrinsics'] = intrinsics
            except:
                pass
            all_profiles.append(prof)

        # if debug: print(f"available profiles: ${self.info_profiles}")

        res = {}
        res['Color'] = self.get_best_profile(all_profiles, 'Color')
        dep_p = None
        if self.depth:
            res['Depth'] = self.get_best_profile(all_profiles, 'Depth')
            dep_p = res['Depth']
        if self.infrared:
            for i in [1, 2]:
                pi = self.get_best_profile(all_profiles, f'Infrared {i}', dep_p)
                if pi != None:
                    res[f'Infrared{i}'] = pi

        # if self.debug:print(res)
        return res

    def get_best_profile(self, all_profiles, typ, match_profile=None):
        best = None
        for p in all_profiles:
            if not (typ in p['type']):
                continue

            if match_profile != None and (p['width'] != match_profile['width'] or p['height'] != match_profile['height']):
                continue
            if best == None:
                best = p
            if best['res'] < p['res'] or best['res'] == p['res'] and best['fps'] < p['fps']:
                best = p
            if best['res'] == p['res'] and best['fps'] == p['fps'] and p['format'] == rs.format.bgr8:
                best = p

        return best