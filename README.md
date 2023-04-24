# ComfyUI_NetDist
Run ComfyUI workflows on multiple local GPUs/networked machines.

Also includes code to utilize in a render farm (save/load images to/from a server).

## Install instructions:
There is currently a single external requirement, which is the `requests` library.
```
pip install requests
```

To install, simply clone into the custom nodes folder.
```
git clone https://github.com/city96/ComfyUI_NetDist ComfyUI/custom_nodes/ComfyUI_NetDist
```

## Usage
### Remote images
The `LoadImageUrl` ('Load Image (URL)') Node acts just like the normal 'Load Image' node.

The `SaveImageUrl` ('Save Image (URL)') Node sends a POST request to the target URL with a json containing the images.
- The filenames are the keys.
- The values are the base64 encoded PNG images (optionally with the `data:image/png;base64` prefix).
- The filenames are **not** guaranteed to be unique across batches since they aren't saved locally. You should handle this server-side.
- No data is written to disk on the server.

### Local Remote control
You will need at least two different ComfyUI instances. You can use two local GPUs by setting different `--port [port]` and `--cuda-device [number]` launch arguments.

The following video is an example of a multi-machine workflow. The `CombineImage` nodes aren't required, they just merge the output images into a single Preview.

https://user-images.githubusercontent.com/125218114/234095447-85bd5111-d407-437a-a270-d159876b3a2a.mp4

**Chaining the seed is required**, as this allows each node to increment the seed (by `node_id*batch_size`). Simply connect the seed output of the first node to the seed input of the next one and eventually into the KSampler.

The `FetchRemote` ('Fetch from remote') node takes an image input, this should be your final image (make sure not to route it back into itself)

The `QueueRemote` ('Queue on remote') node will start the entire current workflow on the remote ComfyUI instance, with some changes:
- Disable all QueueRemote images (to stop recursion)
- Remove all SaveImage and PreviewImage nodes (not needed/makes it so there is only a single output)
- Replaces the `FetchRemote` ('Fetch from remote') node with a PreviewImage node, since this will be the only output
- The `FetchRemote` node (on the current workflow) will wait for the current job to finish on the remote machine.

### Things you probably shouldn't do:
- Have more `FetchRemote` nodes than `QueueRemote` ones.

## Roadmap
- Fix some edge cases, like linux controlling windows (`os.sep` mismatch).
- Switch to per-client batchsize.
- Upload rest of control software (external scheduler).
