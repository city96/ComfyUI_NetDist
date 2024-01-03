from ..core.fetch import fetch_from_remote
from ..core.utils import clean_url, get_client_id, get_new_job_id
from ..core.dispatch import dispatch_to_remote, clear_remote_queue

class FetchRemote():
	"""
	Try to retrieve the final output image from the remote client.
	On the remote client, this is replaced with a preview image node.
	I.e. remote_info can be none, but the node shouldn't exist at that point
	"""
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
	FUNCTION = "fetch"
	CATEGORY = "remote"
	TITLE = "Fetch from remote"

	def fetch(self, final_image, remote_info):
		out = fetch_from_remote(
			remote_url = remote_info.get("remote_url"),
			job_id     = remote_info.get("job_id"),
		)
		if out is None:
			out = final_image[:1] * 0.0 # black image
		return (out,)

class RemoteQueueSimple():
	"""
	This is a "simplified" version without any extra controls.
	"""
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
				"batch_local": ("INT", {"default": 1, "min": 1, "max": 8}),
				"batch_remote": ("INT", {"default": 1, "min": 1, "max": 8}),
				"trigger": (["on_change", "always"],),
				"enabled": (["true", "false", "remote"],{"default": "true"}),
				"seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
			},
			"hidden": {
				"prompt": "PROMPT",
			},
		}

	RETURN_TYPES = ("INT", "INT", "REMINFO",)
	RETURN_NAMES = ("seed", "batch", "remote_info",)
	FUNCTION = "queue"
	CATEGORY = "remote"
	TITLE = "Queue on remote (single)"

	def queue(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt):
		if enabled == "false":
			return (seed, batch_local, {})
		if enabled == "remote":
			return (seed+batch_local, batch_remote, {})

		job_id = get_new_job_id()
		remote_url = clean_url(remote_url)
		clear_remote_queue(remote_url)
		dispatch_to_remote(remote_url, prompt, job_id)

		remote_info = {
			"remote_url" : remote_url,
			"job_id"     : job_id,
		}
		return (seed, batch_local, remote_info)

	@classmethod
	def IS_CHANGED(self, remote_url, batch_local, batch_remote, trigger, enabled, seed, prompt):
		uuid = f"W:{remote_url},B1:{batch_local},B2:{batch_remote},S:{seed},E:{enabled}"
		return uuid if trigger == "on_change" else str(time.time())

NODE_CLASS_MAPPINGS = {
	"FetchRemote"       : FetchRemote,
	"RemoteQueueSimple" : RemoteQueueSimple,
}
