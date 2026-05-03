import React, { useState } from "react";
import { Search, Pin } from "lucide-react";
import { searchLegal, getGlossaryTerm } from "../services/api";
import CitationCard from "./CitationCard";
import SourceViewer from "./SourceViewer";

export default function SourcesPanel({ sources, onDocumentClick }) {
  const [searchQ, setSearchQ]     = useState("");
  const [results, setResults]     = useState([]);
  const [glossary, setGlossary]   = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError]         = useState("");
  const [viewSource, setViewSource] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQ.trim()) return;
    setSearching(true); setError(""); setGlossary(null);
    try {
      const data = await searchLegal(searchQ);
      setResults(data.results);
    } catch {
      setError("Search failed. Is the backend running?");
    } finally {
      setSearching(false);
    }
  };

  const lookupGlossary = async (term) => {
    setError("");
    try {
      const data = await getGlossaryTerm(term);
      setGlossary(data);
    } catch {
      setError(`Term "${term}" not found in glossary.`);
    }
  };

  // Map search result to Source-like shape for CitationCard
  const toSource = (r) => ({
    title: r.title,
    type: r.type,
    citation: r.citation || "",
    excerpt: r.snippet || "",
    page: "",
  });

  return (
    <div className="panel">
      <h3 className="panel-title">
        <Search size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
        Legal Search
      </h3>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          className="search-input"
          placeholder="Search cases, statutes…"
          value={searchQ}
          onChange={(e) => setSearchQ(e.target.value)}
        />
        <button className="search-btn" type="submit" disabled={searching}>
          {searching ? "…" : "Go"}
        </button>
      </form>

      {error && <p className="panel-error">{error}</p>}

      {results.length > 0 && (
        <div style={{ marginTop: "0.75rem" }}>
          {results.map((r, i) => (
            <CitationCard
              key={i}
              source={toSource(r)}
              onViewSource={() => setViewSource(toSource(r))}
            />
          ))}
        </div>
      )}

      {sources && sources.length > 0 && (
        <>
          <h3 className="panel-title" style={{ marginTop: "1.5rem" }}>
            <Pin size={18} style={{ verticalAlign: "middle", marginRight: 8 }} />
            Chat Sources
          </h3>
          {sources.map((src, i) => (
            <CitationCard
              key={i}
              source={src}
              onViewSource={() => setViewSource(src)}
            />
          ))}
        </>
      )}

      {!sources?.length && !results.length && (
        <p style={{ color: "#9ca3af", fontSize: "0.875rem", marginTop: "1rem" }}>
          Sources from your last message will appear here.
        </p>
      )}

      {glossary && (
        <div className="glossary-card">
          <div className="glossary-header">
            <strong>{glossary.term}</strong>
            <button className="close-btn" onClick={() => setGlossary(null)}>✕</button>
          </div>
          <p>{glossary.definition}</p>
          <p className="glossary-example"><em>Example: {glossary.example}</em></p>
        </div>
      )}

      {viewSource && (
        <SourceViewer source={viewSource} onClose={() => setViewSource(null)} />
      )}
    </div>
  );
}
