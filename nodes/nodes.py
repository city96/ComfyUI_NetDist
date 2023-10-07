from .control import QueueRemoteChainStart, QueueRemoteChainEnd, QueueRemoteSingle, QueueRemote, FetchRemote
from .images import LoadImageUrl, SaveImageUrl, CombineImageBatch

NODE_CLASS_MAPPINGS = {
	"QueueRemoteChainStart": QueueRemoteChainStart,
	"QueueRemote": QueueRemote,
	"QueueRemoteChainEnd": QueueRemoteChainEnd,
	"QueueRemoteSingle" : QueueRemoteSingle,
	"FetchRemote": FetchRemote,
	"LoadImageUrl": LoadImageUrl,
	"SaveImageUrl": SaveImageUrl,
	"CombineImageBatch": CombineImageBatch,
}
NODE_DISPLAY_NAME_MAPPINGS = {k:v.TITLE for k,v in NODE_CLASS_MAPPINGS.items()}
