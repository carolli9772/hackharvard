"""
Vessel Proximity Index System (Optimized)
Builds a "who was near whom and when" dataset using spatial indexing.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import json
from datetime import datetime
from data_preprocessing import load_ais_data, preprocess_ais_data


# ------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance (km)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371.0 * c  # Earth radius (km)


# ------------------------------------------------------------
# Core Algorithm
# ------------------------------------------------------------

def build_proximity_index(
    df,
    time_window_minutes=10,
    distance_threshold_km=20,
    save_every=25,
    max_points_per_bin=5000,
    resume=True,
    output_path="proximity_index.json",
):
    """
    Memory-safe, resumable proximity index builder.

    - Uses BallTree spatial indexing per time bin
    - Randomly subsamples dense bins to limit memory
    - Periodically saves partial progress
    - Can resume from partial JSON if interrupted
    """

    import os

    print(f"🚀 Building proximity index with {len(df):,} AIS records")
    print(f"⏱  Time window: {time_window_minutes} min | Distance threshold: {distance_threshold_km} km")
    print(f"💾  Output: {output_path}")

    # ------------------------------------------------------------
    # Resume from partial progress if requested
    # ------------------------------------------------------------
    existing_events = []
    processed_bins = set()
    if resume and os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                existing_events = json.load(f)
            if existing_events:
                processed_bins = {e["time_bin"] for e in existing_events}
                print(f"🔄 Resuming from {len(existing_events):,} saved events ({len(processed_bins)} bins done)")
        except Exception as e:
            print(f"⚠️ Could not resume from {output_path}: {e}")

    # ------------------------------------------------------------
    # Preprocess and initialize
    # ------------------------------------------------------------
    df = df.sort_values("BaseDateTime").reset_index(drop=True)
    df["TimeBin"] = df["BaseDateTime"].dt.floor(f"{time_window_minutes}min")
    time_bins = df["TimeBin"].unique()
    print(f"📦 Total time bins: {len(time_bins)}")

    radius_rad = distance_threshold_km / 6371.0  # km → radians
    proximity_events = existing_events

    # ------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------
    for i, time_bin in enumerate(time_bins):
        if str(time_bin) in processed_bins:
            continue  # skip completed bin

        if i % 10 == 0:
            print(f"  ⏳ Bin {i}/{len(time_bins)} — events so far: {len(proximity_events):,}")

        bin_data = df[df["TimeBin"] == time_bin]
        n_points = len(bin_data)
        if n_points < 2:
            continue

        # Limit bin size to avoid OOM
        if n_points > max_points_per_bin:
            bin_data = bin_data.sample(max_points_per_bin, random_state=42)

        # Build spatial tree
        coords_rad = np.radians(bin_data[["LAT", "LON"]].values)
        tree = BallTree(coords_rad, metric="haversine")
        neighbors = tree.query_radius(coords_rad, r=radius_rad, return_distance=False)

        # Build all pairs efficiently
        pair_list = []
        for idx, nbrs in enumerate(neighbors):
            valid = nbrs[nbrs > idx]  # skip self & dupes
            if valid.size:
                idxs = np.full(valid.shape, idx)
                pair_list.append(np.column_stack((idxs, valid)))
        if not pair_list:
            continue

        pairs = np.vstack(pair_list)
        v1 = bin_data.iloc[pairs[:, 0]].reset_index(drop=True)
        v2 = bin_data.iloc[pairs[:, 1]].reset_index(drop=True)

        # Compute vectorized distances (haversine)
        lat1, lon1 = np.radians(v1["LAT"].values), np.radians(v1["LON"].values)
        lat2, lon2 = np.radians(v2["LAT"].values), np.radians(v2["LON"].values)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        distance_km = 6371.0 * (2 * np.arcsin(np.sqrt(a)))

        prox_df = pd.DataFrame({
            "time_bin": time_bin.isoformat(),
            "vessel1_mmsi": v1["MMSI"].astype(int),
            "vessel2_mmsi": v2["MMSI"].astype(int),
            "vessel1_location": list(zip(v1["LAT"], v1["LON"])),
            "vessel2_location": list(zip(v2["LAT"], v2["LON"])),
            "distance_km": np.round(distance_km, 2)
        })

        proximity_events.extend(prox_df.to_dict(orient="records"))
        processed_bins.add(str(time_bin))

        # --------------------------------------------------------
        # Periodic saving (to limit memory + allow resume)
        # --------------------------------------------------------
        if i % save_every == 0 or i == len(time_bins) - 1:
            tmp_path = output_path.replace(".json", "_partial.json")
            with open(tmp_path, "w") as f:
                json.dump(proximity_events, f)
            print(f"💾  Checkpoint saved ({len(proximity_events):,} total events)")

        # Explicitly free memory each loop
        del bin_data, coords_rad, tree, neighbors, pair_list, pairs, v1, v2, prox_df

    # ------------------------------------------------------------
    # Final save
    # ------------------------------------------------------------
    with open(output_path, "w") as f:
        json.dump(proximity_events, f, indent=2)
    print(f"\n✅ Completed proximity index: {len(proximity_events):,} total events")
    print(f"💾 Saved to {output_path}")

    return proximity_events

# ------------------------------------------------------------
# Aggregation
# ------------------------------------------------------------

def aggregate_proximity_stats(proximity_events):
    """Aggregate proximity events into vessel pair statistics."""
    if not proximity_events:
        print("No proximity events to aggregate.")
        return pd.DataFrame()

    df = pd.DataFrame(proximity_events)
    pair_stats = (
        df.groupby(["vessel1_mmsi", "vessel2_mmsi"])
        .agg(encounter_count=("time_bin", "count"), avg_distance_km=("distance_km", "mean"))
        .reset_index()
        .sort_values("encounter_count", ascending=False)
    )

    print("\nTop vessel pairs by encounter count:")
    print(pair_stats.head(10))
    return pair_stats


# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def get_vessels_near_location(proximity_events, target_location, target_time,
                               radius_km=20, time_window_minutes=15):
    """Find vessels near a given location and time."""
    if isinstance(target_time, str):
        target_time = pd.to_datetime(target_time)

    target_lat, target_lon = target_location
    time_delta = pd.Timedelta(minutes=time_window_minutes)

    nearby = []
    for event in proximity_events:
        event_time = pd.to_datetime(event["time_bin"])
        if abs(event_time - target_time) > time_delta:
            continue

        for vessel_key in ["vessel1", "vessel2"]:
            loc = event[f"{vessel_key}_location"]
            dist = haversine_distance(target_lat, target_lon, loc[0], loc[1])
            if dist <= radius_km:
                nearby.append({
                    "mmsi": event[f"{vessel_key}_mmsi"],
                    "name": event[f"{vessel_key}_name"],
                    "location": loc,
                    "distance_km": round(float(dist), 2),
                    "time": event["time_bin"]
                })

    # Remove duplicates
    seen = set()
    unique = []
    for v in nearby:
        key = (v["mmsi"], v["time"])
        if key not in seen:
            seen.add(key)
            unique.append(v)

    return unique


def save_proximity_index(proximity_events, output_path="proximity_index.json"):
    """Save proximity index to JSON file."""
    with open(output_path, "w") as f:
        json.dump(proximity_events, f, indent=2)
    print(f"Saved proximity index to {output_path}")


# ------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------

def main():
    """Main entry point."""
    # Load and preprocess AIS data
    file_path = "../../datasets/AIS_2024_01_01.csv"
    df = load_ais_data(file_path)
    df_clean = preprocess_ais_data(df)

    # Build proximity index
    proximity_events = build_proximity_index(
        df_clean,
        time_window_minutes=10,
        distance_threshold_km=20,
        save_every=100
    )

    # Aggregate statistics
    pair_stats = aggregate_proximity_stats(proximity_events)

    # Save outputs
    save_proximity_index(proximity_events)
    pair_stats.to_csv("vessel_pair_stats.csv", index=False)
    print("Saved vessel pair statistics to vessel_pair_stats.csv")

    # Quick example lookup
    if proximity_events:
        sample = proximity_events[0]
        print(f"\n🔍 Running sample proximity query for {sample['vessel1_mmsi']} at {sample['time_bin']}...")
        try:
            nearby = get_vessels_near_location(
                proximity_events,
                sample["vessel1_location"],
                sample["time_bin"],
                radius_km=20
            )
            print(f"Found {len(nearby)} vessels nearby.")
        except KeyError:
            print("Skipped example lookup (name fields not included in proximity events).")


    return proximity_events, pair_stats


if __name__ == "__main__":
    main()
