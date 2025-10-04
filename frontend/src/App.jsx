import React, { useState, useEffect } from "react";
import { StatCard } from "./components/StatCard";
import { EventItem } from "./components/EventItem";
import { CommunityItem } from "./components/CommunityItem";
import { HotspotItem } from "./components/HotspotItem";
import { CoordinatorItem } from "./components/CoordinatorItem";
import { MothershipItem } from "./components/MothershipItem";
import { FilterButton } from "./components/FilterButton";
import { Section } from "./components/Section";
import { LoadingSpinner } from "./components/LoadingSpinner";
import { ErrorMessage } from "./components/ErrorMessage";
import { EventMap } from "./components/EventMap";

const API_BASE = "http://localhost:5001/api";

export default function FishNetDashboard() {
  const [stats, setStats] = useState(null);
  const [allEvents, setAllEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [hotspots, setHotspots] = useState([]);
  const [coordinators, setCoordinators] = useState([]);
  const [motherships, setMotherships] = useState([]);
  const [networkStats, setNetworkStats] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVessel, setSelectedVessel] = useState(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadStats(),
        loadEvents(),
        loadCommunities(),
        loadHotspots(),
        loadCoordinators(),
        loadMotherships(),
        loadNetworkStats(),
      ]);
    } catch (err) {
      setError(
        "Failed to load data. Make sure the API server is running on port 5001."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    const response = await fetch(`${API_BASE}/summary`);
    const data = await response.json();
    setStats(data);
  };

  const loadEvents = async () => {
    const response = await fetch(`${API_BASE}/suspicious-events?limit=100`);
    const data = await response.json();
    setAllEvents(data.events || []);
    setFilteredEvents(data.events || []);
  };

  const loadCommunities = async () => {
    const response = await fetch(`${API_BASE}/communities?limit=10`);
    const data = await response.json();
    setCommunities(data.communities || []);
  };

  const loadHotspots = async () => {
    const response = await fetch(`${API_BASE}/hotspots?limit=20`);
    const data = await response.json();
    setHotspots(data.hotspots || []);
  };

  const loadCoordinators = async () => {
    const response = await fetch(`${API_BASE}/coordinators?limit=20`);
    const data = await response.json();
    setCoordinators(data.coordinators || []);
  };

  const loadMotherships = async () => {
    const response = await fetch(`${API_BASE}/motherships`);
    const data = await response.json();
    setMotherships(data.motherships || []);
  };

  const loadNetworkStats = async () => {
    const response = await fetch(`${API_BASE}/network/stats`);
    const data = await response.json();
    setNetworkStats(data);
  };

  const handleFilter = (type) => {
    setActiveFilter(type);
    let filtered = allEvents;

    if (type === "high") {
      filtered = allEvents.filter((e) => (e.total_score || 0) >= 0.7);
    } else if (type === "fishing") {
      filtered = allEvents.filter((e) => e.is_fishing_vessel);
    } else if (type === "rendezvous") {
      filtered = allEvents.filter((e) => (e.nearby_vessels_at_start || 0) > 5);
    }

    setFilteredEvents(filtered);
  };

  const handleEventClick = async (event) => {
    try {
      const response = await fetch(`${API_BASE}/vessel/${event.mmsi}`);
      const vesselData = await response.json();
      setSelectedVessel(vesselData);
    } catch (err) {
      console.error("Error loading vessel details:", err);
    }
  };

  if (loading) {
    return (
      <div
        style={{
          fontFamily:
            '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif',
          background:
            "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
          color: "#fff",
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <LoadingSpinner message="Loading FishNet Dashboard..." />
      </div>
    );
  }

  return (
    <div
      style={{
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif',
        background:
          "linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)",
        color: "#fff",
        minHeight: "100vh",
        padding: "20px",
        margin: 0,
      }}
    >
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <header
          style={{
            textAlign: "center",
            padding: "30px 0",
            borderBottom: "2px solid rgba(255, 255, 255, 0.1)",
            marginBottom: "40px",
          }}
        >
          <h1
            style={{
              fontSize: "3em",
              marginBottom: "10px",
              background: "linear-gradient(90deg, #00d4ff, #00ff88)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            🎣 FishNet
          </h1>
          <p style={{ color: "#aaa", fontSize: "1.2em" }}>
            Illegal Fishing Detection via AIS Dark Patterns
          </p>
        </header>

        {error && <ErrorMessage message={error} />}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "20px",
            marginBottom: "40px",
          }}
        >
          {stats && (
            <>
              <StatCard
                icon="🌑"
                label="Total Dark Events"
                value={stats.total_dark_events?.toLocaleString() || "0"}
              />
              <StatCard
                icon="⚠️"
                label="High Suspicion"
                value={stats.high_suspicion_events?.toLocaleString() || "0"}
              />
              <StatCard
                icon="🎣"
                label="Fishing Vessels"
                value={stats.fishing_vessel_events?.toLocaleString() || "0"}
              />
              <StatCard
                icon="🌐"
                label="Communities"
                value={stats.suspicious_communities?.toLocaleString() || "0"}
              />
              <StatCard
                icon="🚢"
                label="Motherships"
                value={stats.potential_motherships?.toLocaleString() || "0"}
              />
              <StatCard
                icon="⏱️"
                label="Avg Duration"
                value={stats.avg_duration_hours?.toFixed(1) || "0"}
                unit="h"
              />
              <StatCard
                icon="🔥"
                label="Hotspots"
                value={stats.total_hotspots?.toLocaleString() || "0"}
              />
              <StatCard
                icon="🚢"
                label="Total Vessels"
                value={stats.total_vessels_involved?.toLocaleString() || "0"}
              />
            </>
          )}
        </div>

        {networkStats && (
          <Section title="📊 Network Analysis Overview">
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                gap: "15px",
              }}
            >
              <div
                style={{
                  padding: "15px",
                  background: "rgba(0, 212, 255, 0.1)",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#00d4ff",
                    fontSize: "1.5em",
                    fontWeight: "bold",
                  }}
                >
                  {networkStats.total_vessels}
                </div>
                <div style={{ color: "#aaa", fontSize: "0.9em" }}>
                  Total Vessels in Network
                </div>
              </div>
              <div
                style={{
                  padding: "15px",
                  background: "rgba(0, 212, 255, 0.1)",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#00d4ff",
                    fontSize: "1.5em",
                    fontWeight: "bold",
                  }}
                >
                  {networkStats.total_communities}
                </div>
                <div style={{ color: "#aaa", fontSize: "0.9em" }}>
                  Detected Communities
                </div>
              </div>
              <div
                style={{
                  padding: "15px",
                  background: "rgba(255, 165, 0, 0.1)",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#ffa500",
                    fontSize: "1.5em",
                    fontWeight: "bold",
                  }}
                >
                  {networkStats.suspicious_fleets}
                </div>
                <div style={{ color: "#aaa", fontSize: "0.9em" }}>
                  Suspicious Fleets
                </div>
              </div>
            </div>
          </Section>
        )}

        <Section title="🗺️ Interactive Dark Event Map">
          <EventMap
            events={allEvents}
            hotspots={hotspots}
            onEventClick={handleEventClick}
          />
        </Section>

        {motherships.length > 0 && (
          <Section title="🚢 Potential Motherships / Transshipment Vessels">
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {motherships.map((mothership, idx) => (
                <MothershipItem
                  key={idx}
                  mothership={mothership}
                  onClick={handleEventClick}
                />
              ))}
            </div>
          </Section>
        )}

        {hotspots.length > 0 && (
          <Section title="🔥 Dark Zone Hotspots">
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {hotspots.map((hotspot, idx) => (
                <HotspotItem key={idx} hotspot={hotspot} />
              ))}
            </div>
          </Section>
        )}

        <Section title="⚠️ Suspicious Dark Events">
          <div
            style={{
              display: "flex",
              gap: "15px",
              marginBottom: "20px",
              flexWrap: "wrap",
            }}
          >
            <FilterButton
              active={activeFilter === "all"}
              onClick={() => handleFilter("all")}
            >
              All Events
            </FilterButton>
            <FilterButton
              active={activeFilter === "high"}
              onClick={() => handleFilter("high")}
            >
              High Suspicion (≥0.7)
            </FilterButton>
            <FilterButton
              active={activeFilter === "fishing"}
              onClick={() => handleFilter("fishing")}
            >
              Fishing Vessels Only
            </FilterButton>
            <FilterButton
              active={activeFilter === "rendezvous"}
              onClick={() => handleFilter("rendezvous")}
            >
              Potential Rendezvous
            </FilterButton>
          </div>

          <div
            style={{
              color: "#aaa",
              fontSize: "0.9em",
              marginBottom: "15px",
              padding: "10px",
              background: "rgba(0, 212, 255, 0.1)",
              borderRadius: "5px",
            }}
          >
            Showing {filteredEvents.length} of {allEvents.length} events
          </div>

          <div style={{ maxHeight: "500px", overflowY: "auto" }}>
            {filteredEvents.length > 0 ? (
              filteredEvents.map((event, idx) => (
                <EventItem key={idx} event={event} onClick={handleEventClick} />
              ))
            ) : (
              <div
                style={{ textAlign: "center", padding: "40px", color: "#aaa" }}
              >
                No events match the selected filter
              </div>
            )}
          </div>
        </Section>

        {coordinators.length > 0 && (
          <Section title="🎯 Potential Coordinator Vessels (High Centrality)">
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {coordinators.map((coordinator, idx) => (
                <CoordinatorItem
                  key={idx}
                  coordinator={coordinator}
                  onClick={handleEventClick}
                />
              ))}
            </div>
          </Section>
        )}

        {communities.length > 0 && (
          <Section title="🌐 Vessel Networks & Suspicious Communities">
            <div style={{ maxHeight: "400px", overflowY: "auto" }}>
              {communities.map((community, idx) => (
                <CommunityItem key={idx} community={community} />
              ))}
            </div>
          </Section>
        )}

        {selectedVessel && (
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: "rgba(0, 0, 0, 0.8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
              padding: "20px",
            }}
            onClick={() => setSelectedVessel(null)}
          >
            <div
              style={{
                background: "linear-gradient(135deg, #1a2a3a 0%, #2c3e50 100%)",
                borderRadius: "15px",
                padding: "30px",
                maxWidth: "800px",
                maxHeight: "80vh",
                overflowY: "auto",
                border: "2px solid #00d4ff",
                position: "relative",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedVessel(null)}
                style={{
                  position: "absolute",
                  top: "15px",
                  right: "15px",
                  background: "rgba(255, 59, 48, 0.3)",
                  border: "1px solid #ff3b30",
                  color: "#fff",
                  padding: "8px 15px",
                  borderRadius: "5px",
                  cursor: "pointer",
                  fontSize: "1em",
                }}
              >
                ✕ Close
              </button>

              <h2
                style={{
                  color: "#00d4ff",
                  marginBottom: "20px",
                  fontSize: "2em",
                }}
              >
                🚢 Vessel Details: {selectedVessel.mmsi}
              </h2>

              <div style={{ marginBottom: "20px" }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: "15px",
                    marginBottom: "20px",
                  }}
                >
                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "15px",
                      borderRadius: "10px",
                    }}
                  >
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "0.85em",
                        marginBottom: "5px",
                      }}
                    >
                      Vessel Name
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.2em",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedVessel.vessel_name || "Unknown"}
                    </div>
                  </div>

                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "15px",
                      borderRadius: "10px",
                    }}
                  >
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "0.85em",
                        marginBottom: "5px",
                      }}
                    >
                      Type
                    </div>
                    <div
                      style={{
                        color: "#00ff88",
                        fontSize: "1.2em",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedVessel.is_fishing_vessel
                        ? "🎣 Fishing Vessel"
                        : "🚢 Other Vessel"}
                    </div>
                  </div>

                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "15px",
                      borderRadius: "10px",
                    }}
                  >
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "0.85em",
                        marginBottom: "5px",
                      }}
                    >
                      Total Dark Events
                    </div>
                    <div
                      style={{
                        color: "#ffa500",
                        fontSize: "1.2em",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedVessel.total_dark_events}
                    </div>
                  </div>

                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "15px",
                      borderRadius: "10px",
                    }}
                  >
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "0.85em",
                        marginBottom: "5px",
                      }}
                    >
                      Avg Suspicion Score
                    </div>
                    <div
                      style={{
                        color: "#ff3838",
                        fontSize: "1.2em",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedVessel.avg_suspicion_score?.toFixed(3)}
                    </div>
                  </div>

                  <div
                    style={{
                      background: "rgba(255, 255, 255, 0.05)",
                      padding: "15px",
                      borderRadius: "10px",
                    }}
                  >
                    <div
                      style={{
                        color: "#aaa",
                        fontSize: "0.85em",
                        marginBottom: "5px",
                      }}
                    >
                      Max Suspicion Score
                    </div>
                    <div
                      style={{
                        color: "#ff3838",
                        fontSize: "1.2em",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedVessel.max_suspicion_score?.toFixed(3)}
                    </div>
                  </div>

                  {selectedVessel.fishing_gear_types &&
                    selectedVessel.fishing_gear_types.length > 0 && (
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "15px",
                          borderRadius: "10px",
                        }}
                      >
                        <div
                          style={{
                            color: "#aaa",
                            fontSize: "0.85em",
                            marginBottom: "5px",
                          }}
                        >
                          Fishing Gear
                        </div>
                        <div style={{ color: "#00d4ff", fontSize: "1em" }}>
                          {selectedVessel.fishing_gear_types.join(", ")}
                        </div>
                      </div>
                    )}
                </div>

                <h3
                  style={{
                    color: "#00d4ff",
                    marginTop: "30px",
                    marginBottom: "15px",
                  }}
                >
                  Dark Event History ({selectedVessel.events?.length || 0}{" "}
                  events)
                </h3>

                <div style={{ maxHeight: "300px", overflowY: "auto" }}>
                  {selectedVessel.events?.map((event, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: "rgba(255, 255, 255, 0.03)",
                        padding: "12px",
                        marginBottom: "8px",
                        borderRadius: "8px",
                        borderLeft: `3px solid ${
                          event.total_score >= 0.7 ? "#ff3838" : "#ffa500"
                        }`,
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: "8px",
                        }}
                      >
                        <span style={{ color: "#00d4ff", fontWeight: "bold" }}>
                          Event #{idx + 1}
                        </span>
                        <span style={{ color: "#ff3838" }}>
                          Score: {event.total_score?.toFixed(3)}
                        </span>
                      </div>
                      <div style={{ fontSize: "0.85em", color: "#ccc" }}>
                        📍 [{event.location?.[0]?.toFixed(2)},{" "}
                        {event.location?.[1]?.toFixed(2)}] | ⏱️{" "}
                        {event.duration_hours?.toFixed(1)}h | 🌍{" "}
                        {event.region || "Unknown"}
                      </div>
                      <div
                        style={{
                          fontSize: "0.8em",
                          color: "#888",
                          marginTop: "5px",
                        }}
                      >
                        {new Date(event.start).toLocaleString()} →{" "}
                        {new Date(event.end).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        <footer
          style={{
            textAlign: "center",
            padding: "30px 0",
            marginTop: "40px",
            borderTop: "2px solid rgba(255, 255, 255, 0.1)",
            color: "#666",
          }}
        >
          <p>FishNet - Illegal Fishing Detection System</p>
          <p style={{ fontSize: "0.9em", marginTop: "10px" }}>
            Powered by AIS Dark Pattern Analysis & Network Detection
          </p>
        </footer>
      </div>
    </div>
  );
}
