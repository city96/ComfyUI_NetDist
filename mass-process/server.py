import os
import time
import yaml
import json
import requests
import argparse
from PIL import Image
from tqdm import tqdm
from queue import Queue
from copy import deepcopy
from threading import Thread

class JobShard:
	def __init__(self, workflow, job_num):
		self.workflow = workflow  # raw workflow
		self.job_num = job_num    # numerical ID of job
		self.prompt = None        # created when assigned to worker
		self.job_id = None        # ^

	def format_workflow(self, rep, system, job_num):
		w = deepcopy(self.workflow)
		for i in w.keys():
			# Fix path mismatch
			ct = w[i]["class_type"]
			pr = ("\\","/") if system == "posix" else ("/","\\")
			if ct == "LoraLoader":
				w[i]["inputs"]["lora_name"] = w[i]["inputs"]["lora_name"].replace(*pr)
			elif ct == "VAELoader":
				w[i]["inputs"]["vae_name"] = w[i]["inputs"]["vae_name"].replace(*pr)
			elif ct in ["CheckpointLoader","CheckpointLoaderSimple"]:
				w[i]["inputs"]["ckpt_name"] = w[i]["inputs"]["ckpt_name"].replace(*pr)
			# replace strings
			for k in w[i].get("inputs",{}).keys():
				src = w[i]["inputs"][k]
				dst = [x["dst"] for x in rep if x["src"] == src]
				if dst:
					w[i]["inputs"][k] = dst[0].format(job_num=job_num)
		self.prompt = w

	def assign(self, worker):
		self.format_workflow(worker.conf["replacement"], worker.system, self.job_num)
		self.job_id = f"{worker.name}-{self.job_num}@{int(time.time())}"

class Worker:
	def __init__(self, name, system, url, conf, jobs, prog):
		self.name = name
		self.url = url.rstrip("/") if url.endswith("/") else url
		self.system = system.lower().strip()
		self.conf = conf # global config
		self.jobs = jobs # queue of all jobs
		self.prog = prog # progress bar
		self.job = None

	def is_busy(self):
		busy = True if self.job else False
		return busy

	def run(self):
		while not self.jobs.empty():
			self.job = self.jobs.get()
			self.job.assign(self)
			self.start_job()
			self.fetch_job()
			self.job = None
			self.jobs.task_done()
			self.prog.update()

	def start_job(self):
		url = f"{self.url}/prompt"
		data = {
			"prompt": self.job.prompt,
			"client_id": "netdist-mass",
			"extra_data": {
				"job_id": self.job.job_id,
			}
		}
		r = requests.post(url, json=data)
		r.raise_for_status()

	def wait_for_job(self):
		url = self.url + "/history"
		image_data = None
		while not image_data:
			r = requests.get(url)
			r.raise_for_status()
			data = r.json()
			if not data:
				time.sleep(0.5)
				continue
			for i,d in data.items():
				if d["prompt"][3].get("job_id") == self.job.job_id:
					image_data = d["outputs"][list(d["outputs"].keys())[-1]].get("images")
					break
			time.sleep(0.5)
		return image_data

	def fetch_job(self):
		images = []
		for i in self.wait_for_job():
			img_url = f"{self.url}/view?filename={i['filename']}&subfolder={i['subfolder']}&type={i['type']}"
			ir = requests.get(img_url, stream=True)
			ir.raise_for_status()
			images.append(Image.open(ir.raw))

		if len(images) == 0:
			print(f"{self.name}@{self.url} job failed")
		elif len(images) == 1:
			images[0].save(f"output/{self.job.job_num}.png")
		else:
			for i in range(len(images)):
				images[i].save(f"output/{self.job.job_num}.{i}.png")

def get_workflow(path):
	if path.endswith(".png"):
		img = Image.open(path) 
		data = json.loads(
			img.text.get("prompt")
		)
	else:
		print("invalid input workflow")
		exit(1)
	return data

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--conf', required=True, help="Config file describing job.")
	args = parser.parse_args()

	with open(args.conf) as f:
		conf = yaml.safe_load(f.read())

	if not os.path.isdir("output"):
		os.mkdir("output")

	# creqte queue with jobs
	jobs = Queue()
	wf = get_workflow(conf["workflow"])
	for job_num in range(conf["job_start"],conf["job_end"]):
		jobs.put(
			JobShard(wf, job_num)
		)
	prog = tqdm(total=jobs.qsize())

	# initialize workers
	workers = []
	for name, k in conf["workers"].items():
		workers.append(Worker(
			name=name,
			system=k["system"],
			url=k["url"],
			jobs=jobs,
			prog=prog,
			conf=conf)
		)


	# execute all
	[Thread(target=w.run, daemon=True).start() for w in workers]
	jobs.join()
