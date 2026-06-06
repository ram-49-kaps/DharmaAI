import React, { useEffect, useRef, useState, useCallback } from "react";
import { Scale, ScrollText, BookOpen, BrainCircuit, Flower2, FileText, ArrowRight, ChevronRight, Sparkles, Shield, Users, Zap, Play } from "lucide-react";
import Logo from "./Logo";

export default function HomePage({ onGetStarted, onLogin }) {
  const [scrolled, setScrolled] = useState(false);
  const [booksGathered, setBooksGathered] = useState(false);
  const [editorialVisible, setEditorialVisible] = useState(false);
  const booksRef = useRef(null);
  const editorialRef = useRef(null);

  // Scroll-triggered animations
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll);

    // Intersection Observer for scroll reveal
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    document.querySelectorAll(".scroll-reveal, .scroll-reveal-left, .scroll-reveal-right, .stagger-children").forEach((el) => {
      revealObserver.observe(el);
    });

    // Books gathering observer
    const booksObserver = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setBooksGathered(true);
        }
      },
      { threshold: 0.3 }
    );

    if (booksRef.current) booksObserver.observe(booksRef.current);

    // Editorial section observer
    const editorialObserver = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setEditorialVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (editorialRef.current) editorialObserver.observe(editorialRef.current);

    return () => {
      window.removeEventListener("scroll", handleScroll);
      revealObserver.disconnect();
      booksObserver.disconnect();
      editorialObserver.disconnect();
    };
  }, []);

  return (
    <div className="landing-page">
      {/* ── Navbar ──────────────────────────────────────────────── */}
      <nav className={`landing-nav ${scrolled ? "scrolled" : ""}`}>
        <div className="nav-brand">
          <div className="nav-brand-icon">
            <Logo size={24} />
          </div>
          <span className="nav-brand-text">DharmaAI</span>
        </div>

        <ul className="nav-links">
          <li><a href="#features">Features</a></li>
          <li><a href="#demo">Demo</a></li>
          <li><a href="#how-it-works">How It Works</a></li>
          <li><a href="#about">About</a></li>
        </ul>

        <div className="nav-actions">
          <button className="nav-btn-ghost" onClick={onLogin}>
            Log In
          </button>
          <button className="nav-btn-primary" onClick={onGetStarted}>
            Get Started <ArrowRight size={16} />
          </button>
        </div>
      </nav>

      {/* ── Hero Section ───────────────────────────────────────── */}
      <section className="hero-section">
        <div className="hero-grid" />
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            AI-Powered Legal Intelligence
          </div>
          <h1 className="hero-title">
            Your Intelligent{" "}
            <span className="highlight">Legal Research</span>{" "}
            Companion
          </h1>
          <p className="hero-subtitle">
            Grounded in the Indian Knowledge System and modern jurisprudence.
            DharmaAI combines ancient wisdom with cutting-edge AI to deliver
            comprehensive legal analysis, case law research, and structured
            reasoning frameworks.
          </p>
          <div className="hero-actions">
            <button className="hero-btn-primary" onClick={onGetStarted}>
              Start for Free <ArrowRight size={18} />
            </button>
            <button className="hero-btn-secondary" onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}>
              Learn More <ChevronRight size={18} />
            </button>
          </div>
          <div className="hero-stats">
            <div className="hero-stat">
              <div className="hero-stat-number">1,000+</div>
              <div className="hero-stat-label">Legal Concepts</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-number">500+</div>
              <div className="hero-stat-label">Case Laws</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-number">5</div>
              <div className="hero-stat-label">Reasoning Frameworks</div>
            </div>
            <div className="hero-stat">
              <div className="hero-stat-number">24/7</div>
              <div className="hero-stat-label">AI Availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features Section ───────────────────────────────────── */}
      <section className="features-section" id="features">
        <div className="scroll-reveal" style={{ textAlign: "center", marginBottom: "1rem" }}>
          <div className="section-badge">
            <Sparkles size={16} /> Powerful Features
          </div>
          <h2 className="section-title" style={{ maxWidth: 600, margin: "0 auto" }}>
            Everything You Need for Legal Research
          </h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            From case law analysis to ancient Dharmic wisdom — DharmaAI provides
            a comprehensive toolkit for legal scholars, students, and practitioners.
          </p>
        </div>

        <div className="features-grid stagger-children">
          <div className="feature-card-landing">
            <div className="feature-card-icon rust">
              <ScrollText size={26} />
            </div>
            <div className="feature-card-title">Case Law Analysis</div>
            <div className="feature-card-desc">
              Deep analysis of Indian case law with relevant citations, precedents,
              and judicial interpretations from landmark judgments.
            </div>
          </div>

          <div className="feature-card-landing">
            <div className="feature-card-icon blue">
              <Scale size={26} />
            </div>
            <div className="feature-card-title">Statute Lookup</div>
            <div className="feature-card-desc">
              Instant access to Indian statutes, acts, and legislative provisions
              with contextual explanations and amendments.
            </div>
          </div>

          <div className="feature-card-landing">
            <div className="feature-card-icon green">
              <BrainCircuit size={26} />
            </div>
            <div className="feature-card-title">IRAC & FILAC Reasoning</div>
            <div className="feature-card-desc">
              Apply structured legal reasoning frameworks — IRAC, FILAC, CRAC,
              CREAC — to analyze any legal scenario methodically.
            </div>
          </div>

          <div className="feature-card-landing">
            <div className="feature-card-icon amber">
              <Flower2 size={26} />
            </div>
            <div className="feature-card-title">Dharma & IKS Integration</div>
            <div className="feature-card-desc">
              Unique integration of the Indian Knowledge System — bridging
              Arthashastra, Manusmriti, and ancient jurisprudence with modern law.
            </div>
          </div>

          <div className="feature-card-landing">
            <div className="feature-card-icon rose">
              <FileText size={26} />
            </div>
            <div className="feature-card-title">Legal Document Drafting</div>
            <div className="feature-card-desc">
              AI-assisted drafting of legal documents, contracts, petitions, and
              memoranda following standard legal formatting.
            </div>
          </div>

          <div className="feature-card-landing">
            <div className="feature-card-icon terracotta">
              <Users size={26} />
            </div>
            <div className="feature-card-title">Level-Based Learning</div>
            <div className="feature-card-desc">
              Responses tailored to your expertise — from beginner law students
              to advanced practitioners, ensuring the right depth of analysis.
            </div>
          </div>
        </div>
      </section>

      {/* ── Chatbot Demo / Video Section ───────────────────────── */}
      <section className="demo-section" id="demo">
        <div className="demo-inner">
          <div className="scroll-reveal">
            <div className="section-badge">
              <Play size={16} /> See It In Action
            </div>
            <h2 className="section-title" style={{ maxWidth: 600, margin: "0 auto" }}>
              Watch DharmaAI Analyze a Legal Query
            </h2>
            <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
              Ask any legal question and watch DharmaAI retrieve from case law,
              statutes, and IKS texts to build a comprehensive, well-cited answer.
            </p>
          </div>

          <div className="demo-video-wrapper scroll-reveal">
            <div className="demo-chat-mock">
              {/* Mock sidebar */}
              <div className="demo-sidebar-mock">
                <div className="demo-sidebar-logo">
                  <div className="demo-sidebar-logo-icon" />
                  <span className="demo-sidebar-logo-text">DharmaAI</span>
                </div>
                <div className="demo-sidebar-btn">+ New Chat</div>
                <div className="demo-sidebar-item">💬 Right to Privacy...</div>
                <div className="demo-sidebar-item">⚖️ Article 21 Analysis</div>
                <div className="demo-sidebar-item">📜 IPC Section 302...</div>
              </div>

              {/* Mock chat area */}
              <div className="demo-chat-area">
                {/* User message */}
                <div className="demo-msg" style={{ justifyContent: "flex-end" }}>
                  <div className="demo-msg-bubble user-msg">
                    Explain the landmark case of Kesavananda Bharati v. State of Kerala
                    and its significance in Indian constitutional law.
                  </div>
                  <div className="demo-msg-avatar user" />
                </div>

                {/* Typing indicator */}
                <div className="demo-typing">
                  <span className="demo-dot" />
                  <span className="demo-dot" />
                  <span className="demo-dot" />
                </div>

                {/* AI response */}
                <div className="demo-msg">
                  <div className="demo-msg-avatar ai" />
                  <div className="demo-msg-bubble ai-msg">
                    <strong>⚖️ Kesavananda Bharati v. State of Kerala (1973)</strong><br /><br />
                    This landmark case established the <strong>Basic Structure Doctrine</strong>,
                    holding that while Parliament can amend any part of the Constitution,
                    it cannot alter its fundamental framework...<br /><br />
                    <strong>📖 Dharmic Parallel:</strong> <em style={{ color: "#fbbf24" }}>
                    "Dharmo rakshati rakshitah"</em> — The law protects those who protect it.
                    This mirrors the doctrine that the Constitution's spirit must be preserved.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Books Gathering Animation ──────────────────────────── */}
      <section className="books-section" ref={booksRef}>
        <div className="books-inner">
          <div className="scroll-reveal">
            <div className="section-badge">
              <BookOpen size={16} /> Knowledge Base
            </div>
            <h2 className="section-title">
              Centuries of Legal Wisdom,<br />One Intelligent Platform
            </h2>
          </div>

          <div className={`books-container ${booksGathered ? "gathered" : ""}`}>
            <div className="floating-book">📕</div>
            <div className="floating-book">📗</div>
            <div className="floating-book">📘</div>
            <div className="floating-book">⚖️</div>
            <div className="floating-book">📜</div>
            <div className="floating-book">📙</div>
            <div className="floating-book">🏛️</div>
            <div className="floating-book">🕉️</div>
            <div className="books-glow" />
          </div>

          <p className="books-tagline">
            From Arthashastra to Article 21 — all in one place.
          </p>
        </div>
      </section>

      {/* ── Editorial Quote Section (Spots-inspired) ────────────── */}
      <section className="editorial-section" ref={editorialRef}>
        <div className="editorial-inner">
          <div className="editorial-label">Why DharmaAI</div>

          <p className={`editorial-text ${editorialVisible ? "visible" : ""}`}>
            Legal research is more accessible than ever. But depth is rarer.
          </p>

          <p className={`editorial-text ${editorialVisible ? "visible" : ""}`}>
            We bridge ancient jurisprudence and modern law, shaped by the
            Indian Knowledge System, the evolving legal landscape,
            and the quiet discipline of rigorous analysis.
          </p>

          <p className={`editorial-text ${editorialVisible ? "visible" : ""}`}>
            These are insights that endure. They stay with you because
            they reshape how you reason. Because they meet you
            at the right moment in your legal journey.
          </p>

          <p className={`editorial-signature ${editorialVisible ? "visible" : ""}`}>
            Welcome to <em>DharmaAI.</em>
          </p>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────────────── */}
      <section className="how-it-works-section" id="how-it-works">
        <div className="how-it-works-inner">
          <div className="scroll-reveal" style={{ textAlign: "center" }}>
            <div className="section-badge">
              <Zap size={16} /> Simple & Powerful
            </div>
            <h2 className="section-title" style={{ maxWidth: 500, margin: "0 auto" }}>
              How DharmaAI Works
            </h2>
            <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
              From question to comprehensive legal analysis in seconds.
            </p>
          </div>

          <div className="steps-grid stagger-children">
            <div className="step-card">
              <div className="step-number">1</div>
              <div className="step-title">Ask Your Question</div>
              <div className="step-desc">
                Type any legal question — from simple definitions to complex
                case analyses. Attach documents for deeper context.
              </div>
            </div>

            <div className="step-card">
              <div className="step-number">2</div>
              <div className="step-title">AI Analyzes & Retrieves</div>
              <div className="step-desc">
                DharmaAI searches through case law, statutes, IKS texts, and
                its knowledge graph to build a comprehensive answer.
              </div>
            </div>

            <div className="step-card">
              <div className="step-number">3</div>
              <div className="step-title">Get Detailed Response</div>
              <div className="step-desc">
                Receive a structured response with citations, Sanskrit shlokas
                where applicable, and actionable legal insights.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── About / Trust Section ──────────────────────────────── */}
      <section className="landing-section" id="about">
        <div className="scroll-reveal" style={{ textAlign: "center" }}>
          <div className="section-badge">
            <Shield size={16} /> Built for Legal Excellence
          </div>
          <h2 className="section-title" style={{ maxWidth: 600, margin: "0 auto" }}>
            Where Ancient Wisdom Meets Modern Law
          </h2>
          <p className="section-subtitle" style={{ margin: "0.75rem auto 0" }}>
            DharmaAI is the first legal AI platform that integrates the Indian
            Knowledge System (IKS) with contemporary Indian jurisprudence.
            Our RAG-powered engine retrieves from a curated knowledge base of
            case law, statutes, glossaries, and ancient texts to provide
            accurate, well-cited, and contextually rich legal analysis.
          </p>
        </div>
      </section>

      {/* ── CTA Section ────────────────────────────────────────── */}
      <section className="cta-section">
        <div className="cta-inner scroll-reveal">
          <h2 className="cta-title">
            Meet Your New Legal Research Teammate
          </h2>
          <p className="cta-subtitle">
            Join law students, academicians, and practitioners who are already
            using DharmaAI to accelerate their legal research and analysis.
          </p>
          <button className="hero-btn-primary" onClick={onGetStarted}>
            Get Started for Free <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <Logo size={18} color="rgba(255,255,255,0.4)" />
            <span>© {new Date().getFullYear()} DharmaAI. All rights reserved.</span>
          </div>
          <div className="footer-links">
            <a href="#features">Features</a>
            <a href="#demo">Demo</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#about">About</a>
          </div>
        </div>
        <p className="footer-disclaimer">
          ⚖️ Educational Use Only — Not Legal Advice · Powered by IKS & Modern Indian Jurisprudence
        </p>
      </footer>
    </div>
  );
}
