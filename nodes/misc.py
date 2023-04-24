import torch
import torchvision

class CombineImageBatch:
	def __init__(self):
		pass

	@classmethod
	def INPUT_TYPES(s):
		return {
			"required": {
				"images_a": ("IMAGE",),
				"images_b": ("IMAGE",),
			}
		}

	RETURN_TYPES = ("IMAGE",)
	RETURN_NAMES = ("images",)
	FUNCTION = "combine_images"
	CATEGORY = "remote"

	def combine_images(self,images_a,images_b):
		try:
			out = torch.cat((images_a,images_b))
		except RuntimeError:
			print(f"Imagine size mismatch! {images_a.size()}, {images_b.size()}")
			out = images_a
		return (out,)
