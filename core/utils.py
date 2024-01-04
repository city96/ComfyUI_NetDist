import time
import random

# set global ID once for entire session
try: GID
except NameError:
	GID = ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
	print(f"NetDist: Set session ID to '{GID}'")

def get_client_id():
	global GID
	return(f"netdist-{GID}")

def get_new_job_id():
	job_id = f"{get_client_id()}-{int(time.time()*1000)}"
	time.sleep(0.1) # prevent ID mismatch, no matter how unlikely
	return job_id

def clean_url(raw, multi=False):
	raw = raw.strip()
	raw = raw.replace(' ', ',').replace('\n', ',').replace('\t', ',')
	urls = [x.rstrip('/') for x in raw.split(',') if x.strip()]
	return urls if multi else urls[0]
