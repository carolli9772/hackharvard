import React from "react";

export const Pagination = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onItemsPerPageChange,
}) => {
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 4) {
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push("...");
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 3) {
        pages.push(1);
        pages.push("...");
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push("...");
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push("...");
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 15px",
        background: "rgba(255, 255, 255, 0.05)",
        borderRadius: "10px",
        flexWrap: "wrap",
        gap: "10px",
      }}
    >
      {/* Items per page selector */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span style={{ color: "#aaa", fontSize: "0.9em" }}>Show:</span>
        <select
          value={itemsPerPage}
          onChange={(e) => onItemsPerPageChange(Number(e.target.value))}
          style={{
            background: "rgba(255, 255, 255, 0.1)",
            border: "1px solid #00d4ff",
            color: "#fff",
            padding: "8px 12px",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          <option value={10}>10</option>
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
        <span style={{ color: "#aaa", fontSize: "0.9em" }}>
          Showing {Math.min((currentPage - 1) * itemsPerPage + 1, totalItems)} -{" "}
          {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems}
        </span>
      </div>

      {/* Page buttons */}
      <div style={{ display: "flex", gap: "5px", alignItems: "center" }}>
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          style={{
            background:
              currentPage === 1
                ? "rgba(255, 255, 255, 0.05)"
                : "rgba(0, 212, 255, 0.2)",
            border: "1px solid #00d4ff",
            color: currentPage === 1 ? "#666" : "#00d4ff",
            padding: "8px 12px",
            borderRadius: "5px",
            cursor: currentPage === 1 ? "not-allowed" : "pointer",
            fontSize: "0.9em",
          }}
        >
          ← Prev
        </button>

        {getPageNumbers().map((page, idx) =>
          page === "..." ? (
            <span
              key={`ellipsis-${idx}`}
              style={{ color: "#666", padding: "0 5px" }}
            >
              ...
            </span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              style={{
                background:
                  currentPage === page
                    ? "#00d4ff"
                    : "rgba(255, 255, 255, 0.05)",
                border: "1px solid #00d4ff",
                color: currentPage === page ? "#0f2027" : "#00d4ff",
                padding: "8px 12px",
                borderRadius: "5px",
                cursor: "pointer",
                fontWeight: currentPage === page ? "bold" : "normal",
                minWidth: "40px",
              }}
            >
              {page}
            </button>
          )
        )}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          style={{
            background:
              currentPage === totalPages
                ? "rgba(255, 255, 255, 0.05)"
                : "rgba(0, 212, 255, 0.2)",
            border: "1px solid #00d4ff",
            color: currentPage === totalPages ? "#666" : "#00d4ff",
            padding: "8px 12px",
            borderRadius: "5px",
            cursor: currentPage === totalPages ? "not-allowed" : "pointer",
            fontSize: "0.9em",
          }}
        >
          Next →
        </button>
      </div>
    </div>
  );
};
