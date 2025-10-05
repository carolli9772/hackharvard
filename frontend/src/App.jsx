import React, { useState, useEffect, useMemo } from "react";
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
import { Pagination } from "./components/Pagination";

const API_BASE = "http://localhost:5001/api";

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
  const [mapEvents, setMapEvents] = useState([]);
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
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(25);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadStats(),
        loadEvents(),
        loadMapEvents(),
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
    const response = await fetch(`${API_BASE}/suspicious-events?limit=100000`);
    const data = await response.json();
    setAllEvents(data.events || []);
    setFilteredEvents(data.events || []);
  };

  const loadMapEvents = async () => {
    const response = await fetch(
      `${API_BASE}/suspicious-events/top?limit=5000`
    );
    const data = await response.json();
    setMapEvents(data.events || []);
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
    setCurrentPage(1);
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

  const searchedEvents = useMemo(() => {
    if (!searchTerm.trim()) return filteredEvents;
    const lowerSearch = searchTerm.toLowerCase();
    return filteredEvents.filter((event) => {
      return (
        event.mmsi?.toString().includes(lowerSearch) ||
        event.region?.toLowerCase().includes(lowerSearch) ||
        event.vessel_name?.toLowerCase().includes(lowerSearch)
      );
    });
  }, [filteredEvents, searchTerm]);

  const totalPages = Math.ceil(searchedEvents.length / itemsPerPage);
  const paginatedEvents = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return searchedEvents.slice(startIndex, startIndex + itemsPerPage);
  }, [searchedEvents, currentPage, itemsPerPage]);

  const handlePageChange = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1);
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
            active={activeTab === "hotspots"}
            onClick={() => setActiveTab("hotspots")}
            icon="🔥"
          >
            {!sidebarCollapsed && "Hotspots"}
          </SidebarItem>
        </div>

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

      <div
        style={{
          marginLeft: sidebarCollapsed ? "80px" : "280px",
          width: `calc(100% - ${sidebarCollapsed ? "80px" : "280px"})`,
          transition: "margin-left 0.3s, width 0.3s",
          padding: "20px",
          overflow: "hidden",
          height: "100vh",
        }}
      >
        {error && <ErrorMessage message={error} />}

        {activeTab === "overview" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "20px",
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
                marginBottom: "25px",
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
                </>
              )}
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "20px",
                paddingBottom: "20px",
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
          </>
        )}

        {activeTab === "map" && (
          <>
            <h2
              style={{
                fontSize: "2.5em",
                marginBottom: "15px",
                color: "#00d4ff",
              }}
            >
              Interactive Event Map
            </h2>
            <div
              style={{
                padding: "10px 15px",
                background: "rgba(0, 212, 255, 0.1)",
                borderRadius: "8px",
                marginBottom: "15px",
                border: "1px solid rgba(0, 212, 255, 0.3)",
              }}
            >
              <strong style={{ color: "#00d4ff" }}>💡 Smart Loading:</strong>
              <span style={{ color: "#ccc", marginLeft: "10px" }}>
                Events load dynamically based on your zoom level and visible
                area. Zoom in to see more detail!
              </span>
            </div>
            <div style={{ paddingBottom: "20px" }}>
              <EventMap
                events={mapEvents}
                hotspots={hotspots}
                onEventClick={handleEventClick}
              />
            </div>
          </>
        )}

        {activeTab === "events" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              height: "calc(100vh - 40px)",
            }}
          >
            <div style={{ flexShrink: 0 }}>
              <h2
                style={{
                  fontSize: "2.5em",
                  marginBottom: "15px",
                  color: "#00d4ff",
                }}
              >
                Suspicious Dark Events
              </h2>
              <div style={{ marginBottom: "15px" }}>
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setCurrentPage(1);
                  }}
                  placeholder="🔍 Search by MMSI, region, or vessel name..."
                  style={{
                    width: "100%",
                    padding: "12px 20px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(0, 212, 255, 0.3)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "1em",
                    outline: "none",
                  }}
                  onFocus={(e) =>
                    (e.currentTarget.style.borderColor = "#00d4ff")
                  }
                  onBlur={(e) =>
                    (e.currentTarget.style.borderColor =
                      "rgba(0, 212, 255, 0.3)")
                  }
                />
              </div>
              <div
                style={{
                  display: "flex",
                  gap: "15px",
                  marginBottom: "15px",
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
              </div>
              <div
                style={{
                  color: "#aaa",
                  fontSize: "0.9em",
                  marginBottom: "12px",
                  padding: "10px 15px",
                  background: "rgba(0, 212, 255, 0.1)",
                  borderRadius: "5px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>
                  📊{" "}
                  {searchTerm
                    ? `Found ${searchedEvents.length} results`
                    : `${filteredEvents.length} events`}
                </span>
                <span style={{ fontSize: "0.85em" }}>
                  Total: {allEvents.length.toLocaleString()}
                </span>
              </div>
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                marginBottom: "10px",
                paddingRight: "5px",
                minHeight: 0,
              }}
            >
              {paginatedEvents.length > 0 ? (
                paginatedEvents.map((event, idx) => (
                  <EventItem
                    key={`${event.mmsi}-${idx}`}
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
                  {searchTerm
                    ? "🔍 No events match your search"
                    : "No events match the selected filter"}
                </div>
              )}
            </div>
            <div style={{ flexShrink: 0, paddingTop: "5px" }}>
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={searchedEvents.length}
                itemsPerPage={itemsPerPage}
                onPageChange={handlePageChange}
                onItemsPerPageChange={handleItemsPerPageChange}
              />
            </div>
          </div>
        )}

        {activeTab === "hotspots" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              height: "calc(100vh - 40px)",
            }}
          >
            <div style={{ flexShrink: 0 }}>
              <h2
                style={{
                  fontSize: "2.5em",
                  marginBottom: "20px",
                  color: "#00d4ff",
                }}
              >
                Dark Zone Hotspots
              </h2>
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                paddingRight: "5px",
                minHeight: 0,
              }}
            >
              {hotspots.length > 0 && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
                    gap: "20px",
                    paddingBottom: "20px",
                  }}
                >
                  {hotspots.map((hotspot, idx) => (
                    <HotspotItem key={idx} hotspot={hotspot} />
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

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
            overflow: "hidden",
          }}
          onClick={() => setSelectedVessel(null)}
        >
          <div
            style={{
              background: "linear-gradient(135deg, #1a2a3a 0%, #2c3e50 100%)",
              borderRadius: "15px",
              padding: "30px",
              maxWidth: "900px",
              width: "100%",
              maxHeight: "85vh",
              display: "flex",
              flexDirection: "column",
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
            >
              ✕ Close
            </button>

            <div
              style={{
                flexShrink: 0,
                marginBottom: "20px",
                paddingTop: "20px",
              }}
            >
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
                    {selectedVessel.is_fishing_vessel
                      ? "🎣 Fishing"
                      : "🚢 Other"}
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
            </div>

            <div style={{ flexShrink: 0, marginBottom: "10px" }}>
              <h3 style={{ color: "#00d4ff", fontSize: "1.5em" }}>
                Event History ({selectedVessel.events?.length || 0})
              </h3>
            </div>

            <div
              style={{
                flex: 1,
                overflowY: "auto",
                minHeight: 0,
                paddingRight: "5px",
              }}
            >
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
