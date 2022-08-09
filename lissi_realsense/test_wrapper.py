from .realsensewrapper import RealSense
import cv2
import sys
try:
	# cam=RealSense(r"C:\D\Projects\lissi\lissi-realsense\test\a.bag",debug=1,infrared=0,depth=1)
	# cam=RealSense("usb",debug=1,infrared=1,depth=1,save_to_file='a.bag')
	cam=RealSense(sys.argv[1],debug=1,infrared=0,depth=1)
	# cam=RealSense(r"a.bag",debug=1,infrared=0,depth=1)
	cam.start()
	count=0
	

	while count<200:
		frames=cam.waitForFrame()
		if frames=='eof':break
		if frames==None:continue
		count+=1
		n=frames['frame']
		cv2.imshow("usb", cv2.resize(frames['Color'],(800,600)))
		print(f'{count}/{n}',end='\r')
		if cv2.waitKey(25) & 0xFF == ord('q'):
			break


	cam.stop()
	print(f'frames: {count}/{n}')
	cv2.destroyAllWindows() 

except KeyboardInterrupt:pass