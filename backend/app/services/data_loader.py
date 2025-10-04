import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)

class DataLoader:
    """Loads and preprocesses AIS and contextual datasets"""

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or settings.DATA_DIR)

    def load_ais_data(
        self,
        filename: str = "AIS_2024_01_01.csv",
        sample_size: Optional[int] = None,
        mmsi_filter: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Load NOAA AIS data

        Args:
            filename: CSV file name
            sample_size: Number of rows to sample (for testing)
            mmsi_filter: List of MMSI to filter

        Returns:
            DataFrame with standardized columns
        """
        filepath = self.data_dir / filename
        logger.info(f"Loading AIS data from {filepath}")

        # Read with optimized dtypes
        dtypes = {
            'MMSI': 'int64',
            'LAT': 'float32',
            'LON': 'float32',
            'SOG': 'float32',
            'COG': 'float32',
            'VesselName': 'str',
            'VesselType': 'str'
        }

        if sample_size:
            df = pd.read_csv(filepath, nrows=sample_size, dtype=dtypes)
        else:
            df = pd.read_csv(filepath, dtype=dtypes)

        # Standardize column names
        df = df.rename(columns={
            'MMSI': 'mmsi',
            'BaseDateTime': 'timestamp',
            'LAT': 'lat',
            'LON': 'lon',
            'SOG': 'speed',
            'COG': 'course',
            'VesselName': 'vessel_name',
            'VesselType': 'vessel_type'
        })

        # Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Filter invalid coordinates
        df = df[
            (df['lat'].between(-90, 90)) &
            (df['lon'].between(-180, 180))
        ]

        # Filter by MMSI if provided
        if mmsi_filter:
            df = df[df['mmsi'].isin(mmsi_filter)]

        # Add source
        df['source'] = 'noaa_ais'

        logger.info(f"Loaded {len(df)} AIS records")
        return df[['mmsi', 'timestamp', 'lat', 'lon', 'speed', 'course', 'vessel_name', 'vessel_type', 'source']]

    def load_fishing_vessel_data(
        self,
        vessel_type: str,
        sample_size: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load Global Fishing Watch vessel tracks

        Args:
            vessel_type: One of ['trawlers', 'drifting_longlines', 'purse_seines',
                                 'fixed_gear', 'pole_and_line', 'trollers']
            sample_size: Number of rows to sample

        Returns:
            DataFrame with standardized columns
        """
        filepath = self.data_dir / f"{vessel_type}.csv"
        logger.info(f"Loading fishing vessel data from {filepath}")

        dtypes = {
            'mmsi': 'int64',
            'timestamp': 'int64',
            'lat': 'float32',
            'lon': 'float32',
            'speed': 'float32',
            'course': 'float32',
            'distance_from_shore': 'float32',
            'distance_from_port': 'float32',
            'is_fishing': 'float32',
            'source': 'str'
        }

        if sample_size:
            df = pd.read_csv(filepath, nrows=sample_size, dtype=dtypes)
        else:
            df = pd.read_csv(filepath, dtype=dtypes)

        # Convert Unix timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # Filter invalid coordinates
        df = df[
            (df['lat'].between(-90, 90)) &
            (df['lon'].between(-180, 180))
        ]

        # Add vessel type metadata
        df['vessel_type'] = vessel_type
        df['vessel_name'] = None

        logger.info(f"Loaded {len(df)} {vessel_type} records")
        return df[['mmsi', 'timestamp', 'lat', 'lon', 'speed', 'course', 'vessel_name', 'vessel_type',
                  'distance_from_shore', 'distance_from_port', 'is_fishing', 'source']]

    def load_all_fishing_vessels(
        self,
        sample_size: Optional[int] = None,
        sample_size_per_type: Optional[int] = None
    ) -> pd.DataFrame:
        """Load all fishing vessel types and combine"""
        vessel_types = ['trawlers', 'drifting_longlines', 'purse_seines', 'fixed_gear', 'pole_and_line']
        dfs = []

        # Use sample_size_per_type if provided, otherwise use sample_size
        size_per_type = sample_size_per_type or sample_size

        for vtype in vessel_types:
            try:
                logger.info(f"Loading {vtype}...")
                df = self.load_fishing_vessel_data(vtype, sample_size=size_per_type)
                logger.info(f"  → {len(df)} records from {df['mmsi'].nunique()} vessels")
                dfs.append(df)
            except Exception as e:
                logger.warning(f"Could not load {vtype}: {e}")

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            logger.info(f"✓ Combined {len(combined)} records from {combined['mmsi'].nunique()} unique vessels across {len(dfs)} vessel types")
            return combined
        else:
            return pd.DataFrame()

    def load_mpa_data(self) -> gpd.GeoDataFrame:
        """
        Load Marine Protected Areas data

        Returns:
            GeoDataFrame with MPA polygons
        """
        filepath = self.data_dir / "WDPA_WDOECM_Oct2025_Public_marine_csv.csv"
        logger.info(f"Loading MPA data from {filepath}")

        # Read MPA data
        df = pd.read_csv(filepath, encoding='utf-8-sig')

        # Filter for marine areas only
        df = df[df['MARINE'].isin([1, 2])]  # 1=marine only, 2=coastal/mixed

        # Select relevant columns
        mpa_data = df[[
            'WDPAID', 'NAME', 'DESIG_ENG', 'IUCN_CAT',
            'MARINE', 'NO_TAKE', 'STATUS', 'ISO3'
        ]].copy()

        logger.info(f"Loaded {len(mpa_data)} MPAs")
        return mpa_data

    def combine_datasets(
        self,
        ais_df: pd.DataFrame,
        fishing_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Combine AIS and fishing vessel data"""
        # Align columns
        common_cols = ['mmsi', 'timestamp', 'lat', 'lon', 'speed', 'course',
                      'vessel_name', 'vessel_type', 'source']

        ais_subset = ais_df[common_cols]
        fishing_subset = fishing_df[common_cols]

        combined = pd.concat([ais_subset, fishing_subset], ignore_index=True)
        combined = combined.sort_values(['mmsi', 'timestamp'])

        logger.info(f"Combined dataset: {len(combined)} records from {combined['mmsi'].nunique()} vessels")
        return combined
