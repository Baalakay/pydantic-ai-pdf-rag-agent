#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sqlite3
import time
import json
import os
import socket
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from IPython.display import display, HTML
import seaborn as sns
import matplotlib.pyplot as plt
import ipywidgets as widgets
import requests
from rich.console import Console
from rich.table import Table
import argparse
from plotly.subplots import make_subplots

OLLAMA_API_URL = "http://host.docker.internal:11434"
console = Console()

class OllamaProfiler:
    def __init__(self):
        self.db_path = Path.home() / ".config/ollama/performance.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.setup_database()
        
        # Verify host.docker.internal resolution
        try:
            host_ip = socket.gethostbyname('host.docker.internal')
            console.print(f"[blue]host.docker.internal resolves to: {host_ip}[/]")
        except Exception as e:
            console.print("[red]Warning: Could not resolve host.docker.internal[/]")
            console.print(f"[red]Error: {str(e)}[/]")
        
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
                     avg_token_time REAL)''')
        conn.commit()
        conn.close()

    def check_ollama_connection(self):
        """Check if Ollama is accessible"""
        try:
            console.print(f"[yellow]Checking Ollama connection at {OLLAMA_API_URL}...[/]")
            response = requests.get(f"{OLLAMA_API_URL}/api/version")
            if response.status_code == 200:
                version = response.json().get('version', 'unknown')
                console.print(f"[green]Connected to Ollama version {version}[/]")
                return True
            else:
                console.print(f"[red]Unexpected status code: {response.status_code}[/]")
                return False
        except requests.exceptions.ConnectionError as e:
            console.print(f"[red]Connection Error: {str(e)}[/]")
            console.print("[yellow]Make sure Ollama is running on your host machine[/]")
            return False
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/]")
            return False

    def run_test(self, gpu_layers, batch_size, compute_threads):
        """Run a single performance test"""
        console.print(f"\n[bold blue]Running test with settings:[/]")
        console.print(f"GPU Layers: {gpu_layers}")
        console.print(f"Batch Size: {batch_size}")
        console.print(f"Compute Threads: {compute_threads}")

        # Check Ollama connection
        if not self.check_ollama_connection():
            console.print("[bold red]Error: Cannot connect to Ollama on host[/]")
            return None

        # Run test
        try:
            response = requests.post(
                f"{OLLAMA_API_URL}/api/generate",
                json={
                    "model": "deepseek-r1:7b",
                    "prompt": "Write a hello world in Python",
                    "options": {
                        "num_predict": 100,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "top_k": 10,
                        "num_gpu_layers": gpu_layers,
                        "num_threads": compute_threads,
                        "num_batch": batch_size
                    }
                }
            )
            
            # Handle streaming response
            last_metrics = None
            for line in response.text.strip().split('\n'):
                try:
                    data = json.loads(line)
                    if 'total_duration' in data:  # Only store the final metrics
                        last_metrics = data
                except json.JSONDecodeError:
                    continue
            
            if not last_metrics:
                console.print("[red]No metrics received from Ollama[/]")
                return None
                
            # Calculate metrics
            run_metrics = {
                'timestamp': datetime.now().isoformat(),
                'gpu_layers': gpu_layers,
                'batch_size': batch_size,
                'compute_threads': compute_threads,
                'total_duration': last_metrics['total_duration'] / 1e9,
                'load_duration': last_metrics['load_duration'] / 1e9,
                'prompt_eval_duration': last_metrics['prompt_eval_duration'] / 1e9,
                'eval_duration': last_metrics['eval_duration'] / 1e9,
                'tokens_per_second': last_metrics['eval_count'] / (last_metrics['eval_duration'] / 1e9),
                'avg_token_time': (last_metrics['eval_duration'] / last_metrics['eval_count']) / 1e6
            }

            # Create results table
            table = Table(title="Performance Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in run_metrics.items():
                if isinstance(value, float):
                    table.add_row(key, f"{value:.3f}")
                else:
                    table.add_row(key, str(value))
            
            console.print(table)

            # Save to database
            conn = sqlite3.connect(self.db_path)
            pd.DataFrame([run_metrics]).to_sql('performance_runs', conn, 
                                             if_exists='append', index=False)
            conn.close()

            return run_metrics
            
        except Exception as e:
            console.print(f"[bold red]Error during test:[/] {str(e)}")
            console.print(f"[yellow]Response text:[/] {response.text if 'response' in locals() else 'No response'}")
            return None

    def calculate_percentage_diff(self, current, best):
        """Calculate normalized percentage difference"""
        if best == 0:
            return float('inf')
        
        # Calculate raw percentage
        pct_diff = ((current - best) / best) * 100
        
        # Normalize large percentages using log scale
        if abs(pct_diff) > 20:
            sign = 1 if pct_diff > 0 else -1
            normalized_pct = 20 + (sign * 10 * np.log10(abs(pct_diff) / 20))
            return normalized_pct
        
        return pct_diff

    def format_metric_comparison(self, current, best, metric_name):
        """Format metric with comparison arrow and percentage"""
        if isinstance(current, (int, float)):
            pct_diff = self.calculate_percentage_diff(current, best)
            
            # For metrics where lower is better, invert the sign
            lower_is_better = metric_name in ['avg_token_time', 'total_duration', 'eval_duration', 
                                            'load_duration', 'prompt_eval_duration']
            if lower_is_better:
                pct_diff = -pct_diff
            
            return f"{current:.3f} ({pct_diff:+.1f}%)"
        return str(current)

    def calculate_performance_score(self, metrics, best_run):
        """Calculate overall performance score"""
        weights = {
            'tokens_per_second': 0.4,
            'avg_token_time': 0.3,
            'total_duration': 0.2,
            'eval_duration': 0.1
        }
        
        score = 0
        for metric, weight in weights.items():
            current = metrics[metric]
            best = best_run[metric]
            lower_is_better = metric in ['avg_token_time', 'total_duration', 'eval_duration']
            
            # Calculate normalized score (0-1, higher is better)
            if lower_is_better:
                score += weight * (best / current)
            else:
                score += weight * (current / best)
                
        return score * 100  # Convert to percentage

    def show_tables_and_history(self, metrics, output_widget):
        """Display tables and history graph side by side"""
        conn = sqlite3.connect(self.db_path)
        
        # Get data for plots
        all_runs = pd.read_sql_query("""
            SELECT * FROM performance_runs 
            ORDER BY tokens_per_second DESC
        """, conn)
        
        # Get historical data for performance graph
        history_data = pd.read_sql_query("""
            SELECT 
                timestamp,
                tokens_per_second 
            FROM performance_runs 
            ORDER BY datetime(timestamp) ASC
        """, conn)
        
        # Convert timestamps to datetime
        history_data['timestamp'] = pd.to_datetime(history_data['timestamp'])
        
        # Create performance history graph
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=history_data['timestamp'],
            y=history_data['tokens_per_second'],
            mode='lines+markers',
            name='Tokens/sec'
        ))
        
        # Get y-axis range from data
        y_min = history_data['tokens_per_second'].min() * 0.9  # Add 10% padding
        y_max = history_data['tokens_per_second'].max() * 1.1
        
        # Update Performance History graph height
        fig1.update_layout(
            height=300,  # Changed from 400 to 300
            width=620,
            margin=dict(l=40, r=20, t=2, b=40),
            xaxis_title="Time",
            yaxis_title="Tokens/sec",
            yaxis=dict(range=[y_min, y_max]),
            showlegend=False,
            template='plotly_white',
            autosize=False
        )
        
        # Create Configuration Impact 3D plot
        fig2 = px.scatter_3d(
            all_runs,
            x='gpu_layers',
            y='batch_size',
            z='compute_threads',
            color='tokens_per_second',
            size='tokens_per_second',
            color_continuous_scale=[
                [0, 'rgb(215, 48, 39)'],     # Dark red
                [0.2, 'rgb(253, 174, 97)'],   # Light red/orange
                [0.4, 'rgb(255, 255, 191)'],  # Yellow
                [0.6, 'rgb(166, 217, 106)'],  # Light green
                [0.8, 'rgb(26, 152, 80)']     # Dark green
            ]  # Custom scale with more contrast
        )

        fig2.update_layout(
            height=420,
            width=700,
            margin=dict(l=100, r=60, t=20, b=20),
            scene=dict(
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=2.0, y=2.0, z=2.0)
                ),
                xaxis=dict(title=dict(text="GPU Layers")),
                yaxis=dict(title=dict(text="Batch Size")),
                zaxis=dict(title=dict(text="Threads")),
                domain=dict(x=[0.05, 0.85]),
                aspectmode='cube'
            ),
            coloraxis=dict(
                colorbar=dict(
                    x=0.94,
                    xanchor='right',
                    yanchor='middle',
                    y=0.5,
                    len=0.7,
                    thickness=20,
                    title=dict(text="Tokens/sec"),
                    outlinewidth=0
                )
            )
        )
        
        # Create Metric Correlations plot
        fig3 = px.scatter_matrix(
            all_runs,
            dimensions=['tokens_per_second', 'avg_token_time', 'total_duration'],
            color='tokens_per_second',
            color_continuous_scale='RdYlGn',
            labels={
                'tokens_per_second': 'Tokens/sec',
                'avg_token_time': 'Token Time (ms)',
                'total_duration': 'Total Time (s)'
            }
        )
        
        # Create Performance Trends plot (new)
        fig4 = make_subplots(rows=1, cols=3,
            subplot_titles=("GPU Layers", "Batch Size", "Threads"),
            horizontal_spacing=0.1
        )
        
        # GPU Layers trend
        fig4.add_trace(
            go.Scatter(
                x=all_runs['gpu_layers'],
                y=all_runs['tokens_per_second'],
                mode='markers',
                name='GPU Layers',
                marker=dict(
                    color=all_runs['tokens_per_second'],
                    colorscale='RdYlGn',
                    showscale=False
                )
            ),
            row=1, col=1
        )
        
        # Batch Size trend
        fig4.add_trace(
            go.Scatter(
                x=all_runs['batch_size'],
                y=all_runs['tokens_per_second'],
                mode='markers',
                name='Batch Size',
                marker=dict(
                    color=all_runs['tokens_per_second'],
                    colorscale='RdYlGn',
                    showscale=False
                )
            ),
            row=1, col=2
        )
        
        # Compute Threads trend
        fig4.add_trace(
            go.Scatter(
                x=all_runs['compute_threads'],
                y=all_runs['tokens_per_second'],
                mode='markers',
                name='Threads',
                marker=dict(
                    color=all_runs['tokens_per_second'],
                    colorscale='RdYlGn',
                    showscale=False
                )
            ),
            row=1, col=3
        )
        
        # Update Performance Trends plot layout
        fig4.update_layout(
            height=400,
            width=500,
            showlegend=False,
            margin=dict(l=40, r=20, t=30, b=40),
            font=dict(family="Arial, sans-serif", size=12),
            annotations=[
                dict(x=ann.x, y=ann.y, text=ann.text, 
                     showarrow=False, 
                     font=dict(family="Arial, sans-serif", size=12),
                     yshift=10,  # Move titles up
                     yref='paper')  # Reference to the paper coordinates
                for ann in fig4.layout.annotations
            ]
        )
        
        # Update axes for all subplots
        for i in range(1, 4):
            fig4.update_xaxes(
                row=1, 
                col=i,
                tickmode='linear',  # Force linear tick mode
                dtick=5 if i == 1 else (256 if i == 2 else 2),  # Custom tick intervals
                showgrid=True
            )
            fig4.update_yaxes(
                row=1,
                col=i,
                range=[0, max(all_runs['tokens_per_second']) * 1.1],  # Set consistent y-axis range
                title_text="Tokens/sec" if i == 1 else None  # Only show y-axis title on first plot
            )
        
        # Get best run and create tables (existing code)
        best_run = pd.read_sql_query("""
            SELECT * FROM performance_runs 
            ORDER BY tokens_per_second DESC 
            LIMIT 1
        """, conn)
        
        # Create configuration table with renamed header
        config_df = pd.DataFrame({
            'Parameter': ['GPU Layers', 'Batch Size', 'Compute Threads'],
            'Current': [  # Changed from 'Value' to 'Current'
                metrics['gpu_layers'],
                metrics['batch_size'],
                metrics['compute_threads']
            ],
            'Best': [
                int(best_run['gpu_layers'].iloc[0]),
                int(best_run['batch_size'].iloc[0]),
                int(best_run['compute_threads'].iloc[0])
            ]
        })
        
        # Calculate config differences
        config_df['Difference'] = config_df.apply(
            lambda row: f"{row['Current'] - row['Best']:+d}",
            axis=1
        )
        
        # Create performance metrics table with separate columns and arrows
        metric_mapping = {
            'Tokens/Second': 'tokens_per_second',
            'Avg Token Time (ms)': 'avg_token_time',
            'Total Duration (s)': 'total_duration',
            'Load Duration (s)': 'load_duration',
            'Prompt Eval Duration (s)': 'prompt_eval_duration',
            'Eval Duration (s)': 'eval_duration'
        }
        
        performance_data = {
            'Metric': list(metric_mapping.keys()),
            'Current': [metrics[metric_mapping[m]] for m in metric_mapping.keys()],
            'Best': [
                best_run['tokens_per_second'].iloc[0],
                best_run['avg_token_time'].iloc[0],
                best_run['total_duration'].iloc[0],
                best_run['load_duration'].iloc[0],
                best_run['prompt_eval_duration'].iloc[0],
                best_run['eval_duration'].iloc[0]
            ],
            'Difference': []  # Will be filled below
        }
        
        # Calculate differences and arrows separately
        arrows = []
        for idx, row in enumerate(metric_mapping.keys()):
            current = performance_data['Current'][idx]
            best = performance_data['Best'][idx]
            lower_is_better = row in ['Avg Token Time (ms)', 'Total Duration (s)', 'Load Duration (s)', 'Prompt Eval Duration (s)', 'Eval Duration (s)']
            
            # Calculate percentage difference relative to best
            if lower_is_better:
                # For metrics where lower is better
                pct_diff = ((best - current) / best) * 100
                is_better = current < best
            else:
                # For metrics where higher is better
                pct_diff = ((current - best) / best) * 100
                is_better = current > best
            
            performance_data['Difference'].append(f"{pct_diff:+.1f}%")
            arrows.append(f'<span style="color: {("green" if is_better else "red")}">{("↑" if is_better else "↓")}</span>')

        # Create DataFrame with consistent formatting
        df = pd.DataFrame(performance_data)
        
        # Get top 10 best runs
        top_runs = pd.read_sql_query("""
            SELECT * FROM performance_runs 
            ORDER BY tokens_per_second DESC 
            LIMIT 10
        """, conn)

        # Simplify the HTML/CSS structure first
        html_content = f"""
            <style>
                .main-grid {{
                    width: 1000px;
                    margin: 0;
                    display: grid;
                    grid-template-columns: 420px 420px;
                    grid-column-gap: 70px;
                    font-family: Arial, sans-serif;
                }}
                .table-container {{
                    height: 300px;  /* Fixed height to match table */
                    position: relative;
                }}
                .perf-table th, 
                .perf-table td {{
                    padding: 6px 6px;
                    text-align: left !important;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                .color-bar-container {{
                    width: auto;
                    margin-left: 350px;
                }}
                .color-bar {{
                    width: 20px;
                    position: absolute;
                    top: 27px;
                    bottom: 0;
                    background: linear-gradient(to bottom,
                        rgb(26, 152, 80),
                        rgb(166, 217, 106),
                        rgb(255, 255, 191),
                        rgb(253, 174, 97),
                        rgb(215, 48, 39)
                    );
                }}
                .color-bar-label {{
                    position: absolute;
                    right: 25px;
                    font-size: 10px;
                    white-space: nowrap;
                    width: 16px;
                }}
                .section-title {{
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    margin: 0 0 10px 0;
                    text-align: left;
                    margin-top: 16px;
                }}
                .content-row {{
                    margin: 0 0 20px 0;
                }}
                .graph-container {{
                    width: 700px;
                    margin-left: -170px;
                    overflow-y: hidden;
                    overflow-x: hidden;
                }}
                .history-graph-container {{
                    width: 620px;
                    margin-left: -15px;
                    overflow: visible;
                    padding: 0;
                }}
                .full-width-section {{
                    grid-column: 1 / -1;
                    width: 100%;
                    margin-top: 20px;
                }}
                .top-runs-table {{
                    padding-left: 0px;
                }}
                .top-runs-table th:nth-child(5), 
                .top-runs-table td:nth-child(5) {{ 
                    width: 100px;
                    display: table-cell;
                }}
            </style>
        """

        # Create HTML layout with two-column grid structure
        html_content += f"""
            <div class="main-grid">
                <!-- Row 1: Tables and History Graph -->
                <div>
                    <div class="section-title">Performance Metrics</div>
                    <div class="table-container content-row">
                        <div style="position: relative;">
                            <table class="perf-table">
                                <thead>
                                    <tr>
                                        <th>Parameter</th>
                                        <th>Current</th>
                                        <th>Best</th>
                                        <th>Difference</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>GPU Layers</td>
                                        <td>{metrics['gpu_layers']}</td>
                                        <td>{int(best_run['gpu_layers'].iloc[0])}</td>
                                        <td style="background: {self.get_gradient_color(metrics['gpu_layers'] - best_run['gpu_layers'].iloc[0], -10, 10)}">
                                            {int(metrics['gpu_layers'] - best_run['gpu_layers'].iloc[0]):+d}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Batch Size</td>
                                        <td>{metrics['batch_size']}</td>
                                        <td>{int(best_run['batch_size'].iloc[0])}</td>
                                        <td style="background: {self.get_gradient_color(metrics['batch_size'] - best_run['batch_size'].iloc[0], -10, 10)}">
                                            {int(metrics['batch_size'] - best_run['batch_size'].iloc[0]):+d}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>Compute Threads</td>
                                        <td>{metrics['compute_threads']}</td>
                                        <td>{int(best_run['compute_threads'].iloc[0])}</td>
                                        <td style="background: {self.get_gradient_color(metrics['compute_threads'] - best_run['compute_threads'].iloc[0], -10, 10)}">
                                            {int(metrics['compute_threads'] - best_run['compute_threads'].iloc[0]):+d}
                                        </td>
                                    </tr>
                                    <tr style="background-color: #f5f5f5;">
                                        <td colspan="4" style="padding: 8px; font-weight: bold;">Metrics</td>
                                    </tr>
                                    {''.join(f"""
                                        <tr>
                                            <td>{row['Metric']}</td>
                                            <td>{row['Current']:.3f}</td>
                                            <td>{row['Best']:.3f}</td>
                                            <td style="background: {self.get_gradient_color(float(row['Difference'].strip('%+').strip(')')), -20, 20)}">
                                                {row['Difference']}
                                            </td>
                                        </tr>
                                    """ for i, row in df.iterrows())}
                                </tbody>
                            </table>
                            <div class="color-bar-container">
                                <div class="color-bar"></div>
                                <span class="color-bar-label" style="top: 37px;">100%</span>
                                <span class="color-bar-label" style="top: 50%;">50%</span>
                                <span class="color-bar-label" style="bottom: 0;">0%</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div class="section-title">Top Performance Runs</div>
                    <div style="margin-left: 20px;">  <!-- Add margin to container -->
                        <table class="perf-table top-runs-table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>GPU Layers</th>
                                    <th>Batch Size</th>
                                    <th>Threads</th>
                                    <th>Tokens/sec</th>
                                    <th>Token Time</th>
                                    <th>Total Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(f"""
                                    <tr>
                                        <td>{datetime.strptime(row['timestamp'].replace('T', ' '), '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M')}</td>
                                        <td>{row['gpu_layers']}</td>
                                        <td>{row['batch_size']}</td>
                                        <td>{row['compute_threads']}</td>
                                        <td>{row['tokens_per_second']:.3f}</td>
                                        <td>{row['avg_token_time']:.3f}</td>
                                        <td>{row['total_duration']:.3f}</td>
                                    </tr>
                                """ for _, row in top_runs.iterrows())}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- Row 2: Impact and History -->
                <div>
                    <div class="section-title">Configuration Impact</div>
                    <div class="graph-container content-row config-3d-graph">
                        {fig2.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                </div>
                
                <div>
                    <div class="section-title">Performance History</div>
                    <div class="history-graph-container content-row">
                        {fig1.to_html(full_html=False, include_plotlyjs='cdn')}
                    </div>
                </div>
            </div>

            <!-- Full Width Correlations Section -->
            <div class="full-width-section">
                <div class="section-title">Metric Correlations</div>
                {fig3.update_layout(
                    height=500,
                    width=1110,  # Match exact width of the two tables + gap
                    margin=dict(l=50, r=50, t=20, b=50),
                    showlegend=False
                ).to_html(full_html=False, include_plotlyjs='cdn')}
            </div>
        """
        
        # Remove the padding from the container div
        html_content = html_content.replace('style="padding-right: 20px;"', '')

        # Add CSS for the 3D graph specifically
        html_content = html_content.replace(
            '.graph-container {',
            '''
                .config-3d-graph > div {
                    margin-top: -80px !important;  /* Force top margin for 3D graph */
                }
                .graph-container {
                    width: 700px;
                    margin-left: -170px;
                    overflow-y: hidden;
                    overflow-x: hidden;
                }
            '''
        )

        # Update section title style
        html_content = html_content.replace(
            '.section-title {',
            '''
                .section-title {
                    font-family: Arial, sans-serif;
                    font-size: 16px;
                    margin: 0 0 10px 0;
                    text-align: left;
                    margin-top: 16px;
                }
            '''
        )

        # Single display call with complete layout
        display(HTML(html_content))
        
        conn.close()

    def show_comparison(self, metrics):
        """Original method now calls only tables and history"""
        self.show_tables_and_history(metrics)

    def generate_recommendations(self, all_runs, current_metrics):
        """Generate configuration recommendations based on historical data"""
        recommendations = []
        
        # Analyze GPU layers impact
        best_gpu = all_runs.nlargest(3, 'tokens_per_second')['gpu_layers'].mode()[0]
        if current_metrics['gpu_layers'] != best_gpu:
            recommendations.append(
                f"Consider adjusting GPU layers to {best_gpu} "
                f"(current: {current_metrics['gpu_layers']})"
            )
        
        # Analyze batch size impact
        best_batch = all_runs.nlargest(3, 'tokens_per_second')['batch_size'].mode()[0]
        if current_metrics['batch_size'] != best_batch:
            recommendations.append(
                f"Try batch size of {best_batch} "
                f"(current: {current_metrics['batch_size']})"
            )
        
        # Analyze thread count impact
        best_threads = all_runs.nlargest(3, 'tokens_per_second')['compute_threads'].mode()[0]
        if current_metrics['compute_threads'] != best_threads:
            recommendations.append(
                f"Experiment with {best_threads} compute threads "
                f"(current: {current_metrics['compute_threads']})"
            )
        
        return recommendations

    def get_gradient_color(self, diff, min_diff=-100, max_diff=100):
        """Get gradient color based on difference"""
        # Normalize difference to -1 to 1 scale with non-linear scaling
        norm_diff = np.clip(diff / max(abs(min_diff), abs(max_diff)), -1, 1)
        # Apply exponential scaling to increase color contrast
        norm_diff = np.sign(norm_diff) * (abs(norm_diff) ** 0.5)
        
        if norm_diff > 0:
            # Green gradient for positive
            return f'rgba(26, 152, 80, {abs(norm_diff)})'
        else:
            # Red gradient for negative
            return f'rgba(215, 48, 39, {abs(norm_diff)})'

def main():
    parser = argparse.ArgumentParser(description='Ollama Performance Profiler')
    parser.add_argument('--gpu-layers', type=int, default=35,
                      help='Number of GPU layers (default: 35)')
    parser.add_argument('--batch-size', type=int, default=1024,
                      help='Batch size (default: 1024)')
    parser.add_argument('--compute-threads', type=int, default=8,
                      help='Number of compute threads (default: 8)')
    
    args = parser.parse_args()
    
    profiler = OllamaProfiler()
    profiler.run_test(args.gpu_layers, args.batch_size, args.compute_threads)

if __name__ == "__main__":
    main()

