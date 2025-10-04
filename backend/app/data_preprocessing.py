"""
Data Loading and Preprocessing Script for AIS Data Analysis
Loads AIS data and prepares it for dark event detection and spatial analysis.
"""

import pandas as pd
import os


def load_ais_data(file_path):
    """
    Load AIS data from CSV file.

    Args:
        file_path (str): Path to the AIS CSV file

    Returns:
        pd.DataFrame: Loaded AIS data
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"AIS data file not found: {file_path}")

    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} AIS records from {file_path}")
    return df


def preprocess_ais_data(df):
    """
    Preprocess AIS data: convert datetime, handle missing values.

    Args:
        df (pd.DataFrame): Raw AIS data

    Returns:
        pd.DataFrame: Preprocessed AIS data
    """
    # Convert BaseDateTime to datetime format
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])

    # Columns relevant for spatial and temporal calculations
    spatial_temporal_cols = ['LAT', 'LON', 'SOG', 'COG', 'Heading', 'BaseDateTime']

    # Check for missing values
    print("\nMissing values before handling:")
    print(df[spatial_temporal_cols].isnull().sum())

    # Drop rows with missing values in critical columns
    df_clean = df.dropna(subset=spatial_temporal_cols).copy()

    print(f"\nRows after dropping missing values: {len(df_clean)} (removed {len(df) - len(df_clean)} rows)")

    # Sort by MMSI and BaseDateTime for time-series analysis
    df_clean = df_clean.sort_values(by=['MMSI', 'BaseDateTime']).reset_index(drop=True)

    print("\nData types after preprocessing:")
    print(df_clean.dtypes)

    return df_clean


def main():
    """Main function to demonstrate data loading and preprocessing."""
    # Example usage - adjust path as needed
    file_path = '../../datasets/AIS_2024_01_01.csv'

    # Load data
    df = load_ais_data(file_path)
    print("\nFirst few rows of raw data:")
    print(df.head())

    # Preprocess data
    df_clean = preprocess_ais_data(df)
    print("\nFirst few rows of preprocessed data:")
    print(df_clean.head())

    # Save preprocessed data
    output_path = 'preprocessed_ais_data.csv'
    df_clean.to_csv(output_path, index=False)
    print(f"\nPreprocessed data saved to {output_path}")

    return df_clean


if __name__ == "__main__":
    main()
