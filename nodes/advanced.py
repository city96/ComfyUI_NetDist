from ..core.utils import clean_url, get_client_id, get_new_job_id
from ..core.dispatch import dispatch_to_remote, clear_remote_queue

class RemoteChainStart:
	"""Merge required attributes into one [REMCHAIN]"""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": ("JSON",),
				"trigger": (["on_change", "always"],),
				"batch": ("INT", {"default": 1, "min": 1, "max": 8}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
			}
		}

	RETURN_TYPES = ("REMCHAIN",)
	RETURN_NAMES = ("remote_chain",)
	FUNCTION = "chain_start"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (start of chain)"

	def chain_start(self, workflow, trigger, batch, seed):
		remote_chain = {
			"seed": seed,
			"batch": batch,
			"prompt": workflow,
			"seed_offset": batch,
			"job_id": get_new_job_id(),
		}
		return(remote_chain,)

	@classmethod
	def IS_CHANGED(self, workflow, trigger, batch, seed, prompt):
		uuid = f"W:{workflow},B:{batch},S:{seed}"
		return uuid if trigger == "on_change" else str(time.time())

class RemoteChainEnd:
	"""Split [REMCHAIN] into local seed/batch"""
	def __init__(self):
		pass
	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"remote_chain": ("REMCHAIN",)
			}
		}

	RETURN_TYPES = ("INT", "INT")
	RETURN_NAMES = ("seed", "batch")
	FUNCTION = "chain_end"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (end of chain)"

	def chain_end(self, remote_chain):
		seed = remote_chain["seed"]
		batch = remote_chain["batch"]
		return(seed,batch)

class RemoteQueueWorker:
	"""Start job on remote worker"""
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
				"outputs": (["final_image", "any"],{"default":"final_image"}),
			}
		}

	RETURN_TYPES = ("REMCHAIN", "REMINFO")
	RETURN_NAMES = ("remote_chain", "remote_info")
	FUNCTION = "queue"
	CATEGORY = "remote/advanced"
	TITLE = "Queue on remote (worker)"

	def queue(self, remote_chain, remote_url, batch_override, enabled, outputs):
		current_offset = remote_chain["seed_offset"]
		remote_chain["seed_offset"] += 1 if batch_override == 0 else batch_override
		if enabled == "false":
			return (remote_chain, {})
		if enabled == "remote":
			# apply offset from previous nodes in chain
			remote_chain["seed"] += current_offset
			if batch_override > 0:
				remote_chain["batch"] = batch_override
			return (remote_chain, {})

		remote_url = clean_url(remote_url)
		clear_remote_queue(remote_url)
		dispatch_to_remote(
			remote_url,
			remote_chain["prompt"],
			remote_chain["job_id"],
			outputs,
		)
		remote_info = {
			"remote_url" : remote_url,
			"job_id"     : remote_chain["job_id"],
		}
		return (remote_chain, remote_info)

NODE_CLASS_MAPPINGS = {
	"RemoteChainStart"  : RemoteChainStart,
	"RemoteQueueWorker" : RemoteQueueWorker,
	"RemoteChainEnd"    : RemoteChainEnd,
}
