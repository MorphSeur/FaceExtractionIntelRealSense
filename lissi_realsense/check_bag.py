import os,sys,time,utils
from .realsensewrapper import RealSense

comname=os.environ['COMPUTERNAME']
	
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
		# print(comname,f"{info['current_time']:0.0f}s \tframe={i}/{n} \tframe_loss={info['frame_loss']:.0f}% 			 ",end='\r')
	cam.stop()
	# print()
	return info



if __name__ == "__main__":
	file=sys.argv[1]

	# print('\n\n',comname,'checking bag file.........................')
	check_bag(file)
