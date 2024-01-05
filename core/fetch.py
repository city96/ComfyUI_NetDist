import time
import json
import torch
import requests
import numpy as np
from PIL import Image

POLLING = 0.5

def get_job_output(inputs, outputs):
	output_id = list(outputs.keys())[-1] # fallback to last
	for i,d in inputs.items():
		if d.get("final_output") and i in outputs.keys():
			output_id = i
			break
	return outputs[output_id].get("images", [])

def wait_for_job(remote_url, job_id):
	fail = 0
	while fail <= 3:
		r = requests.get(f"{remote_url}/history", timeout=4)
		try:
			r.raise_for_status()
		except Exception as e:
			print("NetDist caught error while fetching output image:\n", e)
			fail += 1
			continue
		data = r.json()
		if not data:
			time.sleep(POLLING)
			continue
		for i,d in data.items():
			if d["prompt"][3].get("job_id") == job_id:
				# this needs to be less jank
				if len(d["outputs"].keys()) > 0:
					return get_job_output(d["prompt"][2], d["outputs"])
				else:
					return []
		# todo: check if it's actually in the queue to avoid waiting forever
		time.sleep(POLLING)
	raise OSError("Failed to fetch image from remote client!")

def fetch_from_remote(remote_url, job_id):
	def img_to_torch(img):
		image = img.convert("RGB")
		image = np.array(image).astype(np.float32) / 255.0
		image = torch.from_numpy(image)[None,]
		return image

	if not remote_url or not job_id:
		return None

	images = []
	for i in wait_for_job(remote_url, job_id):
		img_url = f"{remote_url}/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}"

		ir = requests.get(img_url, stream=True, timeout=16)
		ir.raise_for_status()
		img = Image.open(ir.raw)
		images.append(img_to_torch(img))

	if len(images) == 0:
		return None

	out = images[0]
	for i in images[1:]:
		out = torch.cat((out,i))
	return out
