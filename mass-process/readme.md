This is the script I used when I had to mass-process some controlnet inputs for an animation. It was requested that I publish this in issue#2 


Note that you'll have to make all images accessible to the clients, otherwise they fail. I was using the load from URL nodes for this. For testing, I simply used the built-in python web server with `python -m http.server 8080`, but you can use your own web server to host them.


I don't currently have seed randomization or proper output handling. For the later, just disable all the save/preview image nodes other than the one you'll be using as the final output.
