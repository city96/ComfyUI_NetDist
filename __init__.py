# only import if running as a custom node
try:
	import comfy.utils
except ImportError:
	pass
else:
	NODE_CLASS_MAPPINGS = {}

	from .nodes.simple import NODE_CLASS_MAPPINGS as NetNodes
	NODE_CLASS_MAPPINGS.update(NetNodes)

	from .nodes.advanced import NODE_CLASS_MAPPINGS as AdvNodes
	NODE_CLASS_MAPPINGS.update(AdvNodes)

	from .nodes.images import NODE_CLASS_MAPPINGS as ImgNodes
	NODE_CLASS_MAPPINGS.update(ImgNodes)

	from .nodes.workflows import NODE_CLASS_MAPPINGS as WrkNodes
	NODE_CLASS_MAPPINGS.update(WrkNodes)

	NODE_DISPLAY_NAME_MAPPINGS = {k:v.TITLE for k,v in NODE_CLASS_MAPPINGS.items()}
	__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
