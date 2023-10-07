import os
import time
import json
import torch
import random
import requests
import numpy as np
from PIL import Image
from copy import deepcopy


# set global ID once for entire session
try: GID
except NameError:
	GID = ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
	print(f"NetDist: Set session ID to '{GID}'")
def get_client_id():
	global GID
	return(f"netdist-{GID}")


class FetchRemote():
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"final_image": ("IMAGE",),
				"remote_info": ("REMINFO",),
			},
		}

	RETURN_TYPES = ("IMAGE",)
	FUNCTION = "get_remote_job"
	CATEGORY = "remote"
	TITLE = "Fetch from remote"

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
		def img_to_torch(img):
			image = img.convert("RGB")
			image = np.array(image).astype(np.float32) / 255.0
			image = torch.from_numpy(image)[None,]
			return image

		if not remote_info["remote_url"] or not remote_info["job_id"]:
			return (torch.empty(0,0,0,0),)

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


class QueueRemoteChainStart:
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": (["current"],),
				"trigger": (["on_change", "always"],),
				"batch": ("INT", {"default": 1, "min": 1, "max": 8}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
			},
			"hidden": {
				"prompt": "PROMPT",
			},
		}

	RETURN_TYPES = ("REMCHAIN",)
	RETURN_NAMES = ("remote_chain_start",)
	FUNCTION = "chain_start"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (start of chain)"

	def chain_start(self, workflow, trigger, batch, seed, prompt):
		remote_chain = {
			"seed": seed+batch,
			"batch": batch,
			"prompt": prompt,
			"current_seed": seed+batch,
			"current_batch": batch,
			"job_id": f"{get_client_id()}-{int(time.time()*1000*1000)}"
		}
		return(remote_chain,)

	@classmethod
	def IS_CHANGED(self, workflow, trigger, batch, seed, prompt):
		# don't trigger on workflow change, only input change
		uuid = f"W:{workflow},B:{batch},S:{seed}"
		return uuid if trigger == "on_change" else str(time.time())


class QueueRemoteChainEnd:
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_chain_end": ("REMCHAIN",)
			}
		}

	RETURN_TYPES = ("INT", "INT")
	RETURN_NAMES = ("seed", "batch")
	FUNCTION = "chain_end"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (end of chain)"

	def chain_end(self, remote_chain_end):
		seed = remote_chain_end["current_seed"]
		batch = remote_chain_end["current_batch"]
		return(seed,batch)

	# @classmethod
	# def IS_CHANGED(self, remote_chain_end):
		# uid = f"S:{remote_chain_end['seed']}-B:{remote_chain_end['batch']}"
		# return uid


class QueueRemote:
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_chain": ("REMCHAIN",),
				"remote_url": ("STRING", {
					"multiline": False,
					"default": "http://127.0.0.1:8288/",
				}),
				"batch_override": ("INT", {"default": 0, "min": 0, "max": 8}),
				"enabled": (["true", "false", "remote"],{"default": "true"}),
			}
		}

	RETURN_TYPES = ("REMCHAIN", "REMINFO")
	RETURN_NAMES = ("remote_chain", "remote_info")
	FUNCTION = "queue_on_remote"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (worker)"

	def queue_on_remote(self, remote_chain, remote_url, batch_override, enabled):
		batch = batch_override if batch_override > 0 else remote_chain["batch"]
		remote_chain["seed"] += batch
		remote_info = { # empty
			"remote_url": None,
			"job_id": None,
		}

		if enabled == "false":
			return(remote_chain, remote_info)
		elif enabled == "remote":
			remote_chain["current_seed"] = remote_chain["seed"] # hasn't run yet
			remote_chain["current_batch"] = batch
			# print(remote_chain)
			return(remote_chain, remote_info) #
		else:
			remote_info["remote_url"] = remote_url
			remote_info["job_id"] = remote_chain["job_id"]

		### PROMPT LOGIC ###
		prompt = deepcopy(remote_chain["prompt"])
		to_del = []
		def recursive_node_deletion(start_node):
			target_nodes = [start_node]
			if start_node not in to_del:
				to_del.append(start_node)
			while len(target_nodes) > 0:
				new_targets = []
				for target in target_nodes:
					for node in prompt.keys():
						inputs = prompt[node].get("inputs")
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

		# find current node and disable all others
		output_src = None
		for i in prompt.keys():
			if prompt[i]["class_type"] in ["QueueRemote", "QueueRemoteSingle"]:
				if prompt[i]["inputs"]["remote_url"] == remote_url:
					prompt[i]["inputs"]["enabled"] = "remote"
					output_src = i
				else:
					prompt[i]["inputs"]["enabled"] = "false"

		output = None
		for i in prompt.keys():
			# only leave current fetch but replace with PreviewImage
			if prompt[i]["class_type"] == "FetchRemote":
				if prompt[i]["inputs"]["remote_info"][0] == output_src:
					output = {
							'inputs': {'images': prompt[i]["inputs"]["final_image"]},
							'class_type': 'PreviewImage',
					}
				recursive_node_deletion(i)
			# do not save output on remote
			if prompt[i]["class_type"] in ["SaveImage","PreviewImage"]:
				recursive_node_deletion(i)
		prompt[str(max([int(x) for x in prompt.keys()])+1)] = output
		for i in to_del: del prompt[i]

		### OS LOGIC ###
		def get_remote_os(remote_url):
			url = remote_url + "system_stats"
			r = requests.get(url)
			r.raise_for_status()
			data = r.json()
			return data["system"]["os"]

		sep_remote = "\\" if get_remote_os(remote_url) == "nt" else "/"
		sep_local = "\\" if os.name == "nt" else "/"
		sem_input_map = { # class type : input to replace
			"CheckpointLoaderSimple" : "ckpt_name",
			"CheckpointLoader"       : "ckpt_name",
			"LoraLoader"             : "lora_name",
			"VAELoader"              : "vae_name",
		}
		if sep_remote != sep_local:
			for i in prompt.keys():
				if prompt[i]["class_type"] in sem_input_map.keys():
					key = sem_input_map[prompt[i]["class_type"]]
					prompt[i]["inputs"][key] = prompt[i]["inputs"][key].replace(sep_local, sep_remote)

		### REQ ###
		data = {
			"prompt": prompt,
			"client_id": get_client_id(),
			"extra_data": {
				"job_id": remote_info["job_id"],
			}
		}
		ar = requests.post(remote_url+"prompt", json=data)
		ar.raise_for_status()
		return(remote_chain, remote_info)


class QueueRemoteSingle():
	"""This just abstracts most of the code when only using two GPUs."""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_url": ("STRING", {
					"multiline": False,
					"default": "http://127.0.0.1:8288/",
				}),
				"trigger": (["on_change", "always"],),
				"batch_local": ("INT", {"default": 1, "min": 1, "max": 8}),
				"batch_remote": ("INT", {"default": 1, "min": 1, "max": 8}),
				"enabled": (["true", "false", "remote"],{"default": "true"}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
			},
			"hidden": {
				"prompt": "PROMPT",
			},
		}

	RETURN_TYPES = ("INT", "INT", "REMINFO",)
	RETURN_NAMES = ("seed", "batch", "remote_info",)
	FUNCTION = "queue_on_remote"
	CATEGORY = "remote"
	TITLE = "Queue on remote (single)"

	def queue_on_remote(self, remote_url, trigger, batch_local, batch_remote, enabled, seed, prompt):
		start = QueueRemoteChainStart()
		remote_chain, = start.chain_start(
			workflow = "current",
			trigger  = trigger,
			batch    = batch_local,
			seed     = seed,
			prompt   = prompt
		)
		queue = QueueRemote()
		remote_chain, remote_info = queue.queue_on_remote(
			remote_chain   = remote_chain,
			remote_url     = remote_url,
			batch_override = batch_remote,
			enabled        = enabled
		)
		end = QueueRemoteChainEnd()
		out_seed, out_batch = end.chain_end(remote_chain)
		return(out_seed, out_batch, remote_info)
