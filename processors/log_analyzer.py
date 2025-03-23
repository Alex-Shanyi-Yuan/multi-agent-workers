import os
import re
import gzip
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator, Tuple, Union
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from collections import defaultdict
from scipy import stats

logger = logging.getLogger(__name__)

class LogAnalyzer:
    """Advanced analyzer for processing log files with anomaly detection and trend analysis."""
    
    def __init__(self, log_pattern: Optional[str] = None):
        """Initialize the log analyzer.
        
        Args:
            log_pattern: Custom regex pattern for log entries. If None, uses default.
        """
        self.log_pattern = log_pattern or os.getenv(
            "LOG_PATTERN",
            r'\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s*'
            r'(?P<level>ERROR|WARN|INFO|DEBUG)\s*-\s*'
            r'(?P<message>.*?)(?=\n\[|$)'
        )
        self.compiled_pattern = re.compile(self.log_pattern, re.MULTILINE | re.DOTALL)
        
    def process_log_file(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """Process a single log file (plain text or gzipped).
        
        Args:
            file_path: Path to the log file
            
        Yields:
            Dict containing parsed log entry information
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
            
        # Determine if file is gzipped
        is_gzipped = path.suffix == '.gz'
        
        # Open file with appropriate method
        opener = gzip.open if is_gzipped else open
        with opener(file_path, 'rt', encoding='utf-8') as f:
            content = f.read()
            
        # Process log entries
        for match in self.compiled_pattern.finditer(content):
            entry = match.groupdict()
            if 'timestamp' in entry:
                entry['timestamp'] = pd.to_datetime(entry['timestamp'])
            yield entry
            
    def analyze_logs(
        self,
        log_dir: str,
        time_range: Optional[str] = None,
        error_types: Optional[List[str]] = None,
        max_depth: int = 5,
        detect_anomalies: bool = True,
        analyze_trends: bool = True,
        find_correlations: bool = True,
        predict_errors: bool = True
    ) -> Dict[str, Any]:
        """Analyze log files in a directory.
        
        Args:
            log_dir: Directory containing log files
            time_range: Time range to analyze (e.g., '1d', '1w', '1h')
            error_types: List of error types to focus on
            max_depth: Maximum depth for nested log analysis
            
        Returns:
            Dict containing analysis results
        """
        # Set default values
        error_types = error_types or ["ERROR", "WARN"]
        
        # Calculate time range
        start_time = None
        if time_range:
            end_time = datetime.now()
            if time_range.endswith('d'):
                days = int(time_range[:-1])
                start_time = end_time - timedelta(days=days)
            elif time_range.endswith('w'):
                weeks = int(time_range[:-1])
                start_time = end_time - timedelta(weeks=weeks)
            elif time_range.endswith('h'):
                hours = int(time_range[:-1])
                start_time = end_time - timedelta(hours=hours)
                
        # Find log files
        log_dir_path = Path(log_dir)
        log_files = []
        for ext in ['.log', '.log.gz']:
            log_files.extend(log_dir_path.rglob(f'*{ext}'))
            
        # Process log files
        entries = []
        error_counts = defaultdict(int)
        patterns = []
        total_entries = 0
        
        for log_file in tqdm(log_files, desc="Processing log files"):
            try:
                for entry in self.process_log_file(str(log_file)):
                    total_entries += 1
                    
                    # Apply time range filter
                    if start_time and entry['timestamp'] < start_time:
                        continue
                        
                    entries.append(entry)
                    if entry['level'] in error_types:
                        error_counts[entry['level']] += 1
                        
            except Exception as e:
                logger.error(f"Error processing {log_file}: {str(e)}")
                
        # Convert entries to DataFrame for analysis
        df = pd.DataFrame(entries)
        
        # Basic analysis
        results = {
            'total_entries': total_entries,
            'error_counts': dict(error_counts),
            'patterns': patterns,
            'summary': 'No matching log entries found.' if not entries else 'Analysis complete.',
            'time_range': {
                'start': df['timestamp'].min() if not df.empty else None,
                'end': df['timestamp'].max() if not df.empty else None
            }
        }
        
        # Advanced analysis if data is available
        if not df.empty and len(df) > 1:
            if detect_anomalies:
                results['anomalies'] = self.detect_anomalies(df)
            if analyze_trends:
                results['trends'] = self.analyze_trends(df)
            if find_correlations:
                results['correlations'] = self.find_correlated_events(df)
            if predict_errors:
                results['predictions'] = self.error_prediction(df)
                
        return results
        
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in log patterns.
        
        Args:
            df: DataFrame containing log entries
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        try:
            # Group by hour and level
            hourly_counts = df.groupby([pd.Grouper(key='timestamp', freq='H'), 'level']).size()
            
            # Calculate z-scores for each level
            for level in df['level'].unique():
                level_counts = hourly_counts.xs(level, level=1)
                if len(level_counts) > 1:  # Need at least 2 points for z-score
                    z_scores = stats.zscore(level_counts)
                    anomaly_hours = level_counts.index[abs(z_scores) > 2]
                    
                    for hour in anomaly_hours:
                        anomalies.append({
                            'timestamp': hour,
                            'level': level,
                            'count': level_counts[hour],
                            'z_score': z_scores[level_counts.index.get_loc(hour)]
                        })
                        
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            
        return anomalies
        
    def analyze_trends(self, df: pd.DataFrame, grouping: str = 'h') -> Dict[str, Any]:
        """Analyze trends in log patterns.
        
        Args:
            df: DataFrame containing log entries
            grouping: Time grouping (h=hourly, D=daily)
            
        Returns:
            Dict containing trend analysis results
        """
        try:
            # Set timestamp as index for proper time series analysis
            df = df.set_index('timestamp')
            
            # Group by time and level
            grouped = df.groupby(
                [pd.Grouper(freq=grouping), 'level']
            ).size().unstack(fill_value=0)
            
            # Calculate time series data
            time_series = grouped.to_dict()
            
            # Calculate growth rates
            growth_rates = {}
            for level in grouped.columns:
                series = grouped[level]
                if len(series) > 1:
                    growth = (series.iloc[-1] - series.iloc[0]) / series.iloc[0] if series.iloc[0] != 0 else 0
                    growth_rates[level] = growth
                    
            return {
                'time_series': time_series,
                'growth_rates': growth_rates
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {}
            
    def find_correlated_events(self, df: pd.DataFrame, window: str = '5min') -> List[Dict[str, Any]]:
        """Find correlated events in logs.
        
        Args:
            df: DataFrame containing log entries
            window: Time window for correlation
            
        Returns:
            List of correlated event patterns
        """
        correlations = []
        try:
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Find error sequences
            error_events = df[df['level'] == 'ERROR']
            for i in range(len(error_events)-1):
                current = error_events.iloc[i]
                next_error = error_events.iloc[i+1]
                
                # Check if errors are within the time window
                if (next_error['timestamp'] - current['timestamp']) <= pd.Timedelta(window):
                    correlations.append({
                        'component1': current['component'],
                        'component2': next_error['component'],
                        'message1': current['message'],
                        'message2': next_error['message'],
                        'time_diff': (next_error['timestamp'] - current['timestamp']).total_seconds()
                    })
                    
        except Exception as e:
            logger.error(f"Error finding correlations: {str(e)}")
            
        return correlations
        
    def predict_error_likelihood(self, df: pd.DataFrame, component: str) -> Dict[str, Any]:
        """Predict error likelihood for a specific component.
        
        Args:
            df: DataFrame containing log entries
            component: Component to analyze
            
        Returns:
            Dict containing error prediction results
        """
        try:
            # Filter for the specific component
            component_df = df[df['component'] == component]
            
            if len(component_df) < 2:
                return {
                    'error_likelihood': 0.0,
                    'confidence_score': 0.0
                }
                
            # Calculate error rate
            error_count = len(component_df[component_df['level'] == 'ERROR'])
            total_count = len(component_df)
            error_rate = error_count / total_count
            
            # Calculate time-based patterns
            timestamps = component_df[component_df['level'] == 'ERROR']['timestamp']
            if len(timestamps) > 1:
                intervals = np.diff(timestamps.astype(np.int64)) / 1e9  # Convert to seconds
                std_interval = np.std(intervals)
                confidence = 1.0 / (1.0 + std_interval / 3600)  # Higher confidence for consistent intervals
            else:
                confidence = 0.5
                
            return {
                'error_likelihood': error_rate,
                'confidence_score': confidence
            }
            
        except Exception as e:
            logger.error(f"Error predicting likelihood: {str(e)}")
            return {
                'error_likelihood': 0.0,
                'confidence_score': 0.0
            }
