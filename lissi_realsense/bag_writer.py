import os,sys,time,utils
from realsensewrapper import RealSense

comname=os.environ['COMPUTERNAME']
def save_to_bag(file):
	
	
	cam=RealSense("usb",debug=1,infrared=0,depth=1,save_to_file=file)
	streams=cam.selected_profiles
	start_time = time.time()
	cam.start()
	i=0
	
	try:
		while 1:
			time.sleep(1)
			i+=1
			if i%30==0 or i<10: 
				info={
					'current_time':int(time.time() - start_time),
					'size':utils.get_pretty_folder_size(file)
				}
				print(comname,info,end='\r')
	except KeyboardInterrupt:
		cam.stop()
		info={
			'current_time':int(time.time() - start_time),
			'size':utils.get_pretty_folder_size(file)
		}
		print(comname,info)

		#for fixing the bug of not closing file
		# cam=RealSense("usb",debug=0,infrared=0,depth=0,save_to_file='NUL')
		# cam.start()
		# cam.stop()
		

	
def check_bag(src):
	cam = RealSense(src, debug=0, infrared=0, depth=1)
	cam.start()
	start_time = time.time()
	i=0
	while i < 10000:
		frames = cam.waitForFrame(colorize=0, postprocess=0, align=0)
		# print(frames)
		if frames == 'eof': break
		if frames == None: continue
		i += 1
		n = frames['frame']

		
		info = {
		'recorded_frame': i,
		'camera_frame': n,
		'current_time': int(time.time() - start_time),
		'fps': int(i / (time.time() - start_time + .000001)),
		'frame_loss': max(0, (n - i)) * 100 / max(1, n),
		}
		print(comname,f"{info['current_time']:0.0f}s \tframe={i}/{n} \tframe_loss={info['frame_loss']:.0f}% 			 ",end='\r')
	cam.stop()
	print()



if __name__ == "__main__":
	save_path=sys.argv[1]
	import  shutil
	if os.path.exists(save_path):shutil.rmtree(save_path)
	os.makedirs(save_path,exist_ok=True)		
	save_to_file=f'{save_path}/a.bag'

	save_to_bag(save_to_file)
	print('\n\n',comname,'checking bag file.........................')
	check_bag(save_to_file)
