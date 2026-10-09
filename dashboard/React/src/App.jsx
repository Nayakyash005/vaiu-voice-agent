import React, { useCallback, useEffect, useMemo, useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/phone";

function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export default function App() {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(API_URL);
      if (!response.ok) throw new Error(`Request failed (${response.status})`);
      const data = await response.json();
      if (!Array.isArray(data)) throw new Error("Unexpected response from the API.");
      setRecords(data);
    } catch (err) {
      setError(`Could not load phone records. ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return records;
    return records.filter((record) => String(record.parsedNumber ?? "").toLowerCase().includes(query));
  }, [records, search]);

  async function deleteRecord(id) {
    setDeletingId(id);
    setError("");
    try {
      const response = await fetch(`${API_URL}/${id}`, { method: "DELETE" });
      if (!response.ok) {
        if (response.status === 404) throw new Error("This record was already removed.");
        throw new Error(`Request failed (${response.status})`);
      }
      setRecords((current) => current.filter((record) => record.id !== id));
    } catch (err) {
      setError(`Could not delete the record. ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="VAIU dashboard home">
          <span className="brand-mark">V</span>
          <span>VAIU<span className="brand-subtitle">VOICE DASHBOARD</span></span>
        </a>
        <span className="connection"><span className="status-dot" /> Phone records</span>
      </header>

      <section className="content" id="top">
        <div className="intro">
          <div>
            <p className="eyebrow">COLLECTION OVERVIEW</p>
            <h1>Phone records</h1>
            <p className="subtitle">Review and manage numbers collected by the VAIU voice agent.</p>
          </div>
          <div className="count-card" aria-live="polite">
            <span className="count-label">TOTAL RECORDS</span>
            <strong>{records.length}</strong>
          </div>
        </div>

        <section className="records-card" aria-label="Phone records">
          <div className="toolbar">
            <div>
              <h2>All records</h2>
              <p>{search ? `${filteredRecords.length} matching records` : "Saved phone numbers"}</p>
            </div>
            <label className="search-box">
              <span className="search-icon" aria-hidden="true">⌕</span>
              <input
                type="search"
                placeholder="Search phone number"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                aria-label="Search phone number"
              />
            </label>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button className="text-button" onClick={loadRecords}>Retry</button>
            </div>
          )}

          {loading ? (
            <div className="state-panel"><span className="spinner" />Loading records…</div>
          ) : records.length === 0 ? (
            <div className="state-panel empty-state">
              <span className="empty-icon">↗</span>
              <strong>No phone records yet</strong>
              <span>Confirmed numbers will appear here.</span>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="state-panel empty-state">
              <strong>No matching numbers</strong>
              <span>Try another phone number.</span>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>PHONE NUMBER</th>
                    <th>LANGUAGE</th>
                    <th>COLLECTED</th>
                    <th>TRANSCRIPT</th>
                    <th><span className="sr-only">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.map((record) => (
                    <tr key={record.id}>
                      <td className="number-cell">{record.parsedNumber}</td>
                      <td><span className="language-tag">{record.language || "unknown"}</span></td>
                      <td className="date-cell">{formatDate(record.collectedAt)}</td>
                      <td className="transcript-cell" title={record.rawTranscript}>{record.rawTranscript || "—"}</td>
                      <td className="action-cell">
                        <button
                          className="delete-button"
                          onClick={() => deleteRecord(record.id)}
                          disabled={deletingId === record.id}
                          aria-label={`Delete record for ${record.parsedNumber}`}
                        >
                          {deletingId === record.id ? "Deleting…" : "Delete"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <footer className="card-footer">Showing {filteredRecords.length} of {records.length} records</footer>
        </section>
        <p className="page-note">VAIU · Voice powered phone collection</p>
      </section>
    </main>
  );
}
