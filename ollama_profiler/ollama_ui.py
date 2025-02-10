from ollama_profiler import OllamaProfiler
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import time
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

def setup_environment():
    """Setup environment for the UI"""
    # Add parent directory to path if needed
    if '..' not in sys.path:
        sys.path.append('..')

def create_ui():
    """Create and return the profiler UI"""
    # Ensure environment is setup
    setup_environment()
    
    # Initialize profiler
    profiler = OllamaProfiler()
    
    # Create widgets individually first with explicit styles
    gpu_layers = widgets.IntSlider(
        value=35, 
        min=1, 
        max=50, 
        description='GPU Layers:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='30%')
    )
    
    batch_size = widgets.IntSlider(
        value=1024, 
        min=128, 
        max=2048, 
        step=128, 
        description='Batch Size:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='30%')
    )
    
    compute_threads = widgets.IntSlider(
        value=8, 
        min=1, 
        max=12, 
        description='Threads:',
        style={'description_width': 'initial'},
        layout=widgets.Layout(width='30%')
    )
    
    run_button = widgets.Button(description='Run Test')
    status = widgets.HTML("")
    output = widgets.Output()
    
    def on_run_button_click(b):
        run_button.disabled = True
        run_button.description = "Running..."
        status.value = "<span style='color: blue'>Running test...</span>"
        
        try:
            metrics = profiler.run_test(
                gpu_layers.value,
                batch_size.value,
                compute_threads.value
            )
            
            if metrics:
                with output:
                    output.clear_output(wait=True)
                    
                    # Show tables and history graph side by side
                    profiler.show_tables_and_history(metrics, output)
                    
                    # Show recommendations
                    conn = sqlite3.connect(profiler.db_path)
                    all_runs = pd.read_sql_query("""
                        SELECT * FROM performance_runs 
                        ORDER BY tokens_per_second DESC
                    """, conn)
                    
                    # Show recommendations only
                    recommendations = profiler.generate_recommendations(all_runs, metrics)
                    display(HTML(f"""
                    <ul style='margin-top: 10px;'>
                        {''.join(f'<li style="margin-bottom: 5px;">{r}</li>' for r in recommendations)}
                    </ul>
                    """))
                    
                    conn.close()
                
                status.value = "<span style='color: green'>Test completed successfully</span>"
            else:
                status.value = "<span style='color: red'>Test failed to return metrics</span>"
        except Exception as e:
            status.value = f"<span style='color: red'>Error: {str(e)}</span>"
            print(f"Error details: {str(e)}")
        finally:
            run_button.disabled = False
            run_button.description = "Run Test"
    
    run_button.on_click(on_run_button_click)
    
    # Create layout step by step with explicit styling
    sliders = widgets.HBox(
        [gpu_layers, batch_size, compute_threads],
        layout=widgets.Layout(
            width='80%',
            justify_content='space-between',
            padding='10px'
        )
    )
    controls = widgets.VBox(
        [sliders, run_button, status, output],
        layout=widgets.Layout(width='100%', padding='10px')
    )
    
    return controls 