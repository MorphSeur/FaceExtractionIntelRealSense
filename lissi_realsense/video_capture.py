import psutil
import sys
import time, threading
from multiprocessing import Process, JoinableQueue
import os
from urllib.parse import urlparse
print('starting...')
from .realsensewrapper import RealSense
loc = {}
import cv2
# from video_capture import VideoCapture
from . import utils
only_bag_file=1#False
class VideoCapture:
	def __init__(self,save_path,only_bag_file):
		self.only_bag_file=only_bag_file
		self.save_path=save_path
		import  shutil
		if os.path.exists(save_path):shutil.rmtree(save_path)
		os.makedirs(save_path,exist_ok=True)		
		# cam=RealSense("usb",debug=1,infrared=0,depth=1)
		save_to_file=f'{save_path}/a.bag' if only_bag_file else None
		self.cam=RealSense("usb",debug=1,infrared=0,depth=1,save_to_file=save_to_file)
		# self.cam.connect()
		self.streams=self.cam.selected_profiles
		
		# prcs={s: Process(target=video_recorder, args=(None,None,None,None)) for s in streams}
		self.info={}
	
	
	def start(self):
		self.qs={s:JoinableQueue(1000) for s in self.streams}
		
		self.prcs={s: Process(name=s,target=video_recorder, args=(s,self.qs[s],self.save_path,self.streams[s])) for s in self.streams}
		for p in self.prcs:
			self.prcs[p].daemon=True
			if not self.only_bag_file:
				self.prcs[p].start()
			
		self.working=True
		self.thread = threading.Thread(target=self.worker, name='VideoCapture', args=())
		self.thread.daemon = True
		self.thread.start()
		
		return self

	def stop(self):
		self.working=False
		self.cam.stop()	
		for s in self.streams:self.qs[s].put((-1,'eof')) 
		self.thread.join()
	def kill(self):
		self.cam.stop()	
		for s in self.streams:self.prcs[s].terminate() 

		
	def worker(self):
		print('worker start')
		cam=self.cam;qs=self.qs;prcs=self.prcs;streams=self.cam.selected_profiles
		i=0
		import time
		self.cam.start()
		start_time = time.time()
		while self.working:
			if self.only_bag_file:
				time.sleep(1)
				i+=1
				self.info={
					'current_time':int(time.time() - start_time),
					'size':utils.get_pretty_folder_size(self.save_path)
				}
				if i%30==0 or i<10: print(self.info,end='\r')
				continue
			frames = cam.waitForFrame(colorize=False)
			
			if frames is None:
				time.sleep(0.1)
				continue
			i+=1
			n=frames['frame']
			self.info={
				'recorded_frame':i,
				'camera_frame':n,
				'current_time':int(time.time() - start_time),
				'fps':int(i/(time.time() - start_time)),
				'frame_in_q':sum([qs[s].qsize() for s in qs]),
				'frame_loss':max(0,(n-i))*100/max(1,n),
				'size':utils.get_pretty_folder_size(self.save_path)
			}
			
			if i%30==0 or i<10:
				print(f"{self.info['current_time']:0.0f}s \tframe={n} \tqueue={self.info['frame_in_q']} \tframe_loss={self.info['frame_loss']:.0f}% size={self.info['size']}",end='\r')
			for s in streams:
				qs[s].put((n,frames[s]))	
		
		# for s in streams: qs[s].join()
		if not self.only_bag_file:
			for s in streams:prcs[s].join()




def video_recorder(name,q,save_path,profile):
	print('video_recorder start')
	if profile['type']=='Color':psutil.Process().cpu_affinity([2,3])
	if profile['type']=='Depth':psutil.Process().cpu_affinity([4,5])
	if 'Infrared' in profile['type']: psutil.Process().cpu_affinity([6,7])

	print(f'start recording {name} in cpu={psutil.Process().cpu_affinity()}')
	import numpy as np
	# codec = cv2.VideoWriter.fourcc(*'avc1')
	# codec = cv2.VideoWriter.fourcc(*'MJPG')
	codec = cv2.VideoWriter.fourcc(*'DIVX')
	
	vw=cv2.VideoWriter(f'{save_path}/{name}.avi',codec, profile['fps'], (profile['width'], profile['height']),profile['is_color'])
	# vw.write(np.zeros(profile['width'], profile['height'],3))
	while True:
	
		n,img = q.get()
		
		if n==-1:
			q.task_done()
			break
		# cv2.imshow(name,img)
		# if name=='Depth':
		# 	img = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)
		vw.write(img)
		q.task_done()
		
	vw.release()


if __name__ == "__main__":
	save_path=sys.argv[1]
	
