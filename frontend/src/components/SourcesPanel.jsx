import React, { useState } from "react";
import { Search, Scale, ScrollText, BookOpen, FileText, Pin } from "lucide-react";
import { searchLegal, getGlossaryTerm } from "../services/api";

const getTypeIcon = (type) => {
  if (type === "case") return <Scale size={16} />;
  if (type === "statute") return <ScrollText size={16} />;
  if (type === "glossary") return <BookOpen size={16} />;
  return <FileText size={16} />;
};

export default function SourcesPanel({ sources, onDocumentClick }) {
  const [searchQ, setSearchQ]     = useState("");
  const [results, setResults]     = useState([]);
  const [glossary, setGlossary]   = useState(null);
  const [searching, setSearching] = useState(false);
  const [error, setError]         = useState("");

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

  return (
    <div className="panel">
      <h3 className="panel-title"><Search size={18} style={{verticalAlign: "middle", marginRight: 8}}/> Legal Search</h3>

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

      {/* Search results */}
      {results.length > 0 && (
        <div className="search-results">
          {results.map((r, i) => (
            <div key={i} className="result-card" onClick={() => onDocumentClick?.(r.title)} style={{cursor: "pointer"}}>
              <div className="result-header">
                <span style={{ display: "flex", alignItems: "center" }}>{getTypeIcon(r.type)}</span>
                <strong>{r.title}</strong>
                <span className={`type-tag type-${r.type}`}>{r.type}</span>
              </div>
              <p className="result-snippet">{r.snippet}</p>
            </div>
          ))}
        </div>
      )}

      {/* Current chat sources */}
      {sources && sources.length > 0 && (
        <>
          <h3 className="panel-title" style={{ marginTop: "1.5rem" }}><Pin size={18} style={{verticalAlign: "middle", marginRight: 8}}/> Chat Sources</h3>
          {sources.map((src, i) => (
            <div key={i} className="result-card" onClick={() => onDocumentClick?.(src.title)} style={{cursor: "pointer"}}>
              <div className="result-header">
                <span style={{ display: "flex", alignItems: "center" }}>{getTypeIcon(src.type)}</span>
                <strong>{src.title}</strong>
                <span className={`type-tag type-${src.type}`}>{src.type}</span>
              </div>
              {src.citation && <p className="result-snippet">{src.citation}</p>}
              {src.type === "glossary" && (
                <button className="lookup-btn" onClick={(e) => { e.stopPropagation(); lookupGlossary(src.title); }}>
                  Look up definition
                </button>
              )}
            </div>
          ))}
        </>
      )}

      {/* Glossary popup */}
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
    </div>
  );
}
