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

// Sidebar Navigation Item
const SidebarItem = ({ active, onClick, icon, children }) => (
  <div
    onClick={onClick}
    style={{
      padding: "15px 20px",
      cursor: "pointer",
      background: active ? "rgba(0, 212, 255, 0.2)" : "transparent",
      borderLeft: active ? "4px solid #00d4ff" : "4px solid transparent",
      color: active ? "#00d4ff" : "#aaa",
      transition: "all 0.3s",
      display: "flex",
      alignItems: "center",
      gap: "12px",
      fontSize: "1em",
      fontWeight: active ? "bold" : "normal",
    }}
    onMouseEnter={(e) => {
      if (!active) {
        e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
        e.currentTarget.style.color = "#fff";
      }
    }}
    onMouseLeave={(e) => {
      if (!active) {
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.color = "#aaa";
      }
    }}
  >
    <span style={{ fontSize: "1.5em" }}>{icon}</span>
    <span>{children}</span>
  </div>
);

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
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedVessel, setSelectedVessel] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
        margin: 0,
        display: "flex",
      }}
    >
      {/* Sidebar */}
      <div
        style={{
          width: sidebarCollapsed ? "80px" : "280px",
          background: "rgba(0, 0, 0, 0.3)",
          borderRight: "1px solid rgba(255, 255, 255, 0.1)",
          transition: "width 0.3s",
          position: "fixed",
          height: "100vh",
          overflowY: "auto",
          overflowX: "hidden",
          zIndex: 100,
        }}
      >
        {/* Logo/Header */}
        <div
          style={{
            padding: "25px 20px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
            textAlign: sidebarCollapsed ? "center" : "left",
          }}
        >
          {!sidebarCollapsed ? (
            <>
              <h1
                style={{
                  fontSize: "1.8em",
                  background: "linear-gradient(90deg, #00d4ff, #00ff88)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  marginBottom: "5px",
                }}
              >
                🎣 FishNet
              </h1>
              <p style={{ color: "#666", fontSize: "0.8em" }}>
                Illegal Fishing Detection
              </p>
            </>
          ) : (
            <div style={{ fontSize: "2em" }}>🎣</div>
          )}
        </div>

        {/* Navigation */}
        <div style={{ padding: "20px 0" }}>
          <SidebarItem
            active={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            icon="📊"
          >
            {!sidebarCollapsed && "Overview"}
          </SidebarItem>
          <SidebarItem
            active={activeTab === "map"}
            onClick={() => setActiveTab("map")}
            icon="🗺️"
          >
            {!sidebarCollapsed && "Live Map"}
          </SidebarItem>
          <SidebarItem
            active={activeTab === "events"}
            onClick={() => setActiveTab("events")}
            icon="⚠️"
          >
            {!sidebarCollapsed && "Dark Events"}
          </SidebarItem>
          <SidebarItem
            active={activeTab === "vessels"}
            onClick={() => setActiveTab("vessels")}
            icon="🚢"
          >
            {!sidebarCollapsed && "High-Risk Vessels"}
          </SidebarItem>
          <SidebarItem
            active={activeTab === "network"}
            onClick={() => setActiveTab("network")}
            icon="🌐"
          >
            {!sidebarCollapsed && "Network Analysis"}
          </SidebarItem>
        </div>

        {/* Collapse Button */}
        <div
          style={{
            position: "absolute",
            bottom: "20px",
            left: sidebarCollapsed ? "50%" : "20px",
            transform: sidebarCollapsed ? "translateX(-50%)" : "none",
          }}
        >
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            style={{
              background: "rgba(0, 212, 255, 0.2)",
              border: "1px solid #00d4ff",
              color: "#00d4ff",
              padding: "10px",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "1.2em",
            }}
          >
            {sidebarCollapsed ? "→" : "←"}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div
        style={{
          marginLeft: sidebarCollapsed ? "80px" : "280px",
          width: `calc(100% - ${sidebarCollapsed ? "80px" : "280px"})`,
          transition: "margin-left 0.3s, width 0.3s",
          padding: "30px",
          overflowY: "auto",
          height: "100vh",
        }}
      >
        {error && <ErrorMessage message={error} />}

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "30px",
                color: "#00d4ff",
              }}
            >
              Dashboard Overview
            </h2>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
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
                    icon="🚢"
                    label="Motherships"
                    value={stats.potential_motherships?.toLocaleString() || "0"}
                  />
                </>
              )}
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "30px",
                marginBottom: "30px",
              }}
            >
              <Section title="🔥 Top Hotspots">
                <div style={{ maxHeight: "350px", overflowY: "auto" }}>
                  {hotspots.slice(0, 5).map((hotspot, idx) => (
                    <HotspotItem key={idx} hotspot={hotspot} />
                  ))}
                </div>
              </Section>

              <Section title="⚠️ Recent High-Risk Events">
                <div style={{ maxHeight: "350px", overflowY: "auto" }}>
                  {allEvents
                    .filter((e) => (e.total_score || 0) >= 0.7)
                    .slice(0, 5)
                    .map((event, idx) => (
                      <EventItem
                        key={idx}
                        event={event}
                        onClick={handleEventClick}
                      />
                    ))}
                </div>
              </Section>
            </div>

            {networkStats && (
              <Section title="📊 Network Summary">
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                    gap: "15px",
                  }}
                >
                  <div
                    style={{
                      padding: "20px",
                      background: "rgba(0, 212, 255, 0.1)",
                      borderRadius: "10px",
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        color: "#00d4ff",
                        fontSize: "2em",
                        fontWeight: "bold",
                      }}
                    >
                      {networkStats.total_vessels}
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.9em" }}>
                      Vessels in Network
                    </div>
                  </div>
                  <div
                    style={{
                      padding: "20px",
                      background: "rgba(0, 212, 255, 0.1)",
                      borderRadius: "10px",
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        color: "#00d4ff",
                        fontSize: "2em",
                        fontWeight: "bold",
                      }}
                    >
                      {networkStats.total_communities}
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.9em" }}>
                      Communities
                    </div>
                  </div>
                  <div
                    style={{
                      padding: "20px",
                      background: "rgba(255, 165, 0, 0.1)",
                      borderRadius: "10px",
                      textAlign: "center",
                    }}
                  >
                    <div
                      style={{
                        color: "#ffa500",
                        fontSize: "2em",
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
          </>
        )}

        {/* Map Tab */}
        {activeTab === "map" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "20px",
                color: "#00d4ff",
              }}
            >
              Interactive Event Map
            </h2>
            <EventMap
              events={allEvents}
              hotspots={hotspots}
              onEventClick={handleEventClick}
            />
          </>
        )}

        {/* Events Tab */}
        {activeTab === "events" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "20px",
                color: "#00d4ff",
              }}
            >
              Suspicious Dark Events
            </h2>

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
                High Risk (≥0.7)
              </FilterButton>
              <FilterButton
                active={activeFilter === "fishing"}
                onClick={() => handleFilter("fishing")}
              >
                Fishing Vessels
              </FilterButton>
              <FilterButton
                active={activeFilter === "rendezvous"}
                onClick={() => handleFilter("rendezvous")}
              >
                Rendezvous Events
              </FilterButton>
            </div>

            <div
              style={{
                color: "#aaa",
                fontSize: "0.9em",
                marginBottom: "15px",
                padding: "12px",
                background: "rgba(0, 212, 255, 0.1)",
                borderRadius: "5px",
              }}
            >
              📊 Showing {filteredEvents.length} of {allEvents.length} events
            </div>

            <div
              style={{ maxHeight: "calc(100vh - 300px)", overflowY: "auto" }}
            >
              {filteredEvents.length > 0 ? (
                filteredEvents.map((event, idx) => (
                  <EventItem
                    key={idx}
                    event={event}
                    onClick={handleEventClick}
                  />
                ))
              ) : (
                <div
                  style={{
                    textAlign: "center",
                    padding: "60px",
                    color: "#aaa",
                    fontSize: "1.2em",
                  }}
                >
                  No events match the selected filter
                </div>
              )}
            </div>
          </>
        )}

        {/* High-Risk Vessels Tab */}
        {activeTab === "vessels" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "30px",
                color: "#00d4ff",
              }}
            >
              High-Risk Vessels
            </h2>

            {motherships.length > 0 && (
              <div style={{ marginBottom: "30px" }}>
                <h3
                  style={{
                    color: "#ff3838",
                    marginBottom: "15px",
                    fontSize: "1.5em",
                  }}
                >
                  🚢 Potential Motherships
                </h3>
                <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                  {motherships.map((mothership, idx) => (
                    <MothershipItem
                      key={idx}
                      mothership={mothership}
                      onClick={handleEventClick}
                    />
                  ))}
                </div>
              </div>
            )}

            {coordinators.length > 0 && (
              <div style={{ marginBottom: "30px" }}>
                <h3
                  style={{
                    color: "#ffa500",
                    marginBottom: "15px",
                    fontSize: "1.5em",
                  }}
                >
                  🎯 Coordinator Vessels
                </h3>
                <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                  {coordinators.map((coordinator, idx) => (
                    <CoordinatorItem
                      key={idx}
                      coordinator={coordinator}
                      onClick={handleEventClick}
                    />
                  ))}
                </div>
              </div>
            )}

            {hotspots.length > 0 && (
              <div>
                <h3
                  style={{
                    color: "#00d4ff",
                    marginBottom: "15px",
                    fontSize: "1.5em",
                  }}
                >
                  🔥 Dark Zone Hotspots
                </h3>
                <div style={{ maxHeight: "400px", overflowY: "auto" }}>
                  {hotspots.map((hotspot, idx) => (
                    <HotspotItem key={idx} hotspot={hotspot} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Network Analysis Tab */}
        {activeTab === "network" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "30px",
                color: "#00d4ff",
              }}
            >
              Network Analysis
            </h2>

            {networkStats && (
              <div style={{ marginBottom: "30px" }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    gap: "20px",
                  }}
                >
                  <div
                    style={{
                      padding: "25px",
                      background: "rgba(0, 212, 255, 0.1)",
                      borderRadius: "15px",
                    }}
                  >
                    <div
                      style={{
                        color: "#00d4ff",
                        fontSize: "2.5em",
                        fontWeight: "bold",
                        marginBottom: "10px",
                      }}
                    >
                      {networkStats.total_vessels}
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.1em",
                        marginBottom: "5px",
                      }}
                    >
                      Total Vessels
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.85em" }}>
                      Vessels with dark event connections
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "25px",
                      background: "rgba(0, 212, 255, 0.1)",
                      borderRadius: "15px",
                    }}
                  >
                    <div
                      style={{
                        color: "#00d4ff",
                        fontSize: "2.5em",
                        fontWeight: "bold",
                        marginBottom: "10px",
                      }}
                    >
                      {networkStats.total_communities}
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.1em",
                        marginBottom: "5px",
                      }}
                    >
                      Communities
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.85em" }}>
                      Detected vessel groups
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "25px",
                      background: "rgba(255, 165, 0, 0.1)",
                      borderRadius: "15px",
                    }}
                  >
                    <div
                      style={{
                        color: "#ffa500",
                        fontSize: "2.5em",
                        fontWeight: "bold",
                        marginBottom: "10px",
                      }}
                    >
                      {networkStats.suspicious_fleets}
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.1em",
                        marginBottom: "5px",
                      }}
                    >
                      Suspicious Fleets
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.85em" }}>
                      High-risk communities
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "25px",
                      background: "rgba(0, 255, 136, 0.1)",
                      borderRadius: "15px",
                    }}
                  >
                    <div
                      style={{
                        color: "#00ff88",
                        fontSize: "2.5em",
                        fontWeight: "bold",
                        marginBottom: "10px",
                      }}
                    >
                      {networkStats.avg_degree_centrality?.toFixed(3)}
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.1em",
                        marginBottom: "5px",
                      }}
                    >
                      Avg Degree
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.85em" }}>
                      Connection density
                    </div>
                  </div>

                  <div
                    style={{
                      padding: "25px",
                      background: "rgba(0, 255, 136, 0.1)",
                      borderRadius: "15px",
                    }}
                  >
                    <div
                      style={{
                        color: "#00ff88",
                        fontSize: "2.5em",
                        fontWeight: "bold",
                        marginBottom: "10px",
                      }}
                    >
                      {networkStats.avg_betweenness_centrality?.toFixed(3)}
                    </div>
                    <div
                      style={{
                        color: "#fff",
                        fontSize: "1.1em",
                        marginBottom: "5px",
                      }}
                    >
                      Avg Betweenness
                    </div>
                    <div style={{ color: "#aaa", fontSize: "0.85em" }}>
                      Network bridge importance
                    </div>
                  </div>
                </div>
              </div>
            )}

            {communities.length > 0 && (
              <div>
                <h3
                  style={{
                    color: "#00d4ff",
                    marginBottom: "15px",
                    fontSize: "1.8em",
                  }}
                >
                  🌐 Suspicious Communities
                </h3>
                <div
                  style={{
                    maxHeight: "calc(100vh - 500px)",
                    overflowY: "auto",
                  }}
                >
                  {communities.map((community, idx) => (
                    <CommunityItem key={idx} community={community} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Vessel Details Modal */}
      {selectedVessel && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 2000,
            padding: "20px",
          }}
          onClick={() => setSelectedVessel(null)}
        >
          <div
            style={{
              background: "linear-gradient(135deg, #1a2a3a 0%, #2c3e50 100%)",
              borderRadius: "15px",
              padding: "50px 30px 30px 30px",
              maxWidth: "900px",
              width: "100%",
              maxHeight: "90vh",
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
                background: "#ff3b30",
                border: "none",
                color: "#fff",
                padding: "12px 24px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "1em",
                fontWeight: "bold",
                zIndex: 10,
                boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = "#ff5c54")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = "#ff3b30")
              }
            >
              ✕ Close
            </button>

            <h2
              style={{
                color: "#00d4ff",
                marginBottom: "25px",
                fontSize: "2.2em",
              }}
            >
              🚢 Vessel: {selectedVessel.mmsi}
            </h2>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "15px",
                marginBottom: "30px",
              }}
            >
              <div
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  padding: "18px",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#aaa",
                    fontSize: "0.85em",
                    marginBottom: "8px",
                  }}
                >
                  Vessel Name
                </div>
                <div
                  style={{
                    color: "#fff",
                    fontSize: "1.3em",
                    fontWeight: "bold",
                  }}
                >
                  {selectedVessel.vessel_name || "Unknown"}
                </div>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  padding: "18px",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#aaa",
                    fontSize: "0.85em",
                    marginBottom: "8px",
                  }}
                >
                  Type
                </div>
                <div
                  style={{
                    color: "#00ff88",
                    fontSize: "1.3em",
                    fontWeight: "bold",
                  }}
                >
                  {selectedVessel.is_fishing_vessel ? "🎣 Fishing" : "🚢 Other"}
                </div>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  padding: "18px",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#aaa",
                    fontSize: "0.85em",
                    marginBottom: "8px",
                  }}
                >
                  Dark Events
                </div>
                <div
                  style={{
                    color: "#ffa500",
                    fontSize: "1.3em",
                    fontWeight: "bold",
                  }}
                >
                  {selectedVessel.total_dark_events}
                </div>
              </div>

              <div
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  padding: "18px",
                  borderRadius: "10px",
                }}
              >
                <div
                  style={{
                    color: "#aaa",
                    fontSize: "0.85em",
                    marginBottom: "8px",
                  }}
                >
                  Avg Suspicion
                </div>
                <div
                  style={{
                    color: "#ff3838",
                    fontSize: "1.3em",
                    fontWeight: "bold",
                  }}
                >
                  {selectedVessel.avg_suspicion_score?.toFixed(3)}
                </div>
              </div>
            </div>

            <h3
              style={{
                color: "#00d4ff",
                marginBottom: "15px",
                fontSize: "1.5em",
              }}
            >
              Event History ({selectedVessel.events?.length || 0})
            </h3>

            <div style={{ maxHeight: "350px", overflowY: "auto" }}>
              {selectedVessel.events?.map((event, idx) => (
                <div
                  key={idx}
                  style={{
                    background: "rgba(255, 255, 255, 0.03)",
                    padding: "15px",
                    marginBottom: "10px",
                    borderRadius: "8px",
                    borderLeft: `4px solid ${
                      event.total_score >= 0.7 ? "#ff3838" : "#ffa500"
                    }`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "10px",
                    }}
                  >
                    <span
                      style={{
                        color: "#00d4ff",
                        fontWeight: "bold",
                        fontSize: "1.1em",
                      }}
                    >
                      Event #{idx + 1}
                    </span>
                    <span
                      style={{
                        color: "#ff3838",
                        fontSize: "1.1em",
                        fontWeight: "bold",
                      }}
                    >
                      {event.total_score?.toFixed(3)}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: "0.9em",
                      color: "#ccc",
                      marginBottom: "5px",
                    }}
                  >
                    📍 [{event.location?.[0]?.toFixed(2)},{" "}
                    {event.location?.[1]?.toFixed(2)}] | ⏱️{" "}
                    {event.duration_hours?.toFixed(1)}h | 🌍{" "}
                    {event.region || "Unknown"}
                  </div>
                  <div style={{ fontSize: "0.85em", color: "#888" }}>
                    {new Date(event.start).toLocaleString()} →{" "}
                    {new Date(event.end).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
