NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def remote_control():
	global NODE_CLASS_MAPPINGS
	global NODE_DISPLAY_NAME_MAPPINGS
	from .nodes.remote_control import QueueRemote, FetchRemote
	NODE_CLASS_MAPPINGS.update({
		"QueueRemote": QueueRemote,
		"FetchRemote": FetchRemote,
	})
	NODE_DISPLAY_NAME_MAPPINGS.update({
		"QueueRemote": "Queue on remote",
		"FetchRemote": "Fetch from remote",
	})

def remote_images():
	global NODE_CLASS_MAPPINGS
	global NODE_DISPLAY_NAME_MAPPINGS
	from .nodes.remote_images import LoadImageUrl, SaveImageUrl
	NODE_CLASS_MAPPINGS.update({
		"LoadImageUrl": LoadImageUrl,
		"SaveImageUrl": SaveImageUrl,
	})
	NODE_DISPLAY_NAME_MAPPINGS.update({
		"LoadImageUrl": "Load Image (URL)",
		"SaveImageUrl": "Save Image (URL)",
	})

def remote_misc():
	global NODE_CLASS_MAPPINGS
	global NODE_DISPLAY_NAME_MAPPINGS
	from .nodes.misc import CombineImageBatch
	NODE_CLASS_MAPPINGS.update({
		"CombineImageBatch": CombineImageBatch,
	})
	NODE_DISPLAY_NAME_MAPPINGS.update({
		"CombineImageBatch": "Combine images",
	})

print("Loading network distribution node pack")
remote_control()
remote_images()
remote_misc()
