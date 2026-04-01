"""
Health Drift Engine - Data Parser (FIXED)
Compatible with pandas 2.x
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger()


class HealthDataParser:
    """Parse and preprocess raw JSON health data into clean time series"""
    
    def __init__(self):
        self.config = get_config()
        self.max_forward_fill = self.config.max_forward_fill_days
        
    def parse_json_records(
        self,
        json_records: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Parse list of JSON records into structured DataFrame
        
        Handles two formats:
        1. Nested format (from DBMS): vitals/movement/sleep sub-dicts
        2. Flat format (from synthetic generator): all fields at top level
        
        Args:
            json_records: List of health data records in JSON format
            
        Returns:
            Clean DataFrame with datetime index
        """
        if not json_records:
            raise ValueError("Empty JSON records provided")
        
        logger.info("Parsing JSON records", count=len(json_records))
        
        # Check if data is already flat (from synthetic generator)
        first_record = json_records[0]
        is_nested = any(key in first_record for key in ['vitals', 'movement', 'sleep'])
        
        if is_nested:
            # Flatten nested JSON structure
            flattened_records = self._flatten_nested_records(json_records)
        else:
            # Already flat - just ensure timestamp is present
            flattened_records = json_records
        
        # Create DataFrame
        df = pd.DataFrame(flattened_records)
        
        # Ensure timestamp column exists
        if 'timestamp' not in df.columns:
            raise ValueError("Timestamp column missing from data")
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info("JSON parsing complete", rows=len(df))
        
        return df
    
    def _flatten_nested_records(
        self,
        json_records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Flatten nested JSON structure from DBMS format"""
        flattened_records = []
        
        for record in json_records:
            flat_record = {
                'userId': record.get('userId'),
                'timestamp': record.get('timestamp')
            }
            
            # Flatten vitals
            if 'vitals' in record and record['vitals']:
                for key, value in record['vitals'].items():
                    flat_record[key] = value
            
            # Flatten movement
            if 'movement' in record and record['movement']:
                for key, value in record['movement'].items():
                    flat_record[key] = value
            
            # Flatten sleep
            if 'sleep' in record and record['sleep']:
                flat_record['totalSleepHours'] = record['sleep'].get('totalHours')
                flat_record['deepSleepHours'] = record['sleep'].get('deepSleepHours')
                flat_record['remSleepHours'] = record['sleep'].get('remSleepHours')
                flat_record['sleepLatencyMinutes'] = record['sleep'].get('latencyMinutes')
                flat_record['awakenings'] = record['sleep'].get('awakenings')
            
            # Flatten cognitive
            if 'cognitivePerformance' in record and record['cognitivePerformance']:
                flat_record['reactionTimeMs'] = record['cognitivePerformance'].get('reactionTimeMs')
                flat_record['memoryScore'] = record['cognitivePerformance'].get('memoryScore')
            
            flattened_records.append(flat_record)
        
        return flattened_records
    
    def aggregate_to_daily(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Aggregate intraday measurements to daily values
        
        Args:
            df: DataFrame with timestamp column
            
        Returns:
            Daily aggregated DataFrame
        """
        logger.info("Aggregating to daily values")
        
        # Extract date
        df['date'] = df['timestamp'].dt.date
        
        # Define aggregation strategy for each column
        agg_functions = {}
        
        # Numeric columns - take mean
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['steps']:
                agg_functions[col] = 'sum'  # Sum steps
            else:
                agg_functions[col] = 'mean'  # Average other metrics
        
        # Keep userId
        if 'userId' in df.columns:
            agg_functions['userId'] = 'first'
        
        # Keep age and sex if present
        if 'age' in df.columns:
            agg_functions['age'] = 'first'
        if 'sex' in df.columns:
            agg_functions['sex'] = 'first'
        if 'label' in df.columns:
            agg_functions['label'] = 'first'
        
        # Group by date
        daily_df = df.groupby('date').agg(agg_functions).reset_index()
        
        # Rename date to timestamp
        daily_df = daily_df.rename(columns={'date': 'timestamp'})
        daily_df['timestamp'] = pd.to_datetime(daily_df['timestamp'])
        
        logger.info("Daily aggregation complete", days=len(daily_df))
        
        return daily_df
    
    def handle_missing_values(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Handle missing values with forward fill (limited)
        FIXED: Compatible with pandas 2.x
        
        Args:
            df: DataFrame with potential missing values
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info("Handling missing values")
        
        # Set timestamp as index for forward fill
        df = df.set_index('timestamp')
        
        # Forward fill up to max_forward_fill days
        # FIXED: Use ffill() instead of fillna(method='ffill')
        df = df.ffill(limit=self.max_forward_fill)
        
        # Count remaining missing values
        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            logger.warning(
                "Missing values remain after forward fill",
                total_missing=int(missing_counts.sum())
            )
        
        # Reset index
        df = df.reset_index()
        
        return df
    
    def validate_completeness(
        self,
        df: pd.DataFrame,
        min_completeness: float = 0.7
    ) -> bool:
        """
        Validate that data is sufficiently complete
        
        Args:
            df: DataFrame to validate
            min_completeness: Minimum ratio of non-null values required
            
        Returns:
            True if data meets completeness threshold
        """
        # Exclude metadata columns from completeness check
        exclude_cols = ['userId', 'age', 'sex', 'label', 'timestamp']
        data_cols = [col for col in df.columns if col not in exclude_cols]
        
        if not data_cols:
            logger.warning("No data columns found for completeness check")
            return True
        
        data_df = df[data_cols]
        completeness = 1 - (data_df.isnull().sum().sum() / (data_df.shape[0] * data_df.shape[1]))
        
        logger.info(
            "Data completeness check",
            completeness=f"{completeness:.2%}",
            threshold=f"{min_completeness:.2%}"
        )
        
        if completeness < min_completeness:
            logger.warning(
                "Data completeness below threshold",
                completeness=f"{completeness:.2%}"
            )
            return False
        
        return True
    
    def parse_and_clean(
        self,
        json_records: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Complete parsing pipeline: JSON -> daily aggregation -> missing value handling
        
        Args:
            json_records: Raw JSON health records
            
        Returns:
            Clean daily time series DataFrame
        """
        # Parse JSON
        df = self.parse_json_records(json_records)
        
        # Aggregate to daily
        daily_df = self.aggregate_to_daily(df)
        
        # Handle missing values
        clean_df = self.handle_missing_values(daily_df)
        
        # Validate completeness
        is_valid = self.validate_completeness(
            clean_df,
            min_completeness=self.config.min_completeness_ratio
        )
        
        if not is_valid:
            logger.warning("Data quality concerns - proceeding with caution")
        
        logger.info("Parsing pipeline complete", final_rows=len(clean_df))
        
        return clean_df


if __name__ == "__main__":
    # Test parser with synthetic data format
    sample_records = [
        {
            "userId": "TEST123",
            "timestamp": "2024-01-01T08:00:00Z",
            "hrvSdnnMs": 48.5,
            "heartRateAvg": 72,
            "gaitSpeedMs": 1.25,
            "steps": 8500
        }
    ]
    
    parser = HealthDataParser()
    df = parser.parse_and_clean(sample_records)
    print(df.head())