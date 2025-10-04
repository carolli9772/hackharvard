"""
Additional Dataset Analysis
Analyzes fishing gear types and protected marine areas.
"""

import pandas as pd
import numpy as np
import json
from collections import defaultdict


def analyze_fishing_gear_datasets():
    """Analyze all fishing gear datasets to understand fleet composition."""
    gear_types = {
        'drifting_longlines': '../../datasets/drifting_longlines.csv',
        'fixed_gear': '../../datasets/fixed_gear.csv',
        'pole_and_line': '../../datasets/pole_and_line.csv',
        'purse_seines': '../../datasets/purse_seines.csv',
        'trawlers': '../../datasets/trawlers.csv',
        'trollers': '../../datasets/trollers.csv'
    }

    analysis_results = {
        'gear_type_summary': [],
        'all_fishing_vessels': []
    }

    all_vessels = []

    for gear_type, path in gear_types.items():
        try:
            df = pd.read_csv(path)
            print(f"\n=== {gear_type.upper().replace('_', ' ')} ===")
            print(f"Total vessels: {len(df)}")

            # Get columns info
            print(f"Columns: {', '.join(df.columns.tolist())}")

            # Sample data
            print(f"\nSample records:")
            print(df.head(3))

            # Summary stats
            summary = {
                'gear_type': gear_type,
                'vessel_count': len(df),
                'columns': df.columns.tolist()
            }

            # Check for common columns
            if 'mmsi' in df.columns:
                summary['unique_mmsi'] = df['mmsi'].nunique()
                vessel_list = df['mmsi'].unique().tolist()

                # Add to all vessels
                for mmsi in vessel_list:
                    all_vessels.append({
                        'mmsi': int(mmsi) if pd.notna(mmsi) else None,
                        'gear_type': gear_type
                    })

            if 'flag' in df.columns:
                summary['top_flags'] = df['flag'].value_counts().head(5).to_dict()

            if 'length_m' in df.columns:
                summary['avg_length_m'] = round(df['length_m'].mean(), 2)

            analysis_results['gear_type_summary'].append(summary)

        except Exception as e:
            print(f"Error loading {gear_type}: {e}")

    # Consolidate all fishing vessels
    if all_vessels:
        vessel_df = pd.DataFrame(all_vessels)
        vessel_df = vessel_df.dropna(subset=['mmsi'])

        # Group by MMSI to see multi-gear vessels
        gear_by_vessel = vessel_df.groupby('mmsi')['gear_type'].apply(list).reset_index()
        gear_by_vessel['gear_count'] = gear_by_vessel['gear_type'].apply(len)

        # Find vessels with multiple gear types
        multi_gear = gear_by_vessel[gear_by_vessel['gear_count'] > 1]

        print(f"\n=== FISHING FLEET OVERVIEW ===")
        print(f"Total unique fishing vessels: {len(gear_by_vessel)}")
        print(f"Vessels with multiple gear types: {len(multi_gear)}")

        if len(multi_gear) > 0:
            print(f"\nSample multi-gear vessels:")
            print(multi_gear.head(5))

        analysis_results['total_fishing_vessels'] = len(gear_by_vessel)
        analysis_results['multi_gear_vessels'] = len(multi_gear)
        analysis_results['all_fishing_vessels'] = gear_by_vessel.to_dict('records')

    return analysis_results


def analyze_protected_areas():
    """Analyze marine protected areas dataset."""
    try:
        # Read only essential columns to manage memory
        df = pd.read_csv(
            '../../datasets/WDPA_WDOECM_Oct2025_Public_marine_csv.csv',
            low_memory=False
        )

        print(f"\n=== MARINE PROTECTED AREAS ===")
        print(f"Total protected areas: {len(df)}")
        print(f"Columns: {', '.join(df.columns.tolist())}")

        # Summary statistics
        analysis = {
            'total_areas': len(df),
            'columns': df.columns.tolist()
        }

        # Check for key columns
        if 'DESIG_ENG' in df.columns:
            print(f"\nTop designation types:")
            print(df['DESIG_ENG'].value_counts().head(10))
            analysis['top_designations'] = df['DESIG_ENG'].value_counts().head(10).to_dict()

        if 'REP_AREA' in df.columns:
            print(f"\nArea statistics (reported area):")
            print(df['REP_AREA'].describe())
            analysis['area_stats'] = df['REP_AREA'].describe().to_dict()

        if 'STATUS' in df.columns:
            print(f"\nProtection status:")
            print(df['STATUS'].value_counts())
            analysis['status_counts'] = df['STATUS'].value_counts().to_dict()

        if 'IUCN_CAT' in df.columns:
            print(f"\nIUCN Categories:")
            print(df['IUCN_CAT'].value_counts())
            analysis['iucn_categories'] = df['IUCN_CAT'].value_counts().to_dict()

        # Sample records
        print(f"\nSample protected areas:")
        print(df[['NAME', 'DESIG_ENG', 'REP_AREA']].head(5) if 'NAME' in df.columns else df.head(5))

        return analysis

    except Exception as e:
        print(f"Error analyzing protected areas: {e}")
        return {'error': str(e)}


def cross_reference_dark_events_with_datasets(dark_events, fishing_analysis):
    """
    Cross-reference dark events with fishing gear and protected area data.

    Args:
        dark_events: List of dark events
        fishing_analysis: Results from fishing gear analysis

    Returns:
        Enriched analysis with cross-references
    """
    if not dark_events or not fishing_analysis.get('all_fishing_vessels'):
        print("Missing data for cross-reference")
        return {}

    # Create MMSI to gear type mapping
    mmsi_to_gear = {}
    for vessel in fishing_analysis['all_fishing_vessels']:
        mmsi = vessel['mmsi']
        gear_types = vessel['gear_type']
        if mmsi not in mmsi_to_gear:
            mmsi_to_gear[mmsi] = []
        if isinstance(gear_types, list):
            mmsi_to_gear[mmsi].extend(gear_types)
        else:
            mmsi_to_gear[mmsi].append(gear_types)

    # Analyze dark events by gear type
    gear_type_stats = defaultdict(lambda: {'count': 0, 'total_suspicion': 0, 'events': []})

    for event in dark_events:
        mmsi = event['mmsi']
        if mmsi in mmsi_to_gear:
            for gear_type in mmsi_to_gear[mmsi]:
                gear_type_stats[gear_type]['count'] += 1
                gear_type_stats[gear_type]['total_suspicion'] += event.get('total_score', 0)
                gear_type_stats[gear_type]['events'].append({
                    'mmsi': mmsi,
                    'location': event['location'],
                    'suspicion_score': event.get('total_score', 0)
                })

    # Calculate averages
    gear_summary = []
    for gear_type, stats in gear_type_stats.items():
        if stats['count'] > 0:
            gear_summary.append({
                'gear_type': gear_type,
                'dark_event_count': stats['count'],
                'avg_suspicion_score': round(stats['total_suspicion'] / stats['count'], 3),
                'sample_events': stats['events'][:5]
            })

    # Sort by dark event count
    gear_summary.sort(key=lambda x: x['dark_event_count'], reverse=True)

    print("\n=== DARK EVENTS BY FISHING GEAR TYPE ===")
    for gear in gear_summary:
        print(f"{gear['gear_type']}: {gear['dark_event_count']} events, "
              f"avg suspicion: {gear['avg_suspicion_score']}")

    return {
        'dark_events_by_gear': gear_summary,
        'total_fishing_vessels_with_dark_events': len(set(
            e['mmsi'] for e in dark_events if e['mmsi'] in mmsi_to_gear
        ))
    }


def save_dataset_analysis(fishing_analysis, protected_analysis, cross_ref,
                          output_path='dataset_analysis.json'):
    """Save dataset analysis results."""
    analysis_package = {
        'fishing_gear_analysis': fishing_analysis,
        'protected_areas_analysis': protected_analysis,
        'cross_reference': cross_ref,
        'timestamp': pd.Timestamp.now().isoformat()
    }

    with open(output_path, 'w') as f:
        json.dump(analysis_package, f, indent=2)

    print(f"\nSaved dataset analysis to {output_path}")


def main():
    """Main function to analyze additional datasets."""
    print("=== DATASET ANALYSIS ===\n")

    # Analyze fishing gear datasets
    fishing_analysis = analyze_fishing_gear_datasets()

    # Analyze protected areas
    protected_analysis = analyze_protected_areas()

    # Load dark events for cross-referencing
    try:
        with open('scored_dark_events.json', 'r') as f:
            dark_events = json.load(f)

        # Cross-reference
        cross_ref = cross_reference_dark_events_with_datasets(dark_events, fishing_analysis)

    except FileNotFoundError:
        print("\nWarning: scored_dark_events.json not found. Run suspicion_scoring.py first.")
        cross_ref = {}

    # Save results
    save_dataset_analysis(fishing_analysis, protected_analysis, cross_ref)

    return fishing_analysis, protected_analysis, cross_ref


if __name__ == "__main__":
    main()
