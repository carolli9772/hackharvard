"""
FishNet Analysis Pipeline
Master script to run the complete illegal fishing detection pipeline.
"""

import sys
import time
from datetime import datetime


def run_pipeline(run_full_analysis=True):
    """
    Run the complete FishNet analysis pipeline.

    Args:
        run_full_analysis: If True, runs proximity index (slow). If False, uses simplified analysis.
    """
    print("=" * 60)
    print("FishNet - Illegal Fishing Detection Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    start_time = time.time()

    try:
        # # Step 1: Enhanced Dark Event Detection
        # print("\n[1/7] Enhanced Dark Event Detection...")
        # print("-" * 60)
        # from enhanced_dark_detection import main as dark_detection
        # dark_events = dark_detection()
        # print(f"✓ Completed: Detected {len(dark_events)} dark events")

        # # Step 2: Vessel Proximity Index (optional - can be slow)
        # if run_full_analysis:
        #     print("\n[2/7] Building Vessel Proximity Index...")
        #     print("-" * 60)
        #     print("Note: This step may take several minutes for large datasets...")
        #     from proximity_index import main as proximity_index
        #     proximity_events, pair_stats = proximity_index()
        #     print(f"✓ Completed: Found {len(proximity_events)} proximity events")
        # else:
        #     print("\n[2/7] Skipping Vessel Proximity Index (use --full for complete analysis)")
        #     proximity_events = []

        # # Step 3: Dark Event Context Checking
        # print("\n[3/7] Dark Event Context Checking...")
        # print("-" * 60)
        # from dark_event_context import main as context_check
        # contextualized_events, patterns = context_check(lightweight=True)
        # print(f"✓ Completed: Contextualized {len(contextualized_events)} events")

        # # Step 4: Suspicion Scoring and Clustering
        # print("\n[4/7] Suspicion Scoring and Clustering...")
        # print("-" * 60)
        # from suspicion_scoring import main as scoring
        # scored_events, clusters, hexbins = scoring()
        # print(f"✓ Completed: Scored {len(scored_events)} events, identified {len(clusters)} clusters")

        # Step 5: Network Analysis
        # print("\n[5/7] Network Analysis...")
        # print("-" * 60)
        # from network_analysis import main as network
        # graph, centrality, communities, motherships = network()
        # print(f"✓ Completed: Analyzed network with {graph.number_of_nodes()} vessels, {len(communities)} communities")

        # Step 6: Advanced Visualization
        print("\n[6/7] Generating Visualizations...")
        print("-" * 60)
        from advanced_visualization import main as visualization
        package = visualization()
        print(f"✓ Completed: Generated visualizations and frontend data package")

        # Step 7: Dataset Analysis
        print("\n[7/7] Additional Dataset Analysis...")
        print("-" * 60)
        from dataset_analysis import main as dataset_analysis
        fishing_data, protected_data, cross_ref = dataset_analysis()
        print(f"✓ Completed: Analyzed fishing gear and protected area datasets")

        # Pipeline Summary
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Total execution time: {elapsed_time/60:.2f} minutes")
        print(f"\nGenerated files:")
        print("  • enhanced_dark_events.json")
        print("  • contextualized_dark_events.json")
        print("  • scored_dark_events.json")
        print("  • dark_zone_clusters.json")
        print("  • dark_zone_hexbins.json")
        print("  • vessel_communities.json")
        print("  • centrality_scores.json")
        print("  • potential_motherships.json")
        print("  • frontend_data_package.json")
        print("  • dataset_analysis.json")
        print("  • suspicion_heatmap.png")
        print("  • network_viz.png")
        print("  • temporal_analysis.png")
        print("\nTo start the API server, run:")
        print("  python api.py")

        return True

    except Exception as e:
        print(f"\n✗ ERROR: Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_usage():
    """Print usage instructions."""
    print("""
FishNet Analysis Pipeline

Usage:
  python run_pipeline.py [options]

Options:
  --full      Run complete analysis including proximity index (slower)
  --fast      Run faster analysis without proximity index (default)
  --help      Show this help message

Examples:
  python run_pipeline.py              # Fast analysis
  python run_pipeline.py --full       # Complete analysis
    """)


if __name__ == "__main__":
    # Parse command line arguments
    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print_usage()
        sys.exit(0)

    run_full = '--full' in args

    # Run pipeline
    success = run_pipeline(run_full_analysis=run_full)

    sys.exit(0 if success else 1)
