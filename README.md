# ComfyUI_NetDist
Run ComfyUI workflows on multiple local GPUs/networked machines.

[NetDist_2xspeed.webm](https://github.com/city96/ComfyUI_NetDist/assets/125218114/b7ec2fcf-1e51-4b05-ad62-355da2a1bf6d)

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

### Local Remote control
You will need at least two different ComfyUI instances. You can use two local GPUs by setting different `--port [port]` and `--cuda-device [number]` launch arguments. You'll most likely want `--port 8288 --cuda-device 1`

#### Simple dual-GPU

This is the simplest setup for people who have 2 GPUs or two separate PCs. It only requires two nodes to work.

You can set the local/remote batch size, as well as when the node should trigger (set it to 'always' if it isn't getting executed - i.e. you changed a sampler setting but not the seed.)

If you're running your second instance on a different PC, add `--listen` to your launch arguments and set the correct remote IP (open a terminal window and check with `ipconfig` on windows or `ip a` on linux).

The `FetchRemote` ('Fetch from remote') node takes an image input. This should be your final image than you want to get back from your second instance (make sure not to route it back into itself). This node will wait for the second image to be generated (there's currently no preview/progress bar).

Workflow JSON: [NetDistSimple.json](https://github.com/city96/ComfyUI_NetDist/files/13825326/NetDistSimple.json)

![NetDistSimple](https://github.com/city96/ComfyUI_NetDist/assets/125218114/dce5a155-2ffa-4979-b184-03de168beecb)

#### Simple multi-machine

You can kind of scale the example above by connecting more of the simple queue nodes together, but the seed is a bit jank and you can get duplicate images if you try and reuse it. I guess just set the seed to randomized on both.

![NetDistMulti](https://github.com/city96/ComfyUI_NetDist/assets/125218114/2a0358aa-ab8e-47e2-82a2-7a27a17d0130)

#### Advanced

This is mostly meant for more "advanced" setups with more than two GPUs. It allows easier per-batch overrides as well as setting a default batch size.

It also allows using a workflow JSON as an input. To allow any workflow to run, the final image can be set to "any" instead of the default "final_image" (which would require the `FetchRemote` node to be in the workflow).

I have nodes to save/load the workflows, but ideally there would be some nodes to also edit them - search and replace seed, etc. PRs welcome ;P

Workflow JSON: [NetDistAdvancedV2.json](https://github.com/city96/ComfyUI_NetDist/files/13843005/NetDistAdvancedV2.json)

![NetDistAdvanced](https://github.com/city96/ComfyUI_NetDist/assets/125218114/851c1ee6-edcf-4489-bab1-92ab9c5ef15e)

(This needs a fake image input to trigger, you can just give it a blank image).

![NetDistSaved](https://github.com/city96/ComfyUI_NetDist/assets/125218114/a39b5117-af1b-4f2c-a94e-5a330acc8ea4)

### Remote images
The `LoadImageUrl` ('Load Image (URL)') Node acts just like the normal 'Load Image' node.

The `SaveImageUrl` ('Save Image (URL)') Node sends a POST request to the target URL with a json containing the images.
- The filenames are the keys.
- The values are the base64 encoded PNG images (optionally with the `data:image/png;base64` prefix).
- The filenames are **not** guaranteed to be unique across batches since they aren't saved locally. You should handle this server-side.
- No data is written to disk on the server.

### Remote latents

This node pack has a set of nodes which should (in theory) allow you to pass latents between the nodes seamlessly. A node to save the input latent as a `.npy` file is provided. This node also returns the filename of the saved latent, which can then be loaded by the other instance.

To load a latent from the other instance, you can plug the filename into this URL:

```
# change the filename with a string replacement node.
http://127.0.0.1:8188/view?filename=ComfyUI_00001_.latent&type=output`
# To load them from the input folder instead, change type to 'input'
http://127.0.0.1:8188/view?filename=TestLatent.npy&type=input
```

The `LoadLatentNumpy` node can also load the default safetensor latents, the npy ones (simple numpy file containing just the latent in the standard torch format) as well as the sd_scripts npz cache files.

![LatentSave](https://github.com/city96/ComfyUI_NetDist/assets/125218114/cd68d8dc-bd96-4018-82c9-400337fc5f80)

### Things you probably shouldn't do:
- Queue a workflow on the same remote worker multiple times from the same client.
- ~~Expect this to work smoothly.~~

## Roadmap
- Fix some edge cases, like linux controlling windows (`os.sep` mismatch).
- Better workflow editing for static workflows.
- Handle multiple separate image output nodes.
