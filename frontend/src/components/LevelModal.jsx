import React, { useState } from "react";
import { GraduationCap, Award, BookOpen, Briefcase, Check } from "lucide-react";
import Logo from "./Logo";
import { useAuth } from "../contexts/AuthContext";
import { updateProfile } from "../services/api";

const LEVELS = [
  { 
    value: "beginner", 
    label: "Beginner Student", 
    desc: "1st–2nd year law student. Prefers foundational explanations and defined jargon.", 
    icon: <GraduationCap size={20} /> 
  },
  { 
    value: "advanced", 
    label: "Advanced Student", 
    desc: "3rd–5th year law student. Prefers deep legal analysis and doctrinal details.", 
    icon: <BookOpen size={20} /> 
  },
  { 
    value: "academician", 
    label: "Academician", 
    desc: "Professor or researcher. Prefers exhaustive research, citations, and policy analysis.", 
    icon: <Award size={20} /> 
  },
  { 
    value: "practitioner", 
    label: "Practitioner", 
    desc: "Practicing lawyer or advocate. Prefers precise legal tests, case strategies, and procedural advice.", 
    icon: <Briefcase size={20} /> 
  },
];

export default function LevelModal({ onSave }) {
  const { user } = useAuth();
  const [selected, setSelected] = useState("beginner");

  const handleSave = async () => {
    try {
      await updateProfile({ level: selected });
    } catch (e) {
      console.error("Failed to save level:", e);
    }
    onSave(selected);
  };

  return (
    <div className="level-modal-overlay">
      <div className="level-modal" onClick={(e) => e.stopPropagation()}>
        <div className="level-modal-header">
          <div className="level-modal-logo">
            <Logo size={32} />
          </div>
          <h2 className="level-modal-title">Personalize Your Experience</h2>
          <p className="level-modal-subtitle">
            Select your expertise level to tailor DharmaAI's reasoning depth and vocabulary.
          </p>
        </div>
        
        <div className="level-options-grid">
          {LEVELS.map((lvl) => {
            const isSelected = selected === lvl.value;
            return (
              <button
                key={lvl.value}
                type="button"
                className={`level-option-card ${isSelected ? "active" : ""}`}
                onClick={() => setSelected(lvl.value)}
              >
                <div className={`level-card-icon-wrap ${isSelected ? "active" : ""}`}>
                  {lvl.icon}
                </div>
                <div className="level-card-info">
                  <div className="level-card-title">{lvl.label}</div>
                  <div className="level-card-desc">{lvl.desc}</div>
                </div>
                <div className={`level-card-radio ${isSelected ? "active" : ""}`}>
                  {isSelected && <Check size={12} color="#fff" />}
                </div>
              </button>
            );
          })}
        </div>

        <button className="level-save-btn" onClick={handleSave}>
          Confirm & Continue
        </button>
      </div>
    </div>
  );
}
