import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:5001/api";

// Stat Card Component
const StatCard = ({ label, value, unit = "" }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.1)",
      backdropFilter: "blur(10px)",
      borderRadius: "15px",
      padding: "25px",
      border: "1px solid rgba(255, 255, 255, 0.2)",
    }}
  >
    <div
      style={{
        color: "#aaa",
        fontSize: "0.9em",
        textTransform: "uppercase",
        letterSpacing: "1px",
        marginBottom: "10px",
      }}
    >
      {label}
    </div>
    <div
      style={{
        fontSize: "2.5em",
        fontWeight: "bold",
        color: "#00ff88",
      }}
    >
      {value}
      {unit}
    </div>
  </div>
);

// Event Item Component
const EventItem = ({ event }) => {
  const score = event.total_score || 0;
  const suspicionClass =
    score >= 0.7 ? "#ff3838" : score >= 0.4 ? "#ffa500" : "#4ecdc4";
  const location = event.location
    ? `[${event.location[0].toFixed(2)}, ${event.location[1].toFixed(2)}]`
    : "Unknown";

  return (
    <div
      style={{
        background: "rgba(255, 255, 255, 0.05)",
        borderLeft: `4px solid ${suspicionClass}`,
        padding: "15px",
        marginBottom: "10px",
        borderRadius: "5px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginBottom: "10px",
        }}
      >
        <span style={{ fontWeight: "bold", color: "#00d4ff" }}>
          MMSI: {event.mmsi}
        </span>
        <span
          style={{
            background: "rgba(255, 59, 48, 0.3)",
            padding: "3px 10px",
            borderRadius: "12px",
            fontSize: "0.9em",
          }}
        >
          Score: {score.toFixed(3)}
        </span>
      </div>
      <div style={{ fontSize: "0.9em", color: "#ccc" }}>
        📍 {location} | ⏱️ {event.duration_hours?.toFixed(1)}h |
        {event.is_fishing_vessel ? " 🎣 Fishing Vessel" : " 🚢 Other Vessel"} |
        📅 {new Date(event.start).toLocaleDateString()}
      </div>
    </div>
  );
};

// Community Item Component
const CommunityItem = ({ community }) => (
  <div
    style={{
      background: "rgba(255, 255, 255, 0.05)",
      borderLeft: "4px solid #00d4ff",
      padding: "15px",
      marginBottom: "10px",
      borderRadius: "5px",
    }}
  >
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        marginBottom: "10px",
      }}
    >
      <span style={{ fontWeight: "bold", color: "#00d4ff" }}>
        Community {community.community_id}
      </span>
      <span
        style={{
          background: "rgba(0, 212, 255, 0.3)",
          padding: "3px 10px",
          borderRadius: "12px",
          fontSize: "0.9em",
        }}
      >
        Avg Score: {community.avg_suspicion_score?.toFixed(3)}
      </span>
    </div>
    <div style={{ fontSize: "0.9em", color: "#ccc" }}>
      👥 {community.vessel_count} vessels | 🎣 {community.fishing_vessel_count}{" "}
      fishing vessels | 🔗 {community.internal_connections} connections
    </div>
  </div>
);

// Filter Button Component
const FilterButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    style={{
      background: active ? "#00d4ff" : "rgba(0, 212, 255, 0.2)",
      border: "1px solid #00d4ff",
      color: active ? "#0f2027" : "#00d4ff",
      padding: "10px 20px",
      borderRadius: "25px",
      cursor: "pointer",
      transition: "all 0.3s",
      fontSize: "1em",
    }}
  >
    {children}
  </button>
);

// Main Dashboard Component
export default function FishNetDashboard() {
  const [stats, setStats] = useState(null);
  const [allEvents, setAllEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [communities, setCommunities] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load stats
  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetch(`${API_BASE}/summary`);
        const data = await response.json();
        setStats(data);
      } catch (err) {
        setError(
          "Error loading statistics. Make sure the API server is running."
        );
      }
    };
    loadStats();
  }, []);

  // Load events
  useEffect(() => {
    const loadEvents = async () => {
      try {
        const response = await fetch(`${API_BASE}/suspicious-events?limit=50`);
        const data = await response.json();
        setAllEvents(data.events || []);
        setFilteredEvents(data.events || []);
      } catch (err) {
        setError("Error loading events. Make sure the API server is running.");
      } finally {
        setLoading(false);
      }
    };
    loadEvents();
  }, []);

  // Load communities
  useEffect(() => {
    const loadCommunities = async () => {
      try {
        const response = await fetch(`${API_BASE}/communities?limit=5`);
        const data = await response.json();
        setCommunities(data.communities || []);
      } catch (err) {
        console.error("Error loading communities:", err);
      }
    };
    loadCommunities();
  }, []);

  // Filter events
  const handleFilter = (type) => {
    setActiveFilter(type);
    let filtered = allEvents;

    if (type === "high") {
      filtered = allEvents.filter((e) => (e.total_score || 0) >= 0.7);
    } else if (type === "fishing") {
      filtered = allEvents.filter((e) => e.is_fishing_vessel);
    }

    setFilteredEvents(filtered);
  };

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
      }}
    >
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        {/* Header */}
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
            Illegal Fishing Detection via AIS Silence Patterns
          </p>
        </header>

        {/* Stats Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: "20px",
            marginBottom: "40px",
          }}
        >
          {stats ? (
            <>
              <StatCard
                label="Total Dark Events"
                value={stats.total_dark_events?.toLocaleString() || "N/A"}
              />
              <StatCard
                label="High Suspicion Events"
                value={stats.high_suspicion_events?.toLocaleString() || "N/A"}
              />
              <StatCard
                label="Fishing Vessels"
                value={stats.fishing_vessel_events?.toLocaleString() || "N/A"}
              />
              <StatCard
                label="Suspicious Communities"
                value={stats.suspicious_communities?.toLocaleString() || "N/A"}
              />
              <StatCard
                label="Potential Motherships"
                value={stats.potential_motherships?.toLocaleString() || "N/A"}
              />
              <StatCard
                label="Avg Duration"
                value={stats.avg_duration_hours?.toFixed(1) || "N/A"}
                unit="h"
              />
            </>
          ) : (
            <div
              style={{
                color: "#aaa",
                padding: "40px",
                textAlign: "center",
                gridColumn: "1 / -1",
              }}
            >
              {error || "Loading statistics..."}
            </div>
          )}
        </div>

        {/* Map Section */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: "15px",
            padding: "30px",
            marginBottom: "30px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <h2
            style={{
              fontSize: "1.5em",
              marginBottom: "20px",
              color: "#00d4ff",
            }}
          >
            🗺️ Suspicious Dark Zone Heatmap
          </h2>
          <div
            style={{
              background: "rgba(0, 0, 0, 0.3)",
              borderRadius: "10px",
              height: "400px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#666",
            }}
          >
            Map visualization (integrate with Leaflet, Mapbox, or deck.gl)
          </div>
        </div>

        {/* Events Section */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: "15px",
            padding: "30px",
            marginBottom: "30px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <h2
            style={{
              fontSize: "1.5em",
              marginBottom: "20px",
              color: "#00d4ff",
            }}
          >
            ⚠️ Top Suspicious Events
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
              All
            </FilterButton>
            <FilterButton
              active={activeFilter === "high"}
              onClick={() => handleFilter("high")}
            >
              High Suspicion
            </FilterButton>
            <FilterButton
              active={activeFilter === "fishing"}
              onClick={() => handleFilter("fishing")}
            >
              Fishing Vessels Only
            </FilterButton>
          </div>

          <div style={{ maxHeight: "400px", overflowY: "auto" }}>
            {loading ? (
              <div
                style={{ textAlign: "center", padding: "40px", color: "#aaa" }}
              >
                Loading events...
              </div>
            ) : filteredEvents.length > 0 ? (
              filteredEvents.map((event, idx) => (
                <EventItem key={idx} event={event} />
              ))
            ) : (
              <div
                style={{ textAlign: "center", padding: "40px", color: "#aaa" }}
              >
                No events found
              </div>
            )}
          </div>
        </div>

        {/* Communities Section */}
        <div
          style={{
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(10px)",
            borderRadius: "15px",
            padding: "30px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
          }}
        >
          <h2
            style={{
              fontSize: "1.5em",
              marginBottom: "20px",
              color: "#00d4ff",
            }}
          >
            🌐 Vessel Networks & Communities
          </h2>
          <div>
            {communities.length > 0 ? (
              communities.map((community, idx) => (
                <CommunityItem key={idx} community={community} />
              ))
            ) : (
              <div
                style={{ textAlign: "center", padding: "40px", color: "#aaa" }}
              >
                Loading communities...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
