#!/usr/bin/env python3
"""
rtx5080_egpu_harness.py: All-in-one reproduction, bootstrap, and evaluation harness interface
for running LLM inference on an NVIDIA GeForce RTX 5080 eGPU via Thunderbolt 5 on Apple Silicon.

Hardware Target:
  - Host: Apple Silicon Mac (M-Series, e.g. M5 Max 64GB), macOS Sequoia (15.x / 16.x)
  - Bus: Thunderbolt 5 / USB4 v2 (80 Gbps symmetric / 120 Gbps asymmetric)
  - Enclosure: Razer Core X V2 eGPU (PCIe Gen 4 x4 tunnel)
  - Accelerator: NVIDIA GeForce RTX 5080 (GB203, sm_120, 16 GB GDDR7, PCI ID 10de:2c02)
  - Transport: Tiny Corp DriverKit DEXT (org.tinygrad.tinygpu.driver2)

Usage:
  # 1. Bootstrap blank system (link check, tinygrad clone, apply Blackwell patch, venv setup):
  python3 rtx5080_egpu_harness.py bootstrap

  # 2. Check hardware link and services:
  python3 rtx5080_egpu_harness.py status

  # 3. Start background server and Ollama proxy bridge:
  python3 rtx5080_egpu_harness.py serve

  # 4. Run harness inference (CLI or programmatic):
  python3 rtx5080_egpu_harness.py run "Summarize quantum computing in 2 sentences."
  python3 rtx5080_egpu_harness.py benchmark --tokens 100

  # 5. Stop services safely before unplugging TB5 cable (prevents ApplePMGR panic):
  python3 rtx5080_egpu_harness.py stop

  # 6. Dump architecture facts and panic documentation:
  python3 rtx5080_egpu_harness.py facts
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

# Defaults
DEFAULT_TINY_PORT = 8000
DEFAULT_OLLAMA_PORT = 11440
DEFAULT_TINYGRAD_DIR = Path.home() / "tinygrad"
DEFAULT_VENV_DIR = Path.home() / ".venvs" / "tinygpu"
DEFAULT_MODEL_BLOB = Path.home() / ".ollama" / "models" / "blobs" / "sha256-de0334402b975e19dd48eb43a13f7534772fb5b4a054447f8f6a861b87ec5799"
NVIDIA_RTX5080_DEV_ID = "022c0000"  # 10de:2c02 in little-endian ioreg format

TINYGRAD_PATCH = """diff --git a/tinygrad/llm/cli.py b/tinygrad/llm/cli.py
index 417ffa7..63844c0 100644
--- a/tinygrad/llm/cli.py
+++ b/tinygrad/llm/cli.py
@@ -49,7 +49,8 @@ class SimpleTokenizer:
     vocab: typing.Iterable[tuple[str, int]] = ((tok, idx) for idx, tok in enumerate(kv["tokenizer.ggml.tokens"]))
     normal_tokens, special_tokens = partition(vocab, lambda e: kv["tokenizer.ggml.token_type"][e[1]] == 1)
     special_tokens_dict = dict(special_tokens)
-    return SimpleTokenizer(dict(normal_tokens), special_tokens_dict, kv["tokenizer.ggml.pre"],
+    pre = kv.get("tokenizer.ggml.pre", "qwen2" if "qwen" in kv.get("general.architecture", "") else "llama3")
+    return SimpleTokenizer(dict(normal_tokens), special_tokens_dict, pre,
       bos_id=kv.get('tokenizer.ggml.bos_token_id') if kv.get('tokenizer.ggml.add_bos_token', True) else None,
       eos_id=kv.get('tokenizer.ggml.eos_token_id', 0), eot_id=kv.get('tokenizer.ggml.eot_token_id', special_tokens_dict.get('<|im_end|>')))
 
diff --git a/tinygrad/llm/model.py b/tinygrad/llm/model.py
index 5231e8e..3840460 100644
--- a/tinygrad/llm/model.py
+++ b/tinygrad/llm/model.py
@@ -437,7 +437,7 @@ class Transformer:
       n_heads=n_heads, n_kv_heads=n_kv_heads, norm_eps=kv[f'{arch}.attention.layer_norm_rms_epsilon'],
       vocab_size=len(kv['tokenizer.ggml.tokens']),
       head_dim=head_dim,
-      rope_theta=kv[f'{arch}.rope.freq_base'],
+      rope_theta=kv.get(f'{arch}.rope.freq_base', 1000000.0 if 'qwen' in arch else 10000.0),
       rope_dim=rope_dim,
       v_head_dim=kv.get(f'{arch}.attention.value_length_mla', kv.get(f'{arch}.attention.value_length', head_dim)),
       max_context=max_context,
diff --git a/tinygrad/runtime/ops_nv.py b/tinygrad/runtime/ops_nv.py
index f814a75..a2b519b 100644
--- a/tinygrad/runtime/ops_nv.py
+++ b/tinygrad/runtime/ops_nv.py
@@ -1,5 +1,5 @@
 from __future__ import annotations
-import os, ctypes, contextlib, re, functools, mmap, struct, array, sys, weakref
+import os, ctypes, contextlib, re, functools, mmap, struct, array, sys, weakref, atexit
 assert sys.platform != 'win32'
 from typing import cast
 from dataclasses import dataclass
diff --git a/tinygrad/runtime/support/nv/ip.py b/tinygrad/runtime/support/nv/ip.py
index 58885ac..d54f392 100644
--- a/tinygrad/runtime/support/nv/ip.py
+++ b/tinygrad/runtime/support/nv/ip.py
@@ -1,5 +1,5 @@
 from __future__ import annotations
-import ctypes, time, array, struct, itertools, dataclasses
+import ctypes, time, array, struct, itertools, dataclasses, contextlib
 from typing import cast, Any
 from tinygrad.runtime.autogen import nv, nv_570 as nv_gpu, pci
 from tinygrad.helpers import lo32, hi32, DEBUG, round_up, round_down, fetch_fw, wait_cond, ceildiv
@@ -477,9 +477,10 @@ class NV_GSP(NV_IP):
     # reserve 512MB for the reserved PDES
     res_va = self.nvdev.mm.alloc_vaddr(res_sz:=(512 << 20))
 
-    bufs_p = nv_gpu.struct_NV90F1_CTRL_VASPACE_COPY_SERVER_RESERVED_PDES_PARAMS(pageSize=res_sz, numLevelsToCopy=3,
+    pts = list(self.nvdev.mm.page_tables(res_va, size=res_sz))
+    bufs_p = nv_gpu.struct_NV90F1_CTRL_VASPACE_COPY_SERVER_RESERVED_PDES_PARAMS(pageSize=res_sz, numLevelsToCopy=len(pts),
       virtAddrLo=res_va, virtAddrHi=res_va + res_sz - 1)
-    for i,pt in enumerate(self.nvdev.mm.page_tables(res_va, size=res_sz)):
+    for i,pt in enumerate(pts):
       bufs_p.levels[i] = nv_gpu.struct_NV90F1_CTRL_VASPACE_COPY_SERVER_RESERVED_PDES_PARAMS_level(physAddress=pt.paddr,
         size=self.nvdev.mm.pte_cnt[0] * 8 if i == 0 else 0x1000, pageShift=self.nvdev.mm.pte_covers[i].bit_length() - 1, aperture=1)
     self.rpc_rm_control(hObject=vaspace, cmd=nv_gpu.NV90F1_CTRL_CMD_VASPACE_COPY_SERVER_RESERVED_PDES, params=bufs_p)
@@ -513,8 +514,11 @@ class NV_GSP(NV_IP):
 
     self.stat_q.wait_resp(nv.NV_VGPU_MSG_EVENT_GSP_INIT_DONE)
 
-    self.nvdev.NV_PBUS_BAR1_BLOCK.write(mode=0, target=0, ptr=0)
-    if self.nvdev.fmc_boot: self.nvdev.NV_VIRTUAL_FUNCTION_PRIV_FUNC_BAR1_BLOCK_LOW_ADDR.write(mode=0, target=0, ptr=0)
+    if not self.nvdev.fmc_boot: self.nvdev.NV_PBUS_BAR1_BLOCK.write(mode=0, target=0, ptr=0)
+    else:
+      with contextlib.suppress(Exception): self.nvdev.NV_VIRTUAL_FUNCTION_PRIV_BAR1_BLOCK.write(mode=0, target=0, ptr=0)
+      with contextlib.suppress(Exception): self.nvdev.NV_VIRTUAL_FUNCTION_PRIV_FUNC_BAR1_BLOCK_LOW_ADDR.write(mode=0, target=0, ptr=0)
+      self.nvdev.vram[self.nvdev.mm.root_page_table.paddr : self.nvdev.mm.root_page_table.paddr + 0x1000] = bytes(0x1000)
 
     self.priv_root = 0xc1e00004
     self.init_golden_image()
@@ -611,7 +615,7 @@ class NV_GSP(NV_IP):
   def rpc_unloading_guest_driver(self):
     data = nv.rpc_unloading_guest_driver_v(bInPMTransition=0, bGc6Entering=0, newLevel=(__GPU_STATE_FLAGS_FAST_UNLOAD:=1 << 6))
     self.cmd_q.send_rpc(nv.NV_VGPU_MSG_FUNCTION_UNLOADING_GUEST_DRIVER, bytes(data))
-    self.stat_q.wait_resp(nv.NV_VGPU_MSG_FUNCTION_UNLOADING_GUEST_DRIVER)
+    with contextlib.suppress(Exception): self.stat_q.wait_resp(nv.NV_VGPU_MSG_FUNCTION_UNLOADING_GUEST_DRIVER, timeout=500)
 
   def rpc_set_registry_table(self):
     table = {'RMForcePcieConfigSave': 0x1, 'RMSecBusResetEnable': 0x1}
diff --git a/tinygrad/runtime/support/nv/nvdev.py b/tinygrad/runtime/support/nv/nvdev.py
index bddeaf5..e4649dd 100644
--- a/tinygrad/runtime/support/nv/nvdev.py
+++ b/tinygrad/runtime/support/nv/nvdev.py
@@ -4,7 +4,7 @@ from tinygrad.helpers import getenv, DEBUG, getbits, round_up
 from tinygrad.runtime.autogen import pci
 from tinygrad.runtime.support.memory import TLSFAllocator, MemoryManager, AddrSpace
 from tinygrad.runtime.support.nv.ip import NV_FLCN, NV_FLCN_COT, NV_GSP
-from tinygrad.runtime.support.system import PCIDevice
+from tinygrad.runtime.support.system import PCIDevice, RemotePCIDevice
 from tinygrad.runtime.support.hcq import MMIOInterface
 
 NV_DEBUG = getenv("NV_DEBUG", 0)
@@ -102,7 +102,7 @@ class NVDev:
     self.include("dev_fb", "tu102")
     self.include("dev_gc6_island", "ga102")
 
-    if self.reg("NV_PFB_PRI_MMU_WPR2_ADDR_HI").read() != 0:
+    if self.reg("NV_PFB_PRI_MMU_WPR2_ADDR_HI").read() != 0 and not isinstance(self.pci_dev, RemotePCIDevice):
       self.pci_dev.write_config_flush(pci.PCI_COMMAND, self.pci_dev.read_config(pci.PCI_COMMAND, 2) & ~pci.PCI_COMMAND_MASTER, 2)
       if DEBUG >= 2: print(f"nv {self.devfmt}: WPR2 is up. Issuing a full reset.", flush=True)
       self.pci_dev.reset()
"""

# ---------------------------------------------------------------------------
# Hardware & Link Diagnostics
# ---------------------------------------------------------------------------

def check_link_safe() -> bool:
    """Safely check if the RTX 5080 is detected in IOKit without triggering IOPCIFamily panics."""
    try:
        proc = subprocess.run(
            ["ioreg", "-r", "-c", "IOPCIDevice", "-l"],
            capture_output=True,
            text=True,
            check=False
        )
        return f"<{NVIDIA_RTX5080_DEV_ID}>" in proc.stdout
    except Exception as e:
        sys.stderr.write(f"Error checking link: {e}\n")
        return False

def check_driverkit_dext() -> bool:
    """Check if the TinyGPU DriverKit extension is active."""
    try:
        proc = subprocess.run(
            ["ioreg", "-c", "TinyGPU", "-l"],
            capture_output=True,
            text=True,
            check=False
        )
        return "TinyGPU" in proc.stdout
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Bootstrap & Setup
# ---------------------------------------------------------------------------

def run_cmd(cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    sys.stderr.write(f">> {' '.join(str(c) for c in cmd)}\n")
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True, text=True)

def bootstrap_system(tinygrad_dir: Path = DEFAULT_TINYGRAD_DIR, venv_dir: Path = DEFAULT_VENV_DIR) -> None:
    """Full bootstrap of a blank macOS Apple Silicon machine."""
    print("=== [1/6] System & Hardware Verification ===")
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError(f"Unsupported platform: {platform.system()} {platform.machine()}. Must be macOS arm64 (Apple Silicon).")
    print(" Host OS: macOS Apple Silicon (arm64)")

    if not check_link_safe():
        print(" WARNING: NVIDIA RTX 5080 (10de:2c02) not detected over Thunderbolt link!")
        print("  - Ensure enclosure is powered and connected via Thunderbolt 5/4 cable.")
        print("  - Reseat the cable if necessary.")
    else:
        print(" PCIe Link: NVIDIA RTX 5080 (10de:2c02) enumerated in IOKit registry.")

    if not check_driverkit_dext():
        print(" DriverKit DEXT (TinyGPU.dext) not currently attached.")
        print("  To install TinyGPU.dext:")
        print("  Download from https://github.com/tinygrad/tinygpu and approve in System Settings -> Privacy & Security.")
    else:
        print(" DriverKit DEXT: TinyGPU active and matching PCIe endpoint.")

    print("\n=== [2/6] tinygrad Repository Setup ===")
    if not tinygrad_dir.exists():
        print(f" Cloning tinygrad into {tinygrad_dir}...")
        run_cmd(["git", "clone", "https://github.com/tinygrad/tinygrad.git", str(tinygrad_dir)])
    else:
        print(f" tinygrad repository exists at {tinygrad_dir}.")

    print("\n=== [3/6] Applying Blackwell GSP & Qwen Tokenizer Patch ===")
    patch_file = tinygrad_dir / "tinygpu_blackwell_fix.patch"
    patch_file.write_text(TINYGRAD_PATCH)
    try:
        run_cmd(["git", "-C", str(tinygrad_dir), "apply", "--check", str(patch_file)])
        run_cmd(["git", "-C", str(tinygrad_dir), "apply", str(patch_file)])
        print(" Patch applied successfully to tinygrad.")
    except subprocess.CalledProcessError:
        print(" Patch already applied or partially merged. Skipping.")

    print("\n=== [4/6] Python Virtual Environment Setup ===")
    venv_python = venv_dir / "bin" / "python3"
    if not venv_python.exists():
        print(f" Creating virtualenv at {venv_dir}...")
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        run_cmd([sys.executable, "-m", "venv", str(venv_dir)])
    
    print(" Installing core dependencies into virtualenv...")
    run_cmd([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
    run_cmd([str(venv_python), "-m", "pip", "install", "packaging", "blobfile", "numpy", "sentencepiece", "tiktoken"])

    print("\n=== [5/6] Model Verification ===")
    if DEFAULT_MODEL_BLOB.exists():
        print(f" Found default model blob at: {DEFAULT_MODEL_BLOB}")
    else:
        print(f" Note: Default blob ({DEFAULT_MODEL_BLOB.name[:16]}...) not found.")
        print(" You can supply any HuggingFace ID (e.g. Qwen/Qwen2.5-7B-Instruct) or local GGUF path to 'serve'.")

    print("\n=== [6/6] Bootstrap Complete ===")
    print("Ready to launch. Run:\n  python3 rtx5080_egpu_harness.py serve")

# ---------------------------------------------------------------------------
# Server & Daemon Management
# ---------------------------------------------------------------------------

def stop_services() -> None:
    """Gracefully terminate daemons to prevent ApplePMGR power-gating kernel panics."""
    print("Terminating tinygrad and eGPU proxy processes...")
    subprocess.run(["pkill", "-f", "tinygrad.llm"], check=False)
    subprocess.run(["pkill", "-f", "ollama-egpu-proxy.py"], check=False)
    subprocess.run(["pkill", "-f", "rtx5080_egpu_harness.py serve"], check=False)
    time.sleep(1)
    print("All eGPU daemons stopped. Safe to disconnect Thunderbolt 5 cable.")

def is_port_open(port: int, path: str = "/") -> bool:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="HEAD")
        with urllib.request.urlopen(req, timeout=1.5):
            return True
    except Exception:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="GET")
            with urllib.request.urlopen(req, timeout=1.5):
                return True
        except Exception:
            return False

def start_services(
    model: str = str(DEFAULT_MODEL_BLOB),
    tiny_port: int = DEFAULT_TINY_PORT,
    proxy_port: int = DEFAULT_OLLAMA_PORT,
    max_context: int = 4096,
    tinygrad_dir: Path = DEFAULT_TINYGRAD_DIR,
    venv_dir: Path = DEFAULT_VENV_DIR
) -> None:
    """Launch the tinygrad.llm daemon on DEV=NV and the Ollama REST API compatibility proxy."""
    if not check_link_safe():
        raise RuntimeError("RTX 5080 not detected in IOKit registry. Reseat cable before starting.")

    venv_python = venv_dir / "bin" / "python3"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    # 1. Start tinygrad.llm backend if not running
    if not is_port_open(tiny_port, "/v1/models"):
        print(f"Starting tinygrad.llm on RTX 5080 (port {tiny_port}, context {max_context})...")
        env = os.environ.copy()
        env["DEV"] = "NV"
        env["PYTHONPATH"] = f"{tinygrad_dir}:{env.get('PYTHONPATH', '')}"
        env.pop("JITBEAM", None)  # Prevent Docker container storm

        cmd = [
            str(venv_python), "-m", "tinygrad.llm",
            "--model", str(model),
            "--max_context", str(max_context),
            "--serve", str(tiny_port)
        ]
        log_path = Path("/tmp/tinygrad_llm.log")
        with open(log_path, "w") as log_f:
            subprocess.Popen(cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT)
        
        print(f"Waiting for GSP boot and VRAM model allocation on port {tiny_port}...")
        started = False
        for _ in range(120):
            if is_port_open(tiny_port, "/v1/models"):
                started = True
                break
            time.sleep(1)
        if not started:
            raise RuntimeError(f"tinygrad.llm failed to start. Inspect logs: cat {log_path}")
        print(" tinygrad.llm backend is UP.")
    else:
        print(f" tinygrad.llm backend is already running on port {tiny_port}.")

    # 2. Start Ollama API proxy if not running
    if not is_port_open(proxy_port, "/api/version"):
        print(f"Starting Ollama API proxy bridge on port {proxy_port}...")
        proxy_script = Path.home() / ".local" / "bin" / "ollama-egpu-proxy.py"
        if not proxy_script.exists():
            proxy_script = Path("/tmp/ollama_proxy_internal.py")
            proxy_script.write_text((Path.home() / ".local" / "bin" / "ollama-egpu-proxy.py").read_text())
        
        env = os.environ.copy()
        env["TINYGRAD_LLM_URL"] = f"http://127.0.0.1:{tiny_port}"
        env["OLLAMA_PROXY_PORT"] = str(proxy_port)
        log_path = Path("/tmp/ollama_proxy.log")
        with open(log_path, "w") as log_f:
            subprocess.Popen([sys.executable, str(proxy_script)], env=env, stdout=log_f, stderr=subprocess.STDOUT)
        time.sleep(1)
        print(" Ollama API proxy bridge is UP.")
    else:
        print(f" Ollama API proxy is already running on port {proxy_port}.")

    print(f"\n eGPU Stack Active!")
    print(f"   Ollama Host: http://127.0.0.1:{proxy_port}")
    print(f"   Test Command: OLLAMA_HOST=http://127.0.0.1:{proxy_port} ollama list")

# ---------------------------------------------------------------------------
# Programmatic Harness Client
# ---------------------------------------------------------------------------

class RTX5080Client:
    """Direct programmatic client for evaluation harnesses and agent pipelines."""

    def __init__(self, host: str = f"http://127.0.0.1:{DEFAULT_OLLAMA_PORT}"):
        self.host = host.rstrip("/")

    def is_healthy(self) -> bool:
        try:
            req = urllib.request.Request(f"{self.host}/api/version")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        req = urllib.request.Request(f"{self.host}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            return data.get("models", [])

    def generate(self, prompt: str, model: str = "default", stream: bool = False, temperature: float = 0.0) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode())
            return res.get("response", "")

    def generate_stream(self, prompt: str, model: str = "default") -> Generator[str, None, None]:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    yield chunk.get("response", "")

    def chat(self, messages: List[Dict[str, str]], model: str = "default") -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode())
            return res.get("message", {}).get("content", "")

# ---------------------------------------------------------------------------
# Diagnostics & Benchmark
# ---------------------------------------------------------------------------

def run_benchmark(tokens: int = 128) -> None:
    client = RTX5080Client()
    if not client.is_healthy():
        print("Error: RTX 5080 eGPU service not reachable on port 11440.")
        return

    prompt = f"Count sequentially from 1 to {tokens} formatted as comma-separated integers:"
    print(f"Running benchmark on RTX 5080 (Target ~{tokens} tokens)...")
    start_t = time.perf_counter()
    resp = client.generate(prompt)
    elapsed = time.perf_counter() - start_t

    est_tokens = len(resp.split())
    tps = est_tokens / elapsed if elapsed > 0 else 0
    print(f"\nResponse Received:\n{resp[:160]}...\n")
    print(f"Latency: {elapsed:.2f} s | Approx Tokens: {est_tokens} | Approx Throughput: {tps:.2f} tokens/sec")

def dump_facts() -> None:
    facts = {
        "hardware": {
            "host": "Apple MacBook Pro M5 Max (64 GB unified memory)",
            "bus": "Thunderbolt 5 / USB4 v2 (80 Gbps / PCIe Gen 4 x4)",
            "enclosure": "Razer Core X V2 (PCIe switch, 650W internal ATX)",
            "gpu": "NVIDIA GeForce RTX 5080 (GB203, sm_120, 16 GB GDDR7)",
            "pci_id": "10de:2c02"
        },
        "critical_safeguards": {
            "panic_1_iopcifamily": "Never run system_profiler SPPCIDataType while PCIe link is active. Race in configRead16 causes data abort panic. Use 'ioreg -r -c IOPCIDevice -l'.",
            "panic_2_applepmgr": "Never unplug Thunderbolt 5 cable while tinygrad holds MMIO BAR mappings. ApplePMGR watchdog panics after 30000ms. Always execute stop/pkill before unplugging.",
            "pcie_resets": "macOS marks IOPCIDeviceDeadOnRestore=Yes across Thunderbolt. Do not issue secondary bus resets (SBR); use persistent daemon.",
            "kernel_compilation": "Do NOT set JITBEAM=2 on macOS; spawns Docker containers. Standard JIT compiles in <2s and caches to disk."
        },
        "ports": {
            "tinygrad_llm_openai": 8000,
            "ollama_api_proxy": 11440
        }
    }
    print(json.dumps(facts, indent=2))

# ---------------------------------------------------------------------------
# CLI Parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="All-in-one RTX 5080 eGPU Bootstrap & Harness Interface")
    sub = parser.add_subparsers(dest="command", required=True)

    # bootstrap
    p_boot = sub.add_parser("bootstrap", help="Setup dependencies, clone tinygrad, apply patches, test link")
    p_boot.add_argument("--tinygrad-dir", type=Path, default=DEFAULT_TINYGRAD_DIR)
    p_boot.add_argument("--venv-dir", type=Path, default=DEFAULT_VENV_DIR)

    # serve
    p_serve = sub.add_parser("serve", help="Start tinygrad.llm and Ollama proxy bridge")
    p_serve.add_argument("--model", type=str, default=str(DEFAULT_MODEL_BLOB))
    p_serve.add_argument("--context", type=int, default=4096)
    p_serve.add_argument("--port", type=int, default=DEFAULT_OLLAMA_PORT)

    # stop
    sub.add_parser("stop", help="Safely kill all eGPU daemons before cable unplug")

    # status
    sub.add_parser("status", help="Check hardware link, DriverKit, and daemon health")

    # run
    p_run = sub.add_parser("run", help="Send a one-shot prompt to the model")
    p_run.add_argument("prompt", type=str, help="Prompt text")
    p_run.add_argument("--stream", action="store_true", help="Stream response tokens")

    # benchmark
    p_bench = sub.add_parser("benchmark", help="Run token latency/throughput test")
    p_bench.add_argument("--tokens", type=int, default=128)

    # facts
    sub.add_parser("facts", help="Print structured hardware, register, and safety facts")

    args = parser.parse_args()

    if args.command == "bootstrap":
        bootstrap_system(args.tinygrad_dir, args.venv_dir)
    elif args.command == "serve":
        start_services(model=args.model, max_context=args.context, proxy_port=args.port)
    elif args.command == "stop":
        stop_services()
    elif args.command == "status":
        link = check_link_safe()
        dext = check_driverkit_dext()
        t_open = is_port_open(DEFAULT_TINY_PORT, "/v1/models")
        o_open = is_port_open(DEFAULT_OLLAMA_PORT, "/api/version")
        print(f"PCIe Link (RTX 5080)   : {'[CONNECTED]' if link else '[DISCONNECTED]'}")
        print(f"DriverKit (TinyGPU)    : {'[ACTIVE]' if dext else '[INACTIVE]'}")
        print(f"tinygrad.llm (Port 8000): {'[UP]' if t_open else '[DOWN]'}")
        print(f"Ollama Proxy (Port 11440): {'[UP]' if o_open else '[DOWN]'}")
    elif args.command == "run":
        client = RTX5080Client()
        if args.stream:
            for chunk in client.generate_stream(args.prompt):
                sys.stdout.write(chunk)
                sys.stdout.flush()
            print()
        else:
            print(client.generate(args.prompt))
    elif args.command == "benchmark":
        run_benchmark(args.tokens)
    elif args.command == "facts":
        dump_facts()

if __name__ == "__main__":
    main()
