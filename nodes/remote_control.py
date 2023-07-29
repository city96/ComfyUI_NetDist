import time
import json
import torch
import random
import requests
import numpy as np
from PIL import Image
from copy import deepcopy

def img_to_torch(img):
	image = img.convert("RGB")
	image = np.array(image).astype(np.float32) / 255.0
	image = torch.from_numpy(image)[None,]
	return image

class FetchRemote():
	def __init__(self):
		pass
	
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"final_image": ("IMAGE",),
				"remote_info": ("REMOTE",),
			},
		}

	RETURN_TYPES = ("IMAGE",)
	FUNCTION = "get_remote_job"
	CATEGORY = "remote"

	def wait_for_job(self,remote_url,job_id):
		url = remote_url + "history"
		
		image_data = None
		while not image_data:
			r = requests.get(url)
			r.raise_for_status()
			data = r.json()
			if not data:
				time.sleep(0.5)
				continue
			for i,d in data.items():
				if d["prompt"][3].get("job_id") == job_id:
					image_data = d["outputs"][list(d["outputs"].keys())[-1]].get("images")
			time.sleep(0.5)
		return image_data

	# remote_info can be none, but the node shouldn't exist at that point
	def get_remote_job(self, final_image, remote_info):
		images = []
		for i in self.wait_for_job(remote_info["remote_url"],remote_info["job_id"]):
			img_url = f"{remote_info['remote_url']}view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}"

			ir = requests.get(img_url, stream=True)
			ir.raise_for_status()
			img = Image.open(ir.raw)
			images.append(img_to_torch(img))

		if len(images) == 0:
			img = Image.new(mode="RGB", size=(768, 768))
			images.append(img_to_torch(img))

		out = images[0]
		for i in images[1:]:
			out = torch.cat((out,i))

		return (out,)

class QueueRemote:
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_url": ("STRING", {
					"multiline": False,
					"default": "http://127.0.0.1:8188/",
				}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
				"batch_override": ("INT", {"default": 0, "min": 0, "max": 8}),
				"system": (["windows", "posix"],),
				"enabled": (["true", "false", "remote"],{"default": "true"}),
				"node_id": ("INT", {"default": 1, "min": 1, "max": 64}),
			},
			"hidden": {
				"prompt": "PROMPT",
			},
		}
	
	RETURN_TYPES = ("INT","REMOTE")
	RETURN_NAMES = ("seed+batch","remote_info")
	FUNCTION = "queue_on_remote"
	CATEGORY = "remote"
	
	def queue_on_remote(self, remote_url, seed, batch_override, system, enabled, node_id, prompt):
		def get_max_batch_size(prompt):
			bs = 1
			for node in prompt.keys():
				if prompt[node]["class_type"] == "EmptyLatentImage":
					for k,v in prompt[node]["inputs"].items():
						if k == "batch_size":
							if batch_override > 0:
								bs = batch_override
								prompt[node]["inputs"]["batch_size"] = batch_override
							else:
								bs = max(bs,int(v))
			return bs

		if enabled == "false":
			return (seed,{"remote_url":None,"job_id":None,})
		elif enabled == "remote":
			return (seed+node_id*get_max_batch_size(prompt),{"remote_url":None,"job_id":None,})

		new_prompt = deepcopy(prompt)
		to_del = []
		def recursive_node_deletion(start_node):
			target_nodes = [start_node]
			if start_node not in to_del:
				to_del.append(start_node)
			while len(target_nodes) > 0:
				new_targets = []
				for target in target_nodes:
					for node in new_prompt.keys():
						inputs = new_prompt[node].get("inputs")
						if not inputs:
							continue
						for i in inputs.values():
							if type(i) == list:
								if len(i) > 0 and i[0] in to_del:
									if node not in to_del:
										to_del.append(node)
										new_targets.append(node)
				target_nodes += new_targets
				target_nodes.remove(target)
		
		output_src = None
		for i in new_prompt.keys():
			if new_prompt[i]["class_type"] == "QueueRemote":
				if new_prompt[i]["inputs"]["remote_url"] == remote_url:
					new_prompt[i]["inputs"]["enabled"] = "remote"
					output_src = i
				else:
					new_prompt[i]["inputs"]["enabled"] = "false"
		
		output = None
		for i in new_prompt.keys():
			# only leave current fetch but replace with PreviewImage
			if new_prompt[i]["class_type"] == "FetchRemote":
				if new_prompt[i]["inputs"]["remote_info"][0] == output_src:
					output = {
							'inputs': {'images': new_prompt[i]["inputs"]["final_image"]},
							'class_type': 'PreviewImage',
					}
				recursive_node_deletion(i)
			# do not save output on remote
			if new_prompt[i]["class_type"] in ["SaveImage","PreviewImage"]:
				recursive_node_deletion(i)
		new_prompt[str(max([int(x) for x in new_prompt.keys()])+1)] = output

		if system == "posix":
			for i in new_prompt.keys():
				if new_prompt[i]["class_type"] == "LoraLoader":
					new_prompt[i]["inputs"]["lora_name"] = new_prompt[i]["inputs"]["lora_name"].replace("\\","/")
				if new_prompt[i]["class_type"] == "VAELoader":
					new_prompt[i]["inputs"]["vae_name"] = new_prompt[i]["inputs"]["vae_name"].replace("\\","/")
				if new_prompt[i]["class_type"] in ["CheckpointLoader","CheckpointLoaderSimple"]:
					new_prompt[i]["inputs"]["ckpt_name"] = new_prompt[i]["inputs"]["ckpt_name"].replace("\\","/")
		for i in to_del:
			del new_prompt[i]

		job_id = f"netdist-{time.time()}"
		data = {
			"prompt": new_prompt,
			"client_id": "netdist",
			"extra_data": {
				"job_id": job_id,
			}
		}
		ar = requests.post(remote_url+"prompt", json=data)
		ar.raise_for_status()
		return (seed,{"remote_url":remote_url,"job_id":job_id})
