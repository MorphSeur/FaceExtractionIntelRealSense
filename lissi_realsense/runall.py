
cams={
# 'cam3':'10.12.20.211',
# 'cam2':'127.0.0.1',
#  'cam4':'10.12.20.76',
#  'cam1':'10.12.20.102',
# 'cam1':'192.168.137.34',
'cam1':'192.168.1.101',#'10.12.20.68',
'cam2':'192.168.1.100',#'10.12.20.185',
 'cam3':'192.168.1.103',#'10.12.20.194',
 'cam4':'192.168.1.104'#'10.12.20.193',
}

import os
from datetime import datetime
dt_string = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
import sys









def remote_call(cam,path, timeout=3):
	import requests
	try:
		r = requests.get(url = f"http://{cams[cam]}:8080/{path}",timeout=timeout)
		return r.content
		# print(f'{cam}-{r.content}')
	except Exception as e:
		# print(f'{cam}-{e}')
		return e
	# return f'{cam}-{r}'


import multiprocessing
def parallelRunner(parallel, runner, items):
    if parallel:
        from multiprocessing.pool import ThreadPool

        pool = ThreadPool(min(8,len(items)))
        result = pool.imap(runner, items)
        try:
            for item in items:
                res = result.next()
                yield item, res
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()
            pool.close()
            raise
    else:
        for item in items:
            res = runner(item)
            yield item,res

def printRemoteStatus():
	import time
	try:
		while 1:
			
			for i,(cam,p) in enumerate(parallelRunner(1,lambda cam:remote_call(cam,"status"),cams.keys())):
				if i==0:os.system('cls')
				print(f'{cam}-{p}\n')
			time.sleep(1)
	except KeyboardInterrupt:
		pass


if __name__ == "__main__":
	if len(sys.argv)==1:
		print(f'usage: \n{sys.argv[0]} start user act prefix_path\n{sys.argv[0]} stop')
		sys.exit(3)

	from multiprocessing import Process, freeze_support
	freeze_support()
	if sys.argv[1]=="start":
		user=sys.argv[2]
		act=sys.argv[3]
		prefix_path=sys.argv[4]
		path=f'start?path={prefix_path}/{user}/{act}/{dt_string}/'
		for cam,p in parallelRunner(1,lambda cam:remote_call(cam,path+cam),cams.keys()):
			print(f'{cam}-{p}')
		# os.system('start python.exe runall.py status')

	if sys.argv[1]=="stop":
		for cam,p in parallelRunner(1,lambda cam:remote_call(cam,"stop",60),cams.keys()):
			print(f'{cam}-{p}')

	if sys.argv[1]=="status":
		printRemoteStatus()

	if sys.argv[1]=="ping":
		for cam,p in parallelRunner(1,lambda cam:remote_call(cam,"ping"),cams.keys()):
			print(f'{cam}-{p}')

	if sys.argv[1]=='image':
		[print(f'http://{cams[cam]}:8080/image') for cam in cams]
	if sys.argv[1]=="update":
		for cam,p in parallelRunner(1,lambda cam:remote_call(cam,"update"),cams.keys()):
			print(f'{cam}-{p}')

	if sys.argv[1]=="command":
		cmd=' '.join(sys.argv[2:])
		for cam,p in parallelRunner(1,lambda cam:remote_call(cam,f"command?{cmd}"),cams.keys()):
			print(f'{cam}-{p}')

	