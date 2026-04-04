import React, { useEffect, useState } from "react";
import { BrainCircuit, Flower2 } from "lucide-react";
import { getTemplates } from "../services/api";

const COLORS = ["var(--intent-definition)", "var(--intent-caselaw)", "var(--intent-statute)", "var(--intent-irac)"];

export default function TemplatesPanel({ onUseTemplate }) {
  const [templates, setTemplates] = useState([]);

  useEffect(() => {
    getTemplates()
      .then((data) => setTemplates(data.templates))
      .catch(() => {});
  }, []);

  return (
    <div className="panel">
      <h3 className="panel-title"><BrainCircuit size={20} style={{verticalAlign: "middle", marginRight: 8}}/> Reasoning Templates</h3>
      <p className="panel-sub">
        Apply structured legal reasoning frameworks to analyse any scenario.
        Click a template to start.
      </p>

      {templates.map((tpl, i) => (
        <div key={i} className="template-card" style={{ borderLeft: `4px solid ${COLORS[i % COLORS.length]}` }}>
          <div className="template-header">
            <strong>{tpl.name}</strong>
            <button
              className="use-btn"
              style={{ background: COLORS[i % COLORS.length] }}
              onClick={() => onUseTemplate(`Apply ${tpl.name} method to: `)}
            >
              Use Template
            </button>
          </div>
          <div className="template-steps">
            {tpl.structure.map((step, j) => (
              <span key={j} className="step-chip">
                <span className="step-num">{j + 1}</span> {step}
              </span>
            ))}
          </div>
        </div>
      ))}

      <div className="iks-note">
        <span><Flower2 size={24} color="var(--intent-idar)" /></span>
        <p>
          <strong>IDAR</strong> is a Dharma-based reasoning template rooted in the Indian Knowledge System —
          applying <em>Dharma</em> (the applicable rule of righteousness) and <em>Danda</em> (the theory of
          state sanction) to legal analysis. This framework bridges ancient jurisprudence with modern law.
        </p>
      </div>
    </div>
  );
}
