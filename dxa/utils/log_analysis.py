"""Log analysis utilities for DXA."""

from typing import Dict, List
from datetime import datetime
from pathlib import Path
import json

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class LLMInteractionAnalyzer:
    """Analyze LLM interactions from logs."""
    
    def __init__(self, log_dir: str):
        """Initialize analyzer with log directory."""
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for log analysis. "
                "Install it with: pip install pandas"
            )
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / 'dxa.log'

    def _safe_get_usage(self, row: Dict) -> int:
        """Safely extract token usage from a log entry."""
        try:
            if 'response' in row and isinstance(row['response'], dict):
                usage = row['response'].get('usage', {})
                if isinstance(usage, dict):
                    return usage.get('total_tokens', 0)
            return 0
        except (KeyError, ValueError):
            return 0

    def load_interactions(self) -> pd.DataFrame:
        """Load LLM interactions into a pandas DataFrame."""
        interactions = []
        
        try:
            with open(self.log_file, encoding='utf-8') as f:
                for line in f:
                    try:
                        log = json.loads(line)
                        # Create a clean record with required fields
                        record = {
                            'timestamp': datetime.fromisoformat(log.get('timestamp', datetime.now().isoformat())),
                            'token_usage': self._safe_get_usage(log),
                            'success': log.get('success', False),
                            'interaction_type': log.get('interaction_type', 'unknown'),
                            'error': log.get('error'),
                            'metadata': log.get('metadata', {}),
                            'content': log.get('content', ''),
                            'response': log.get('response', {})
                        }
                        interactions.append(record)
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        print(f"Error parsing log line: {e}")
                        continue
                        
            # Create DataFrame with explicit columns
            df = pd.DataFrame(interactions, columns=[
                'timestamp',
                'token_usage',
                'success',
                'interaction_type',
                'error',
                'metadata',
                'content',
                'response'
            ])
            
            # Ensure timestamp is datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df
            
        except FileNotFoundError:
            print(f"Log file not found: {self.log_file}")
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=[
                'timestamp',
                'token_usage',
                'success',
                'interaction_type',
                'error',
                'metadata',
                'content',
                'response'
            ])

    def get_interaction_stats(self) -> Dict:
        """Get basic statistics about LLM interactions."""
        df = self.load_interactions()
        
        if df.empty:
            return {
                "total_interactions": 0,
                "success_rate": 0.0,
                "error_rate": 0.0,
                "average_tokens": 0.0,
                "most_common_errors": {},
                "interactions_by_phase": {}
            }
        
        stats = {
            "total_interactions": len(df),
            "success_rate": df['success'].mean(),
            "error_rate": (df['interaction_type'] == 'error').mean(),
            "average_tokens": df['token_usage'].mean()
        }
            
        # Safely get error types
        try:
            error_counts = df[
                (df['interaction_type'] == 'error') & 
                (df['error'].notna())
            ]['error'].value_counts().head()
            stats["most_common_errors"] = error_counts.to_dict()
        except (KeyError, ValueError):
            stats["most_common_errors"] = {}
            
        # Safely get phase counts
        try:
            phase_counts = df['metadata'].apply(
                lambda x: x.get('phase', 'unknown') if isinstance(x, dict) else 'unknown'
            ).value_counts()
            stats["interactions_by_phase"] = phase_counts.to_dict()
        except (KeyError, ValueError):
            stats["interactions_by_phase"] = {}
        
        return stats

    def get_token_usage_over_time(self) -> pd.DataFrame:
        """Analyze token usage over time."""
        df = self.load_interactions()
        if df.empty:
            return pd.DataFrame(columns=['token_usage'])
        return df.set_index('timestamp')['token_usage'].resample('1H').sum()

    def get_response_times(self) -> pd.Series:
        """Analyze LLM response times."""
        df = self.load_interactions()
        if df.empty:
            return pd.Series()
        return df['metadata'].apply(
            lambda x: x.get('duration_ms', 0) if isinstance(x, dict) else 0
        ).describe()

    def find_similar_prompts(self, prompt: str, threshold: float = 0.8) -> List[Dict]:
        """Find similar prompts in the logs using fuzzy matching."""
        from difflib import SequenceMatcher
        
        df = self.load_interactions()
        similar_prompts = []
        
        for _, row in df.iterrows():
            if 'prompt' in row:
                similarity = SequenceMatcher(
                    None, 
                    prompt.lower(), 
                    row['prompt'].lower()
                ).ratio()
                
                if similarity >= threshold:
                    similar_prompts.append({
                        'timestamp': row['timestamp'],
                        'prompt': row['prompt'],
                        'similarity': similarity,
                        'response': row.get('response', {}).get('content')
                    })
                    
        return sorted(similar_prompts, key=lambda x: x['similarity'], reverse=True)

    def get_prompt_patterns(self) -> Dict:
        """Analyze common patterns in prompts."""
        from collections import Counter
        import re
        
        df = self.load_interactions()
        patterns = Counter()
        
        for prompt in df['prompt']:
            # Extract key phrases or patterns
            key_phrases = re.findall(r'\b\w+\s+\w+\s+\w+\b', prompt.lower())
            patterns.update(key_phrases)
            
        return {
            "common_patterns": patterns.most_common(10),
            "average_prompt_length": df['prompt'].str.len().mean(),
            "prompt_complexity": df['prompt'].apply(lambda x: len(x.split()))
        }

    def export_report(self, output_file: str):
        """Generate a comprehensive analysis report."""
        stats = self.get_interaction_stats()
        token_usage = self.get_token_usage_over_time()
        response_times = self.get_response_times()
        patterns = self.get_prompt_patterns()
        
        report = {
            "summary": stats,
            "token_usage": token_usage.to_dict(),
            "response_times": response_times.to_dict(),
            "prompt_patterns": patterns
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str) 