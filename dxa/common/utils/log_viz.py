"""Visualization utilities for DXA log analysis.

This module provides visualization tools for analyzing LLM interaction patterns.
It requires optional dependencies: matplotlib, seaborn, and pandas.

Basic Usage:
    # Create visualizer
    visualizer = LLMInteractionVisualizer("path/to/logs")

    # Create individual plots
    visualizer.plot_token_usage("token_usage.png")
    visualizer.plot_response_times("response_times.png")
    visualizer.plot_success_rate_by_phase("success_rates.png")

    # Create comprehensive dashboard
    visualizer.create_dashboard("dashboard/")

Note: Install visualization dependencies with:
    pip install matplotlib seaborn pandas
"""

from typing import Optional
from pathlib import Path
from dxa.common.utils.log_analysis import LLMInteractionAnalyzer

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False

def require_viz(func):
    """Decorator to check if visualization dependencies are available."""
    def wrapper(*args, **kwargs):
        if not VIZ_AVAILABLE:
            raise ImportError(
                "matplotlib, seaborn, and pandas are required for visualization. "
                "Install them with: pip install matplotlib seaborn pandas"
            )
        return func(*args, **kwargs)
    return wrapper

class LLMInteractionVisualizer:
    """Visualize LLM interaction patterns."""

    def __init__(self, log_dir: str):
        """Initialize visualizer."""
        if not VIZ_AVAILABLE:
            raise ImportError(
                "matplotlib, seaborn, and pandas are required for visualization. "
                "Install them with: pip install matplotlib seaborn pandas"
            )
        self.analyzer = LLMInteractionAnalyzer(log_dir)

    @require_viz
    def plot_token_usage(
        self,
        save_path: Optional[str] = None
    ):
        """Plot token usage over time."""
        token_usage = self.analyzer.get_token_usage_over_time()
        if token_usage.empty:
            print("No token usage data available")
            return

        plt.figure(figsize=(12, 6))
        sns.lineplot(data=token_usage)
        plt.title('Token Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Tokens Used')
        plt.xticks(rotation=45)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        plt.close()

    def plot_response_times(
        self,
        save_path: Optional[str] = None
    ):
        """Plot distribution of response times."""
        df = self.analyzer.load_interactions()
        if df.empty:
            print("No response time data available")
            return

        response_times = df['metadata'].apply(
            lambda x: float(x.get('duration_ms', 0)) if isinstance(x, dict) else 0.0
        )

        plt.figure(figsize=(10, 6))
        sns.histplot(response_times, bins=50)
        plt.title('Distribution of Response Times')
        plt.xlabel('Response Time (ms)')
        plt.ylabel('Count')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        plt.close()

    def plot_success_rate_by_phase(
        self,
        save_path: Optional[str] = None
    ):
        """Plot success rates across different phases."""
        df = self.analyzer.load_interactions()
        if df.empty:
            print("No phase data available")
            return

        # Convert success to numeric
        df['success_num'] = df['success'].astype(int)

        # Get phase from metadata
        df['phase'] = df['metadata'].apply(
            lambda x: x.get('phase', 'unknown') if isinstance(x, dict) else 'unknown'
        )

        # Create success rate crosstab
        success_by_phase = pd.crosstab(
            df['phase'],
            df['success_num']
        )

        plt.figure(figsize=(10, 6))
        success_by_phase.plot(kind='bar', stacked=True)
        plt.title('Success Rate by Phase')
        plt.xlabel('Phase')
        plt.ylabel('Count')
        plt.legend(['Failed', 'Successful'])
        plt.xticks(rotation=45)

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        plt.close()

    def plot_error_types(
        self,
        save_path: Optional[str] = None
    ):
        """Plot distribution of error types."""
        df = self.analyzer.load_interactions()
        if df.empty:
            print("No error data available")
            return

        error_types = df[df['interaction_type'] == 'error']['error'].value_counts()

        if error_types.empty:
            print("No errors found in the logs")
            return

        plt.figure(figsize=(12, 6))
        sns.barplot(x=error_types.values, y=error_types.index)
        plt.title('Distribution of Error Types')
        plt.xlabel('Count')
        plt.ylabel('Error Type')

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
        plt.close()

    def create_dashboard(
        self,
        save_dir: Optional[str] = None
    ):
        """Create a comprehensive dashboard of visualizations."""
        df = self.analyzer.load_interactions()
        if df.empty:
            print("No data available for dashboard")
            return

        plt.style.use('seaborn')
        plt.figure(figsize=(20, 15))

        # Token usage over time
        ax1 = plt.subplot(2, 2, 1)
        token_usage = self.analyzer.get_token_usage_over_time()
        if not token_usage.empty:
            sns.lineplot(data=token_usage, ax=ax1)
        ax1.set_title('Token Usage Over Time')
        ax1.tick_params(axis='x', rotation=45)

        # Response time distribution
        ax2 = plt.subplot(2, 2, 2)
        response_times = df['metadata'].apply(
            lambda x: float(x.get('duration_ms', 0)) if isinstance(x, dict) else 0.0
        )
        sns.histplot(response_times, bins=50, ax=ax2)
        ax2.set_title('Response Time Distribution')

        # Success rate by phase
        ax3 = plt.subplot(2, 2, 3)
        df['success_num'] = df['success'].astype(int)
        df['phase'] = df['metadata'].apply(
            lambda x: x.get('phase', 'unknown') if isinstance(x, dict) else 'unknown'
        )
        success_by_phase = pd.crosstab(df['phase'], df['success_num'])
        success_by_phase.plot(kind='bar', stacked=True, ax=ax3)
        ax3.set_title('Success Rate by Phase')
        ax3.tick_params(axis='x', rotation=45)

        # Error types
        ax4 = plt.subplot(2, 2, 4)
        error_types = df[df['interaction_type'] == 'error']['error'].value_counts()
        if not error_types.empty:
            sns.barplot(x=error_types.values, y=error_types.index, ax=ax4)
        ax4.set_title('Error Types')

        plt.tight_layout()

        if save_dir:
            plt.savefig(Path(save_dir) / 'dashboard.png', bbox_inches='tight')
        plt.close()

    def get_token_usage_over_time(self) -> pd.DataFrame:
        """Get token usage over time."""
        return self.analyzer.get_token_usage_over_time()
