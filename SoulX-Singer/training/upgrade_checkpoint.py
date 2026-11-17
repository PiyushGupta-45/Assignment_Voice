"""Create a non-destructive 4096-vocabulary initialization for fine-tuning."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import torch

def main():
    p=argparse.ArgumentParser(); p.add_argument("--base", required=True); p.add_argument("--output", required=True); args=p.parse_args()
    ckpt=torch.load(args.base,map_location="cpu",weights_only=False)
    state=ckpt["state_dict"]
    key="note_text_encoder.weight"; old=state[key]
    if old.shape[0] > 4096: raise ValueError("base vocabulary exceeds multilingual vocabulary")
    new=torch.empty((4096,old.shape[1]), dtype=old.dtype)
    new[:old.shape[0]]=old
    # Newly introduced phones start at the learned unknown-token representation;
    # they must be fine-tuned on aligned singing before serving.
    new[old.shape[0]:]=old[3].unsqueeze(0)
    state[key]=new
    ckpt["state_dict"]=state; ckpt["multilingual_initialized"]=True; ckpt["trained_languages"]=[]
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); torch.save(ckpt,args.output)
    Path(args.output).with_name("manifest.json").write_text(json.dumps({"base_checkpoint":args.base,"trained_languages":[],"status":"initialization_only"},indent=2),encoding="utf-8")
if __name__ == "__main__": main()
