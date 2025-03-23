import unittest
from pathlib import Path
import os
from processors.log_analyzer import LogAnalyzer
import pandas as pd
from datetime import datetime, timedelta

class TestLogAnalyzer(unittest.TestCase):
    def setUp(self):
        self.log_analyzer = LogAnalyzer()
        self.assets_dir = Path(__file__).parent.parent.parent / 'assets'
        
    def test_process_log_file(self):
        """Test basic log file processing"""
        log_file = self.assets_dir / 'intro.log'
        entries = list(self.log_analyzer.process_log_file(str(log_file)))
        
        self.assertTrue(len(entries) > 0)
        self.assertEqual(entries[0]['level'], 'INFO')
        self.assertEqual(entries[0]['component'], 'Application')
        
        # Check error entry
        error_entry = next(e for e in entries if e['level'] == 'ERROR')
        self.assertIn('Processing failed', error_entry['message'])
        self.assertIn('request_id=879345', error_entry['message'])
        
    def test_analyze_logs(self):
        """Test full log analysis functionality"""
        results = self.log_analyzer.analyze_logs(str(self.assets_dir))
        
        # Basic assertions
        self.assertIn('error_counts', results)
        self.assertIn('total_entries', results)
        self.assertIn('patterns', results)
        
        # Check error counts
        self.assertGreater(results['error_counts'].get('ERROR', 0), 0)
        
        # Check time range
        self.assertIn('time_range', results)
        self.assertTrue(isinstance(results['time_range']['start'], pd.Timestamp))
        
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        # Create test DataFrame
        df = pd.DataFrame([
            {'timestamp': datetime.now() - timedelta(minutes=i), 
             'level': 'ERROR' if i % 30 == 0 else 'INFO',
             'component': 'TestComponent',
             'message': f'Test message {i}'}
            for i in range(120)
        ])
        
        anomalies = self.log_analyzer.detect_anomalies(df)
        self.assertIsInstance(anomalies, list)
        
    def test_analyze_trends(self):
        """Test trend analysis"""
        # Create test DataFrame with known patterns
        df = pd.DataFrame([
            {'timestamp': datetime.now() - timedelta(hours=i),
             'level': 'ERROR' if i % 4 == 0 else 'INFO',
             'component': 'TestComponent',
             'message': f'Test message {i}'}
            for i in range(48)
        ])
        
        trends = self.log_analyzer.analyze_trends(df)
        self.assertIn('time_series', trends)
        self.assertIn('growth_rates', trends)
        
    def test_find_correlated_events(self):
        """Test event correlation"""
        # Create test DataFrame with correlated events
        df = pd.DataFrame([
            # Component1 error followed by Component2 error
            {'timestamp': datetime.now() - timedelta(minutes=5),
             'level': 'ERROR',
             'component': 'Component1',
             'message': 'Error in Component1'},
            {'timestamp': datetime.now() - timedelta(minutes=4),
             'level': 'ERROR',
             'component': 'Component2',
             'message': 'Error in Component2'}
        ])
        
        correlations = self.log_analyzer.find_correlated_events(df)
        self.assertIsInstance(correlations, list)
        if correlations:  # If correlations were found
            self.assertEqual(correlations[0]['component1'], 'Component1')
            self.assertEqual(correlations[0]['component2'], 'Component2')
            
    def test_error_prediction(self):
        """Test error prediction"""
        # Create test DataFrame with periodic errors
        df = pd.DataFrame([
            {'timestamp': datetime.now() - timedelta(hours=i),
             'level': 'ERROR' if i % 12 == 0 else 'INFO',
             'component': 'TestComponent',
             'message': f'Test message {i}'}
            for i in range(72)
        ])
        
        prediction = self.log_analyzer.predict_error_likelihood(df, 'TestComponent')
        self.assertIn('error_likelihood', prediction)
        self.assertIn('confidence_score', prediction)
        
if __name__ == '__main__':
    unittest.main()
