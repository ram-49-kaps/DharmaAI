import React, { useState, useEffect } from "react";
import { Scale, ScrollText, BrainCircuit, BookOpen, GraduationCap, Search, FileSignature, Layers, ShieldCheck, Database, LayoutTemplate, MessageSquare, Zap } from "lucide-react";

const SLIDES = [
  {
    badgeIcon: Scale,
    badgeText: "Trusted by Law Students & Practitioners",
    title: (
      <>
        Centuries of Legal Wisdom,<br />
        One Intelligent Platform.
      </>
    ),
    features: [
      {
        icon: ScrollText,
        color: "#B45309",
        title: "Case Law Analysis",
        desc: "Deep analysis with citations & precedents"
      },
      {
        icon: BrainCircuit,
        color: "#C2410C",
        title: "IRAC & FILAC Frameworks",
        desc: "Structured legal reasoning methods"
      },
      {
        icon: BookOpen,
        color: "#92400E",
        title: "Dharma & IKS",
        desc: "Ancient wisdom meets modern jurisprudence"
      },
      {
        icon: GraduationCap,
        color: "#D97706",
        title: "Level-Based Learning",
        desc: "Beginner to Practitioner level responses"
      }
    ]
  },
  {
    badgeIcon: Search,
    badgeText: "Step 1: Query Analysis",
    title: (
      <>
        Intelligent Contextual<br />
        Understanding.
      </>
    ),
    features: [
      {
        icon: MessageSquare,
        color: "#0369A1",
        title: "Natural Language Processing",
        desc: "Understanding complex legal queries"
      },
      {
        icon: Zap,
        color: "#0284C7",
        title: "Intent Recognition",
        desc: "Identifying needs: research, drafting, or advice"
      },
      {
        icon: Layers,
        color: "#075985",
        title: "Fact Extraction",
        desc: "Pinpointing key material facts for research"
      },
      {
        icon: ShieldCheck,
        color: "#0C4A6E",
        title: "Jurisdiction Mapping",
        desc: "Focusing on relevant Indian courts and laws"
      }
    ]
  },
  {
    badgeIcon: Database,
    badgeText: "Step 2: Comprehensive Research",
    title: (
      <>
        Deep Search Across<br />
        Indian Jurisprudence.
      </>
    ),
    features: [
      {
        icon: FileSignature,
        color: "#15803D",
        title: "Bare Acts & Statutes",
        desc: "Referencing the exact sections of Indian laws"
      },
      {
        icon: Scale,
        color: "#16A34A",
        title: "Landmark Judgments",
        desc: "Finding binding precedents from SC & High Courts"
      },
      {
        icon: BookOpen,
        color: "#166534",
        title: "Dharma & IKS",
        desc: "Integrating traditional Indian Knowledge Systems"
      },
      {
        icon: Layers,
        color: "#14532D",
        title: "Cross-Referencing",
        desc: "Validating laws against the latest amendments"
      }
    ]
  },
  {
    badgeIcon: LayoutTemplate,
    badgeText: "Step 3: Structured Delivery",
    title: (
      <>
        Professional Legal<br />
        Responses.
      </>
    ),
    features: [
      {
        icon: BrainCircuit,
        color: "#6D28D9",
        title: "IRAC Framework",
        desc: "Issue, Rule, Application, Conclusion format"
      },
      {
        icon: Layers,
        color: "#7C3AED",
        title: "FILAC Framework",
        desc: "Facts, Issues, Law, Application, Conclusion"
      },
      {
        icon: GraduationCap,
        color: "#5B21B6",
        title: "Adaptive Depth",
        desc: "Adjusting complexity to your expertise level"
      },
      {
        icon: ScrollText,
        color: "#4C1D95",
        title: "Inline Citations",
        desc: "Providing verifiable sources for all claims"
      }
    ]
  }
];

export default function AuthShowcase() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [fade, setFade] = useState(true);

  useEffect(() => {
    const interval = setInterval(() => {
      setFade(false); // start fade out
      setTimeout(() => {
        setCurrentSlide((prev) => (prev + 1) % SLIDES.length);
        setFade(true); // start fade in
      }, 400); // 400ms for transition out
    }, 5000); // 5 seconds per slide

    return () => clearInterval(interval);
  }, []);

  const slide = SLIDES[currentSlide];
  const BadgeIcon = slide.badgeIcon;

  return (
    <div className="auth-right">
      <div className={`auth-right-content ${fade ? "fade-in" : "fade-out"}`}>
        <div className="auth-showcase-badge">
          <BadgeIcon size={15} style={{ marginRight: 6, verticalAlign: 'middle' }} /> 
          {slide.badgeText}
        </div>
        <h2 className="auth-showcase-title">
          {slide.title}
        </h2>
        <div className="auth-showcase-features">
          {slide.features.map((feature, idx) => {
            const FeatureIcon = feature.icon;
            return (
              <div key={idx} className="auth-showcase-feature">
                <span className="auth-sf-icon">
                  <FeatureIcon size={22} color={feature.color} />
                </span>
                <div>
                  <strong>{feature.title}</strong>
                  <p>{feature.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Slide Indicators */}
      <div className="auth-showcase-indicators">
        {SLIDES.map((_, idx) => (
          <div 
            key={idx} 
            className={`auth-showcase-dot ${idx === currentSlide ? "active" : ""}`}
            onClick={() => {
              setFade(false);
              setTimeout(() => {
                setCurrentSlide(idx);
                setFade(true);
              }, 400);
            }}
          />
        ))}
      </div>
    </div>
  );
}
