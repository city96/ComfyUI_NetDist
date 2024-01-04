import os
import json
import hashlib
import folder_paths

class SaveDiskWorkflowJSON:
	"""Save workflow to disk"""
	def __init__(self):
		self.output_dir = folder_paths.get_output_directory()

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"workflow": ("JSON", ),
				"filename_prefix": ("STRING", {"default": "workflow/ComfyUI"}),
			}
		}

	RETURN_TYPES = ()
	FUNCTION = "save_workflow"
	OUTPUT_NODE = True
	CATEGORY = "remote/advanced"
	TITLE = "Save workflow (disk)"

	def save_workflow(self, workflow, filename_prefix):
		full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir)

		json_path = os.path.join(full_output_folder, f"{filename}_{counter:05}_.json")
		with open(json_path, "w") as f:
			f.write(json.dumps(workflow, indent=2))
		return {}

class LoadDiskWorkflowJSON:
	"""Load workflow JSON from disk"""
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		input_dir = folder_paths.get_input_directory()
		files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f)) and f.endswith(".json")]
		return {
			"required": {
				"workflow": [sorted(files),],
			}
		}

	RETURN_TYPES = ("JSON",)
	RETURN_NAMES = ("Workflow JSON",)
	FUNCTION = "load_workflow"
	CATEGORY = "remote/advanced"
	TITLE = "Load workflow (disk)"

	def load_workflow(self, workflow):
		json_path = folder_paths.get_annotated_filepath(workflow)
		with open(json_path) as f:
			data = json.loads(f.read())
		return (data,)

	@classmethod
	def IS_CHANGED(s, workflow):
		json_path = folder_paths.get_annotated_filepath(workflow)
		m = hashlib.sha256()
		with open(json_path, 'rb') as f:
			m.update(f.read())
		return m.digest().hex()

	@classmethod
	def VALIDATE_INPUTS(s, workflow):
		if not folder_paths.exists_annotated_filepath(workflow):
			return "Invalid JSON file: {}".format(workflow)
		json_path = folder_paths.get_annotated_filepath(workflow)
		with open(json_path) as f:
			try: json.loads(f.read())
			except:
				return "Failed to read JSON file: {}".format(workflow)
		return True

class LoadCurrentWorkflowJSON:
	"""Fetch the current workflow/prompt as an API compatible JSON"""
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {},
			"hidden": {
				"prompt": "PROMPT",
			},
		}
	
	RETURN_TYPES = ("JSON",)
	RETURN_NAMES = ("Workflow JSON",)
	FUNCTION = "load_workflow"
	CATEGORY = "remote/advanced"
	TITLE = "Load workflow (current)"

	def load_workflow(self, prompt):
		return (prompt,)

	@classmethod
	def IS_CHANGED(s, prompt):
		return hashlib.sha256(json.dumps(prompt)).digest().hex()

NODE_CLASS_MAPPINGS = {
	"SaveDiskWorkflowJSON":    SaveDiskWorkflowJSON,
	"LoadDiskWorkflowJSON":    LoadDiskWorkflowJSON,
	"LoadCurrentWorkflowJSON": LoadCurrentWorkflowJSON,
}
