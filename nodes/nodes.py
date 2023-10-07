from .control import QueueRemoteChainStart, QueueRemoteChainEnd, QueueRemote, FetchRemote
from .images import LoadImageUrl, SaveImageUrl
from .misc import CombineImageBatch

NODE_CLASS_MAPPINGS = {
	"QueueRemoteChainStart": QueueRemoteChainStart,
	"QueueRemoteChainEnd": QueueRemoteChainEnd,
	"QueueRemote": QueueRemote,
	"FetchRemote": FetchRemote,
	"LoadImageUrl": LoadImageUrl,
	"SaveImageUrl": SaveImageUrl,
	"CombineImageBatch": CombineImageBatch,
}
NODE_DISPLAY_NAME_MAPPINGS = {k:v.TITLE for k,v in NODE_CLASS_MAPPINGS.items()}
