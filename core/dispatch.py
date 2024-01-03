import os
import time
import json
import torch
import random
import requests
import numpy as np
from PIL import Image
from copy import deepcopy

from .utils import clean_url, get_client_id

def clear_remote_queue(remote_url):
	r = requests.get(f"{remote_url}/queue", timeout=4)
	r.raise_for_status()
	queue = r.json()

	to_cancel = []
	client_id = get_client_id()
	for k in queue.get("queue_pending", []):
		if k[3].get("client_id") == client_id:
			to_cancel.append(k[1]) # job UUID
	r = requests.post(
		f"{remote_url}/queue",
		json    = {"delete" : to_cancel},
		timeout = 4,
	)
	r.raise_for_status()

	for k in queue.get("queue_running", []):
		if k[3].get("client_id") == client_id:
			r = requests.post(
				f"{remote_url}/interrupt",
				json    = {},
				timeout = 4,
			)
			r.raise_for_status()
			break

def get_remote_os(remote_url):
	url = f"{remote_url}/system_stats"
	r = requests.get(url)
	r.raise_for_status()
	data = r.json()
	return data["system"]["os"]

def dispatch_to_remote(remote_url, prompt, job_id=f"{get_client_id()}-unknown"):
	### PROMPT LOGIC ###
	prompt = deepcopy(prompt)
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
		if prompt[i]["class_type"].startswith("RemoteQueue"):
			if clean_url(prompt[i]["inputs"]["remote_url"]) == remote_url:
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
					"inputs": {"images": prompt[i]["inputs"]["final_image"]},
					"class_type": 'PreviewImage',
				}
			recursive_node_deletion(i)
		# do not save output on remote
		# todo: other output types
		if prompt[i]["class_type"] in ["SaveImage", "PreviewImage"]:
			recursive_node_deletion(i)
	prompt[str(max([int(x) for x in prompt.keys()])+1)] = output
	for i in to_del: del prompt[i]

	### OS LOGIC ###
	sep_remote = "\\" if get_remote_os(remote_url) == "nt" else "/"
	sep_local  = "\\" if os.name == "nt" else "/"
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

	### SEND REQUEST ###
	data = {
		"prompt": prompt,
		"client_id": get_client_id(),
		"extra_data": {
			"job_id": job_id,
		}
	}
	ar = requests.post(f"{remote_url}/prompt", json=data, timeout=4)
	ar.raise_for_status()
	return
