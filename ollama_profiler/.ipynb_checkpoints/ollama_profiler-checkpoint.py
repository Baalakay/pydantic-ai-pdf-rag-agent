#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sqlite3
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from IPython.display import display, HTML
import seaborn as sns
import matplotlib.pyplot as plt
import ipywidgets as widgets

OLLAMA_API_URL = "http://host.docker.internal:11434"

class OllamaProfiler:
    def __init__(self):
        self.db_path = Path.home() / ".config/ollama/performance.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for storing performance metrics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS performance_runs
                    (timestamp TEXT,
                     gpu_layers INTEGER,
                     batch_size INTEGER,
                     compute_threads INTEGER,
                     total_duration REAL,
                     load_duration REAL,
                     prompt_eval_duration REAL,
                     eval_duration REAL,
                     tokens_per_second REAL,
                     avg_token_time REAL,
                     metal_stats TEXT)''')  # Added Metal GPU stats
        conn.commit()
        conn.close()

    def get_metal_stats(self):
        """Get Apple Metal GPU statistics"""
        try:
            result = subprocess.run(
                ['powermetrics', '--samplers', 'gpu_power', '-n', '1'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout
        except:
            return "GPU stats collection failed"

    def run_test(self, gpu_layers, batch_size, compute_threads):
        """Run a single performance test"""
        print(f"\nRunning test with settings:")
        print(f"GPU Layers: {gpu_layers}")
        print(f"Batch Size: {batch_size}")
        print(f"Compute Threads: {compute_threads}")

        # Set environment variables
        env = {
            "OLLAMA_GPU_LAYERS": str(gpu_layers),
            "OLLAMA_BATCH_SIZE": str(batch_size),
            "OLLAMA_COMPUTE_THREADS": str(compute_threads),
            "OLLAMA_METAL": "true",
            "PATH": os.environ["PATH"]
        }

        # Restart Ollama with new settings
        subprocess.run(["pkill", "ollama"], capture_output=True)
        time.sleep(2)
        
        # Start Ollama
        ollama_process = subprocess.Popen(["ollama", "serve"], env=env)
        time.sleep(5)

        # Get Metal stats before test
        metal_stats = self.get_metal_stats()

        # Run test
        response = subprocess.run([
            "curl", "-s", "-X", "POST", f"{OLLAMA_API_URL}/api/generate",
            "-d", json.dumps({
                "model": "deepseek-r1:7b",
                "prompt": "Write a hello world in Python",
                "options": {
                    "num_predict": 100,
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 10
                }
            })
        ], capture_output=True, text=True)

        # Parse response
        last_line = response.stdout.strip().split('\n')[-1]
        metrics = json.loads(last_line)

        # Calculate and store metrics
        run_metrics = {
            'timestamp': datetime.now().isoformat(),
            'gpu_layers': gpu_layers,
            'batch_size': batch_size,
            'compute_threads': compute_threads,
            'total_duration': metrics['total_duration'] / 1e9,
            'load_duration': metrics['load_duration'] / 1e9,
            'prompt_eval_duration': metrics['prompt_eval_duration'] / 1e9,
            'eval_duration': metrics['eval_duration'] / 1e9,
            'tokens_per_second': metrics['eval_count'] / (metrics['eval_duration'] / 1e9),
            'avg_token_time': (metrics['eval_duration'] / metrics['eval_count']) / 1e6,
            'metal_stats': metal_stats
        }

        # Save to database
        conn = sqlite3.connect(self.db_path)
        pd.DataFrame([run_metrics]).to_sql('performance_runs', conn, 
                                         if_exists='append', index=False)
        conn.close()

        return run_metrics

