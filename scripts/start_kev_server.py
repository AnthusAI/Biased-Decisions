"""Start a local Kev inference server with pinned settings and memory limits.

This script launches the Kev model server with the exact configuration used for
Biased-Decisions data collection: MLX backend with bfloat16, pinned checkpoint,
4 GiB memory limits, and port 8009. It must run on Apple silicon. The model cache
directory comes from the KEV_HF_HOME environment variable, defaulting to
<repo-root>/var/hf-cache. After launch, the server answers at http://127.0.0.1:8009.
"""
import os
import runpy
import sys
from pathlib import Path

# Determine repo root: parent of the scripts directory
repo_root = Path(__file__).resolve().parents[1]

# Set cache directory from env var or default
hf_cache_dir = os.environ.get('KEV_HF_HOME') or str(repo_root / 'var' / 'hf-cache')

# Set all required environment variables
os.environ.update({
    'HF_HOME': hf_cache_dir,
    'HF_HUB_OFFLINE': '1',
    'KEV_BACKEND': 'mlx',
    'KEV_DTYPE': 'bf16',
    'KEV_PREFIX_CACHE': '0',
    'KEV_DATE_FACTS': '0',
    'KEV_MERGE': '1',
    'KEV_LORA_SCALE': '1',
    'TOKENIZERS_PARALLELISM': 'false',
    'OMP_NUM_THREADS': '2',
})

# Remove any leftover API key or temperature settings
for name in ('KEV_API_KEY', 'KEV_TEMPERATURE'):
    os.environ.pop(name, None)

# Import and configure MLX memory limits before any model code loads
import mlx.core as mx
mx.set_memory_limit(4 * 1024**3)       # 4 GiB
mx.set_cache_limit(256 * 1024**2)      # 256 MiB
mx.set_wired_limit(4 * 1024**3)        # 4 GiB

# Configure command-line arguments and launch kev.serve
sys.argv = [
    'kev.serve',
    '--run', 'jaredpalmer/kev-0.8b@54f4f8777356cd5bbbb6c6919c657f26e6f2f6d8',
    '--port', '8009'
]
runpy.run_module('kev.serve', run_name='__main__')
