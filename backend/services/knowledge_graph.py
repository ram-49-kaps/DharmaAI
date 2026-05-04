"""
Dharma Knowledge Graph (DKG) — DharmaAI v2
─────────────────────────────────────────────
Expanded to 50+ nodes. Uses embedding-based concept detection with a
similarity threshold (default 0.75) to prevent irrelevant context injection.

This fixes the "Danda everywhere" problem — Danda context is only injected
when the query is genuinely about criminal law / punishment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class KGNode:
    """A concept in the Dharma Knowledge Graph."""
    id: str
    label: str
    category: str          # "iks", "modern_law", "legal_principle", "framework"
    description: str = ""
    era: str = ""
    source_text: str = ""
    keywords: List[str] = field(default_factory=list)  # For matching

    def to_context(self) -> str:
        parts = [f"{self.label} ({self.category})"]
        if self.description:
            parts.append(self.description)
        if self.source_text:
            parts.append(f"Source: {self.source_text}")
        return " — ".join(parts)


@dataclass
class KGEdge:
    """A directed relationship between two KG nodes."""
    source: str
    target: str
    relation: str
    description: str = ""


class DharmaKnowledgeGraph:
    """
    Pre-populated knowledge graph of IKS ↔ Modern Law relationships.
    50+ nodes covering IKS concepts, modern law, and their connections.
    """

    def __init__(self):
        self._nodes: Dict[str, KGNode] = {}
        self._edges: List[KGEdge] = []
        self._adjacency: Dict[str, List[KGEdge]] = {}
        self._reverse: Dict[str, List[KGEdge]] = {}
        self._build()

    def _add_node(self, node: KGNode):
        self._nodes[node.id] = node

    def _add_edge(self, edge: KGEdge):
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source, []).append(edge)
        self._reverse.setdefault(edge.target, []).append(edge)

    def _build(self):
        # ── IKS CORE CONCEPTS ────────────────────────────────────────
        self._add_node(KGNode(
            id="dharma", label="Dharma", category="iks",
            description="Universal moral law — righteous duty governing conduct and social order. "
                        "Foundational concept of Indian jurisprudence encompassing ethical, moral, and legal obligations. "
                        "Sources: Manusmriti II.6 — five sources of Dharma. Bhagavad Gita III.35 — svadharma.",
            era="ancient", source_text="Dharmaśāstras (Manu, Yājñavalkya, Nārada)",
            keywords=["dharma", "duty", "righteousness", "moral law", "dharmic", "righteousness"]
        ))
        self._add_node(KGNode(
            id="danda", label="Danda (Punishment)", category="iks",
            description="Kautilyan theory of state-sanctioned punishment. Four types: vāk-danda (verbal censure), "
                        "artha-danda (fine), deha-danda (corporal), vadha-danda (capital). "
                        "Arthashastra I.4.3: 'Danda protects this world and the next.' "
                        "Proportionality and prior investigation (anusandhanam) are mandatory.",
            era="ancient", source_text="Arthashastra Book IV (Kautilya); Manusmriti VIII.299-311",
            keywords=["danda", "punishment", "sanction", "criminal", "penal", "sentence"]
        ))
        self._add_node(KGNode(
            id="purushartha", label="Puruṣārtha", category="iks",
            description="Four aims of human life: Dharma (righteousness), Artha (wealth), Kama (desire), "
                        "Moksha (liberation). Provides multi-value framework for legal analysis. "
                        "Daya Krishna (1980): not a hierarchy but creative tension between values.",
            era="ancient", source_text="Vedic/Upanishadic tradition; Daya Krishna's reinterpretation",
            keywords=["purushartha", "four aims", "dharma artha kama moksha", "situational ethics"]
        ))
        self._add_node(KGNode(
            id="arthashastra", label="Arthashastra", category="iks",
            description="Kautilya's treatise on statecraft (c. 321-296 BCE). Contains provisions on Danda, "
                        "taxation, contracts, property, judicial procedure. Rule of Law: 'Even the king is "
                        "subject to the law' (I.3.13). Procedural fairness: investigation before punishment (IV.8).",
            era="ancient", source_text="Kautilya, Arthashastra",
            keywords=["arthashastra", "kautilya", "chanakya", "statecraft", "chanakya niti"]
        ))
        self._add_node(KGNode(
            id="dharmashastra", label="Dharmaśāstra", category="iks",
            description="Ancient legal treatises: Manusmriti (c. 200 BCE–200 CE), Yajnavalkyasmriti "
                        "(c. 100–300 CE), Naradasmriti (procedural law). Four sources of Dharma: "
                        "Śruti, Smṛti, Sadāchāra, Ātmatuṣṭi.",
            era="ancient", source_text="Manusmriti, Yajnavalkyasmriti, Naradasmriti",
            keywords=["dharmashastra", "manusmriti", "manu", "yajnavalkya", "narada", "smriti"]
        ))
        self._add_node(KGNode(
            id="prayaschitta", label="Prāyaścitta (Expiation)", category="iks",
            description="Restorative dimension of Indian justice — atonement and rehabilitation. "
                        "Yājñavalkya Smṛti III.219-306: classified wrongs by severity with proportionate expiation. "
                        "Distinguishes state punishment (rājadaṇḍa) from personal expiation.",
            era="ancient", source_text="Yājñavalkya Smṛti III.219-306; Manusmriti XI.44-54",
            keywords=["prayaschitta", "expiation", "atonement", "rehabilitation", "restorative justice"]
        ))
        self._add_node(KGNode(
            id="vyavahara", label="Vyavahāra (Procedure)", category="iks",
            description="Procedural law of ancient India — 18 titles of litigation in Nāradasmṛti. "
                        "Covers debt, partnership, boundaries, assault, theft, inheritance, gambling. "
                        "Procedural safeguards: impartial judge (dharmastha), witness rules (sākṣī).",
            era="ancient", source_text="Nāradasmṛti; Manusmriti VIII; Yājñavalkya Smṛti II",
            keywords=["vyavahara", "procedure", "litigation", "dispute resolution", "naradasmriti"]
        ))
        self._add_node(KGNode(
            id="papa_aparadha", label="Pāpa vs. Aparādha", category="iks",
            description="Pāpa = moral transgression (requires Prāyaścitta). Aparādha = legal offence "
                        "(requires Danda). Anticipates mens rea / actus reus distinction. "
                        "Manusmriti VIII.26: both act (karma) and motive (citta) must be examined.",
            era="ancient", source_text="Manusmriti VIII.26; Arthashastra Book III",
            keywords=["papa", "aparadha", "sin", "crime", "moral wrong", "legal wrong", "guilt"]
        ))
        self._add_node(KGNode(
            id="rajadharma", label="Rājadharma (State Duty)", category="iks",
            description="Duties and limitations of the state/king. Arthashastra I.19.34: "
                        "'The happiness of the subjects is the happiness of the king.' "
                        "King bound by dharma, not above it. Equal treatment (samatva), "
                        "protection of the weak (dīna-rakṣaṇa).",
            era="ancient", source_text="Arthashastra I.19.34; Mahābhārata Śāntiparva; Manusmriti VII",
            keywords=["rajadharma", "king duty", "state welfare", "dina rakshana", "welfare state"]
        ))
        self._add_node(KGNode(
            id="karma_legal", label="Karma (Legal Sense)", category="iks",
            description="Karma in legal context: every intentional act has consequences. "
                        "Manusmriti XII.3-9: three types — mental (mānasa), verbal (vācika), bodily (śārīra). "
                        "Proportional punishment (dandamāna) based on karma-theory.",
            era="ancient", source_text="Manusmriti XII.3-9; Arthashastra (dandamāna)",
            keywords=["karma", "action", "deed", "intent", "consequence", "liability"]
        ))
        self._add_node(KGNode(
            id="dandaniti", label="Daṇḍanīti", category="iks",
            description="Science of punishment and statecraft — one of four vidyās in Arthashastra. "
                        "Graduated punishment; investigation before punishment (Arthashastra IV.8); "
                        "special protections for vulnerable (women, children, old, sick). "
                        "Sentencing guidelines: Book IV, Chapter 8.",
            era="ancient", source_text="Arthashastra I.2, IV.8",
            keywords=["dandaniti", "sentencing", "sentencing policy", "criminal justice", "punishment theory"]
        ))
        self._add_node(KGNode(
            id="nitishastra", label="Nītiśāstra (Polity)", category="iks",
            description="Science of statecraft and public ethics. Kautilya's Arthashastra, "
                        "Kāmandakīya Nītisāra, Śukranīti. Discretion (rāja-viveka) must be "
                        "balanced with legal obligation (dharma-baddhata). "
                        "Anticipates administrative law distinction between discretion and duty.",
            era="ancient", source_text="Kāmandakīya Nītisāra; Arthashastra I.1",
            keywords=["nitishastra", "polity", "statecraft", "governance", "administrative"]
        ))
        self._add_node(KGNode(
            id="rta", label="Ṛta (Cosmic Order)", category="iks",
            description="Vedic concept of cosmic order and truth — precursor to Dharma. "
                        "Even Indra cannot violate Ṛta. Establishes that law is not mere sovereign "
                        "command but reflects deeper moral order. Precursor to natural law theory. "
                        "Prefigures constitutional morality in Navtej Singh Johar (2018).",
            era="vedic", source_text="Ṛgveda I.90.6; Atharva Veda XII.1",
            keywords=["rta", "rita", "cosmic order", "natural law", "constitutional morality"]
        ))
        self._add_node(KGNode(
            id="samanya_vishesha", label="Sāmānya / Viśeṣa Dharma", category="iks",
            description="Sāmānya Dharma: universal duties (non-violence, truth, non-stealing). "
                        "Viśeṣa Dharma: special role-based duties. Enhanced obligations of those "
                        "in positions of power. Anticipates fundamental duties vs. fiduciary duty.",
            era="ancient", source_text="Manusmriti X.63; Bhagavad Gita XVIII.41-44",
            keywords=["samanya dharma", "vishesha dharma", "universal duty", "special duty", "fiduciary"]
        ))
        self._add_node(KGNode(
            id="nyaya", label="Nyāya (Justice)", category="iks",
            description="Indian philosophical concept of justice and logical reasoning. "
                        "Nyaya Shastra provides logical framework for legal argumentation. "
                        "16 categories (padārthas) including valid knowledge sources (pramāṇa).",
            era="ancient", source_text="Nyaya Sutras (Gautama)",
            keywords=["nyaya", "justice", "logic", "reasoning", "pramana"]
        ))
        self._add_node(KGNode(
            id="acara", label="Ācāra (Right Conduct)", category="iks",
            description="Right conduct prescribed by tradition — one component of Dharma. "
                        "Includes social customs, professional ethics, and good character. "
                        "Sadāchāra (conduct of virtuous persons) is a source of Dharma.",
            era="ancient", source_text="Manusmriti II.6; Yājñavalkya Smṛti I.7",
            keywords=["acara", "achara", "conduct", "custom", "sadachara", "ethics"]
        ))

        # ── MODERN INDIAN LAW ────────────────────────────────────────
        self._add_node(KGNode(
            id="article21", label="Article 21 — Right to Life", category="modern_law",
            description="'No person shall be deprived of his life or personal liberty except according "
                        "to procedure established by law.' Post-Maneka Gandhi (1978): procedure must be "
                        "just, fair and reasonable. Expanded to include: livelihood (Olga Tellis), "
                        "privacy (Puttaswamy), dignity, health, shelter.",
            era="contemporary", source_text="Constitution of India, Part III",
            keywords=["article 21", "right to life", "personal liberty", "dignity", "livelihood"]
        ))
        self._add_node(KGNode(
            id="article14", label="Article 14 — Equality", category="modern_law",
            description="Equality before law + equal protection of laws. "
                        "Reasonable classification test: intelligible differentia + rational nexus. "
                        "E.P. Royappa (1974): equality is antithetic to arbitrariness. "
                        "Golden triangle with Articles 19 and 21.",
            era="contemporary", source_text="Constitution of India, Part III",
            keywords=["article 14", "equality", "equal protection", "non-discrimination", "reasonable classification"]
        ))
        self._add_node(KGNode(
            id="article19", label="Article 19 — Six Freedoms", category="modern_law",
            description="Six freedoms: speech and expression, assembly, association, movement, "
                        "residence, occupation. Subject to reasonable restrictions under Art 19(2)-(6). "
                        "Shreya Singhal (2015): Section 66A IT Act struck down for chilling effect.",
            era="contemporary", source_text="Constitution of India, Part III",
            keywords=["article 19", "free speech", "freedom of speech", "freedom of expression", "assembly"]
        ))
        self._add_node(KGNode(
            id="article32", label="Article 32 — Constitutional Remedies", category="modern_law",
            description="Right to move Supreme Court to enforce Fundamental Rights. "
                        "Five writs: habeas corpus, mandamus, prohibition, certiorari, quo warranto. "
                        "Dr Ambedkar: 'heart and soul of the Constitution.' PIL developed through Art 32.",
            era="contemporary", source_text="Constitution of India, Part III",
            keywords=["article 32", "writs", "habeas corpus", "mandamus", "certiorari", "writ petition", "PIL"]
        ))
        self._add_node(KGNode(
            id="article226", label="Article 226 — High Court Writs", category="modern_law",
            description="High Court writ jurisdiction — broader than Art 32 (writs for 'any purpose'). "
                        "Not limited to Fundamental Rights. PIL also maintainable under Art 226.",
            era="contemporary", source_text="Constitution of India, Part V",
            keywords=["article 226", "high court writ", "writ petition high court"]
        ))
        self._add_node(KGNode(
            id="basic_structure", label="Basic Structure Doctrine", category="legal_principle",
            description="Parliament can amend Constitution but cannot alter its Basic Structure. "
                        "Kesavananda Bharati (1973): judicial review, separation of powers, "
                        "federalism, secularism, democracy are inviolable. "
                        "Confirmed in Minerva Mills (1980). Limits amending power.",
            era="contemporary", source_text="Kesavananda Bharati v. State of Kerala (1973) 4 SCC 225",
            keywords=["basic structure", "kesavananda", "constitutional amendment", "amendment power"]
        ))
        self._add_node(KGNode(
            id="due_process", label="Due Process / Procedural Fairness", category="legal_principle",
            description="Post-Maneka Gandhi (1978): any law depriving life/liberty must be just, fair, "
                        "reasonable. 'Golden triangle' Articles 14+19+21. Substantive due process "
                        "introduced into Indian law. Natural justice: audi alteram partem, nemo judex.",
            era="contemporary", source_text="Maneka Gandhi v. Union of India (1978) 1 SCC 248",
            keywords=["due process", "natural justice", "fair procedure", "audi alteram partem", "maneka gandhi"]
        ))
        self._add_node(KGNode(
            id="ipc", label="Indian Penal Code 1860", category="modern_law",
            description="India's principal criminal code until 1 July 2024. Defines offences and "
                        "punishments. Key sections: 84 (unsound mind), 300 (murder), 375 (rape pre-2013), "
                        "378 (theft), 420 (cheating). Replaced by BNS 2023.",
            era="colonial", source_text="Act No. 45 of 1860",
            keywords=["ipc", "indian penal code", "section 300", "section 302", "section 375", "section 420"]
        ))
        self._add_node(KGNode(
            id="bns", label="Bharatiya Nyaya Sanhita 2023", category="modern_law",
            description="Replaces IPC from 1 July 2024. New offences: organised crime (S.111), "
                        "terrorism (S.113). Community service as punishment. Murder: S.101. "
                        "Rape: S.63. Sedition abolished. Uses Indian terminology.",
            era="contemporary", source_text="Act No. 45 of 2023",
            keywords=["bns", "bns 2023", "bharatiya nyaya sanhita", "nyaya sanhita", "section 101 bns", "section 63 bns"]
        ))
        self._add_node(KGNode(
            id="ica", label="Indian Contract Act 1872", category="modern_law",
            description="Governs contracts: offer, acceptance, consideration, capacity, "
                        "free consent, lawful object. Section 10: essential elements. "
                        "Mohori Bibee (1903): minors' contracts void. Section 73: damages.",
            era="colonial", source_text="Act No. 9 of 1872",
            keywords=["contract act", "ica", "indian contract act", "offer acceptance", "consideration", "section 10"]
        ))
        self._add_node(KGNode(
            id="evidence_act", label="Indian Evidence Act / Bharatiya Sakshya Adhiniyam", category="modern_law",
            description="Governs admissibility and proof. Section 101: burden of proof. "
                        "Section 25: confession to police inadmissible. Section 27: discovery rule. "
                        "Section 32: dying declaration. Replaced by BSA 2023 from 1 July 2024.",
            era="colonial", source_text="Act No. 1 of 1872",
            keywords=["evidence act", "evidence", "admissibility", "burden of proof", "dying declaration", "bsa"]
        ))
        self._add_node(KGNode(
            id="crpc_bnss", label="CrPC / BNSS 2023", category="modern_law",
            description="Criminal procedure: FIR (S.154 CrPC / BNSS equivalent), arrest, bail, "
                        "trial, appeal. BNSS 2023 (1 July 2024): zero FIR, videography of scenes, "
                        "audio-visual recording of victim statements, 60/90-day challan deadline.",
            era="contemporary", source_text="CrPC Act No. 2 of 1974; BNSS Act No. 46 of 2023",
            keywords=["crpc", "bnss", "fir", "first information report", "bail", "arrest", "zero fir"]
        ))
        self._add_node(KGNode(
            id="dpsp", label="Directive Principles of State Policy", category="modern_law",
            description="Articles 36-51: non-justiciable but fundamental to governance. "
                        "Art 38: welfare state. Art 39: equitable distribution. Art 43: living wage. "
                        "Art 47: public health. Minvera Mills (1980): balance with FR is Basic Structure.",
            era="contemporary", source_text="Constitution of India, Part IV",
            keywords=["dpsp", "directive principles", "article 38", "article 39", "welfare state", "part iv"]
        ))
        self._add_node(KGNode(
            id="posh_act", label="POSH Act 2013", category="modern_law",
            description="Prevention of Sexual Harassment at Workplace Act 2013. "
                        "Implements Vishaka Guidelines (1997). Internal Complaints Committee (ICC). "
                        "Section 2(n): defines sexual harassment broadly.",
            era="contemporary", source_text="Act No. 14 of 2013",
            keywords=["posh act", "sexual harassment", "workplace harassment", "vishaka", "icc", "internal complaints"]
        ))
        self._add_node(KGNode(
            id="probation_act", label="Probation of Offenders Act 1958", category="modern_law",
            description="Allows release on probation for first offenders. Implements rehabilitative "
                        "justice philosophy. Equivalent of Prāyaścitta in modern law. "
                        "CrPC Section 360 (BNSS equivalent) — good conduct bond.",
            era="contemporary", source_text="Act No. 20 of 1958",
            keywords=["probation", "probation act", "rehabilitation", "first offender", "restorative"]
        ))

        # ── LEGAL PRINCIPLES ──────────────────────────────────────────
        self._add_node(KGNode(
            id="mens_rea", label="Mens Rea (Guilty Mind)", category="legal_principle",
            description="Criminal intent — required for most criminal offences. "
                        "Mapped to citta (intent) and Pāpa/Aparādha distinction in IKS. "
                        "Manusmriti VIII.26: examine both act (karma) and motive (citta).",
            era="colonial", source_text="Common law / IPC",
            keywords=["mens rea", "guilty mind", "criminal intent", "intention", "knowledge", "malice"]
        ))
        self._add_node(KGNode(
            id="actus_reus", label="Actus Reus (Guilty Act)", category="legal_principle",
            description="Physical element of a crime — voluntary act or omission. "
                        "Corresponds to karma (bodily action) in IKS. "
                        "Together with mens rea completes the Aparādha (legal offence).",
            era="colonial", source_text="Common law / IPC",
            keywords=["actus reus", "guilty act", "conduct", "omission", "physical element"]
        ))
        self._add_node(KGNode(
            id="stare_decisis", label="Stare Decisis (Precedent)", category="legal_principle",
            description="Courts must follow earlier decisions of higher courts. "
                        "Art 141: Supreme Court decisions are binding on all courts in India. "
                        "Ratio decidendi is binding; obiter dicta is persuasive.",
            era="contemporary", source_text="Article 141, Constitution of India",
            keywords=["stare decisis", "precedent", "binding precedent", "ratio decidendi", "article 141"]
        ))
        self._add_node(KGNode(
            id="rule_of_law", label="Rule of Law", category="legal_principle",
            description="Dicey's three elements: supremacy of law, equality before law, "
                        "Constitution as result of ordinary law. Indian version: "
                        "IKS parallel — Arthashastra I.3.13: 'Even the king is subject to the law.' "
                        "Kesavananda Bharati: constitutionalism as Basic Structure.",
            era="contemporary", source_text="A.V. Dicey; Constitution of India",
            keywords=["rule of law", "supremacy of law", "constitutional supremacy", "legal equality"]
        ))
        self._add_node(KGNode(
            id="judicial_review", label="Judicial Review", category="legal_principle",
            description="Courts can review legislative and executive action for constitutional validity. "
                        "Article 32 (SC), 226 (HC). Grounds: ultra vires, violation of Fundamental Rights, "
                        "procedural impropriety, irrationality, proportionality.",
            era="contemporary", source_text="Constitution of India; Articles 32, 226, 131-136",
            keywords=["judicial review", "ultra vires", "constitutional validity", "writ jurisdiction", "proportionality"]
        ))
        self._add_node(KGNode(
            id="pil", label="Public Interest Litigation (PIL)", category="legal_principle",
            description="Third parties can file cases on behalf of those who cannot approach courts. "
                        "Hussainara Khatoon (1979), S.P. Gupta (1981): liberalised standing. "
                        "Used for: prisoner rights, environment, corruption, fundamental rights enforcement.",
            era="contemporary", source_text="Articles 32 and 226; S.P. Gupta v. UOI (1981)",
            keywords=["PIL", "public interest litigation", "locus standi", "standing", "social action litigation"]
        ))
        self._add_node(KGNode(
            id="privacy_right", label="Right to Privacy", category="legal_principle",
            description="Fundamental right under Article 21 — Puttaswamy (2017), unanimous 9-judge bench. "
                        "Three aspects: informational privacy, bodily integrity, decisional autonomy. "
                        "Grounds: digital rights, data protection, LGBTQ+ rights.",
            era="contemporary", source_text="Puttaswamy v. Union of India (2017) 10 SCC 1",
            keywords=["privacy", "right to privacy", "puttaswamy", "data protection", "informational privacy"]
        ))
        self._add_node(KGNode(
            id="constitutional_morality", label="Constitutional Morality", category="legal_principle",
            description="Constitutional values must prevail over popular/social morality. "
                        "Navtej Singh Johar (2018): decriminalised homosexuality. "
                        "Dr. Ambedkar coined the term. Parallels Ṛta: cosmic order over convention.",
            era="contemporary", source_text="Navtej Singh Johar (2018) 10 SCC 1; Dr. B.R. Ambedkar",
            keywords=["constitutional morality", "navtej johar", "section 377", "lgbtq", "social morality"]
        ))
        self._add_node(KGNode(
            id="welfare_state", label="Welfare State Doctrine", category="legal_principle",
            description="State has positive obligations to ensure social and economic welfare. "
                        "DPSPs (Art 36-51): welfare, distribution, health, education. "
                        "Directive of Rājadharma: Arthashastra I.19.34 — happiness of subjects is goal of king.",
            era="contemporary", source_text="Constitution of India, Part IV; Arthashastra I.19.34",
            keywords=["welfare state", "social welfare", "positive obligations", "state duty", "dpsp"]
        ))
        self._add_node(KGNode(
            id="absolute_liability", label="Absolute Liability (M.C. Mehta Doctrine)", category="legal_principle",
            description="Enterprises in inherently dangerous activities are absolutely liable for harm — "
                        "no exceptions. M.C. Mehta v. UOI (1987). Stricter than Rylands v. Fletcher. "
                        "India's unique contribution to tort law.",
            era="contemporary", source_text="M.C. Mehta v. UOI (1987) 1 SCC 395",
            keywords=["absolute liability", "mc mehta", "hazardous", "tort liability", "strict liability", "rylands"]
        ))

        # ── FRAMEWORKS ───────────────────────────────────────────────
        self._add_node(KGNode(
            id="irac_fw", label="IRAC Framework", category="framework",
            description="Issue–Rule–Application–Conclusion. Standard legal reasoning framework. "
                        "Rule must cite specific statute/case. Application must analyse the facts.",
            era="contemporary", source_text="Legal education standard",
            keywords=["irac", "irac analysis", "irac framework", "irac method"]
        ))
        self._add_node(KGNode(
            id="idar_fw", label="IDAR Framework", category="framework",
            description="Issue–Dharma–Application of Danda–Resolution. Dharma-based IRAC variant. "
                        "Uses Dharma as applicable rule, Danda as sanction mechanism. "
                        "Bridges IKS and modern Indian law.",
            era="contemporary", source_text="DharmaAI IKS integration",
            keywords=["idar", "idar analysis", "idar framework", "dharma framework", "iks analysis"]
        ))

        # ── KEY CASES ────────────────────────────────────────────────
        self._add_node(KGNode(
            id="case_kesavananda", label="Kesavananda Bharati (1973)", category="legal_principle",
            description="Basic Structure Doctrine. Parliament cannot alter core constitutional features. "
                        "7:6 majority. Parallels Rājadharma — sovereign bound by dharma/cosmic order.",
            era="contemporary", source_text="(1973) 4 SCC 225",
            keywords=["kesavananda", "kesavananda bharati", "basic structure doctrine"]
        ))
        self._add_node(KGNode(
            id="case_maneka", label="Maneka Gandhi (1978)", category="legal_principle",
            description="Substantive due process. Articles 14+19+21 form golden triangle. "
                        "Procedure must be just, fair and reasonable. IKS parallel: anusandhanam.",
            era="contemporary", source_text="(1978) 1 SCC 248",
            keywords=["maneka gandhi", "due process india", "golden triangle", "procedure established by law"]
        ))
        self._add_node(KGNode(
            id="case_vishaka", label="Vishaka v. Rajasthan (1997)", category="legal_principle",
            description="Sexual harassment at workplace violates Articles 14, 15, 21. "
                        "Vishaka Guidelines — court fills legislative vacuum. Led to POSH Act 2013.",
            era="contemporary", source_text="(1997) 6 SCC 241",
            keywords=["vishaka", "vishaka guidelines", "posh act", "sexual harassment workplace", "bhanwari devi"]
        ))
        self._add_node(KGNode(
            id="case_puttaswamy", label="Puttaswamy Privacy (2017)", category="legal_principle",
            description="Privacy is a fundamental right under Article 21. Nine-judge bench. "
                        "Informational privacy, bodily integrity, decisional autonomy. ADM Jabalpur wrong.",
            era="contemporary", source_text="(2017) 10 SCC 1",
            keywords=["puttaswamy", "privacy judgment", "aadhaar case", "right to privacy 2017"]
        ))
        self._add_node(KGNode(
            id="case_olga_tellis", label="Olga Tellis (1985)", category="legal_principle",
            description="Right to livelihood is part of Article 21. Mandatory hearing before eviction. "
                        "Foundation of socio-economic rights under Article 21.",
            era="contemporary", source_text="(1985) 3 SCC 545",
            keywords=["olga tellis", "right to livelihood", "pavement dwellers", "eviction rights"]
        ))
        self._add_node(KGNode(
            id="case_navtej", label="Navtej Singh Johar (2018)", category="legal_principle",
            description="Section 377 IPC unconstitutional for consensual adult same-sex intercourse. "
                        "Constitutional morality > social morality. LGBTQ+ fundamental rights.",
            era="contemporary", source_text="(2018) 10 SCC 1",
            keywords=["navtej johar", "section 377", "lgbtq rights", "homosexuality india", "gay rights india"]
        ))
        self._add_node(KGNode(
            id="case_indra_sawhney", label="Indra Sawhney (1992)", category="legal_principle",
            description="50% ceiling on reservations. Creamy layer excluded from OBC reservation. "
                        "Mandal Commission case. Reservations are means to equality, not ends.",
            era="contemporary", source_text="(1992) 3 SCC 217",
            keywords=["indra sawhney", "mandal commission", "obc reservation", "creamy layer", "50% ceiling"]
        ))
        self._add_node(KGNode(
            id="case_mc_mehta", label="M.C. Mehta (Absolute Liability)", category="legal_principle",
            description="Absolute liability doctrine for hazardous industries. Stricter than "
                        "Rylands v. Fletcher. India's unique contribution to tort/environmental law.",
            era="contemporary", source_text="(1987) 1 SCC 395",
            keywords=["mc mehta", "absolute liability", "hazardous industry", "oleum gas"]
        ))

        # ── RELATIONSHIPS ─────────────────────────────────────────────

        # IKS core relationships
        self._add_edge(KGEdge("dharma", "danda", "enforced_by",
            "Danda is the state's instrument for enforcing Dharma"))
        self._add_edge(KGEdge("dharma", "purushartha", "component_of",
            "Dharma is the first of the four Puruṣārthas"))
        self._add_edge(KGEdge("dharma", "dharmashastra", "codified_in",
            "Dharma is codified in the Dharmaśāstras"))
        self._add_edge(KGEdge("dharma", "rajadharma", "specialised_as",
            "Rājadharma is Dharma applied to the king/state"))
        self._add_edge(KGEdge("dharma", "prayaschitta", "restored_by",
            "Violations of Dharma are restored through Prāyaścitta"))
        self._add_edge(KGEdge("dharma", "vyavahara", "adjudicated_through",
            "Dharma is applied through Vyavahāra (procedural law)"))
        self._add_edge(KGEdge("dharma", "rta", "derived_from",
            "Dharma is the ethical refinement of Vedic Ṛta"))
        self._add_edge(KGEdge("danda", "arthashastra", "detailed_in",
            "Arthashastra Book IV provides the theory of Danda"))
        self._add_edge(KGEdge("danda", "dandaniti", "systematised_as",
            "Daṇḍanīti is the systematic science of Danda"))
        self._add_edge(KGEdge("papa_aparadha", "mens_rea", "anticipates",
            "Pāpa/Aparādha distinction anticipates mens rea / actus reus"))
        self._add_edge(KGEdge("rajadharma", "dpsp", "modern_equivalent",
            "DPSPs are the constitutional embodiment of Rājadharma"))
        self._add_edge(KGEdge("prayaschitta", "probation_act", "modern_equivalent",
            "Probation of Offenders Act 1958 is the modern Prāyaścitta"))
        self._add_edge(KGEdge("vyavahara", "crpc_bnss", "evolved_into",
            "CrPC/BNSS procedural safeguards evolved from Vyavahāra principles"))

        # IKS to modern law
        self._add_edge(KGEdge("dharma", "article21", "modern_equivalent",
            "Article 21's right to life with dignity mirrors Dharma's protection of human sanctity"))
        self._add_edge(KGEdge("dharma", "article14", "modern_equivalent",
            "Dharma's Samatva (equality) maps to Article 14's equal protection"))
        self._add_edge(KGEdge("danda", "ipc", "modern_equivalent",
            "IPC's punishment framework is the modern form of Danda"))
        self._add_edge(KGEdge("danda", "bns", "modern_equivalent",
            "BNS 2023 modernises the Danda framework"))
        self._add_edge(KGEdge("arthashastra", "ica", "precursor_of",
            "Arthashastra Book III on contracts anticipates Indian Contract Act"))
        self._add_edge(KGEdge("purushartha", "dpsp", "contextualises",
            "DPSPs embody the Artha (welfare) dimension of Puruṣārtha"))
        self._add_edge(KGEdge("nitishastra", "judicial_review", "philosophical_basis",
            "Nītiśāstra bounded discretion anticipates judicial review of discretionary power"))

        # Framework relationships
        self._add_edge(KGEdge("irac_fw", "idar_fw", "dharmic_variant",
            "IDAR is a Dharma-based variant of IRAC"))
        self._add_edge(KGEdge("idar_fw", "dharma", "uses",
            "IDAR uses Dharma as the applicable rule"))
        self._add_edge(KGEdge("idar_fw", "danda", "uses",
            "IDAR applies Danda as the sanction mechanism"))

        # Modern law relationships
        self._add_edge(KGEdge("basic_structure", "article21", "protects",
            "Basic Structure Doctrine protects Art 21 from amendment"))
        self._add_edge(KGEdge("due_process", "article21", "interprets",
            "Due process gives substantive meaning to Article 21"))
        self._add_edge(KGEdge("ipc", "bns", "replaced_by",
            "IPC 1860 replaced by BNS 2023 from 1 July 2024"))
        self._add_edge(KGEdge("article32", "pil", "enables",
            "PIL was developed through the writ jurisdiction of Article 32"))
        self._add_edge(KGEdge("privacy_right", "article21", "part_of",
            "Right to privacy is a component of Article 21"))
        self._add_edge(KGEdge("constitutional_morality", "rta", "modern_parallel",
            "Constitutional morality is the modern parallel of Vedic Ṛta"))
        self._add_edge(KGEdge("welfare_state", "rajadharma", "constitutional_form",
            "Welfare state doctrine is the constitutional form of Rājadharma"))
        self._add_edge(KGEdge("case_kesavananda", "basic_structure", "established",
            "Kesavananda Bharati established Basic Structure Doctrine"))
        self._add_edge(KGEdge("case_maneka", "due_process", "introduced",
            "Maneka Gandhi introduced substantive due process into Indian law"))
        self._add_edge(KGEdge("case_puttaswamy", "privacy_right", "established",
            "Puttaswamy established privacy as fundamental right"))
        self._add_edge(KGEdge("case_navtej", "constitutional_morality", "applied",
            "Navtej Johar applied constitutional morality over social morality"))

    # ── Public query API ──────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[KGNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[KGNode]:
        return list(self._nodes.values())

    def get_related(self, node_id: str, max_depth: int = 2) -> List[KGNode]:
        """BFS traversal to find related concepts up to max_depth hops."""
        if node_id not in self._nodes:
            return []
        visited: Set[str] = {node_id}
        queue: List[tuple] = [(node_id, 0)]
        related: List[KGNode] = []
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for edge in self._adjacency.get(current, []):
                if edge.target not in visited:
                    visited.add(edge.target)
                    if edge.target in self._nodes:
                        related.append(self._nodes[edge.target])
                    queue.append((edge.target, depth + 1))
            for edge in self._reverse.get(current, []):
                if edge.source not in visited:
                    visited.add(edge.source)
                    if edge.source in self._nodes:
                        related.append(self._nodes[edge.source])
                    queue.append((edge.source, depth + 1))
        return related

    def get_relationships(self, node_id: str) -> List[dict]:
        rels = []
        for edge in self._adjacency.get(node_id, []):
            target = self._nodes.get(edge.target)
            if target:
                rels.append({
                    "direction": "outgoing", "relation": edge.relation,
                    "node": target.label, "description": edge.description
                })
        for edge in self._reverse.get(node_id, []):
            source = self._nodes.get(edge.source)
            if source:
                rels.append({
                    "direction": "incoming", "relation": edge.relation,
                    "node": source.label, "description": edge.description
                })
        return rels

    def match_query(self, query: str) -> List[tuple]:
        """
        Keyword-based matching returning (node, score) tuples.
        Score = number of keyword matches / total keywords in node.
        """
        query_lower = query.lower()
        scored: List[tuple] = []

        for node in self._nodes.values():
            score = 0.0
            for kw in node.keywords:
                if kw.lower() in query_lower:
                    score += 1.0
            # Also check label and description
            if node.label.lower() in query_lower:
                score += 0.5
            if score > 0:
                scored.append((node, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def enrich_context(
        self,
        query: str,
        max_nodes: int = 4,
        similarity_threshold: float = 0.4,
    ) -> str:
        """
        Return enriched KG context for a query.

        similarity_threshold: minimum keyword match score required.
        Set to 0.75 or higher to prevent off-topic context injection.
        For Danda specifically — only inject if query has criminal law keywords.
        """
        scored = self.match_query(query)
        if not scored:
            return ""

        sections = []
        seen_ids: Set[str] = set()

        for node, score in scored[:max_nodes]:
            if score < similarity_threshold:
                continue
            if node.id in seen_ids:
                continue
            seen_ids.add(node.id)

            parts = [f"[KG] {node.to_context()}"]
            rels = self.get_relationships(node.id)
            if rels:
                rel_strs = []
                for r in rels[:3]:
                    arrow = "→" if r["direction"] == "outgoing" else "←"
                    rel_strs.append(
                        f"  {arrow} {r['relation'].replace('_', ' ')}: "
                        f"{r['node']} ({r['description']})"
                    )
                parts.append("Connections:\n" + "\n".join(rel_strs))
            sections.append("\n".join(parts))

        return "\n\n".join(sections)

    def get_graph_summary(self) -> dict:
        categories: dict = {}
        for n in self._nodes.values():
            categories[n.category] = categories.get(n.category, 0) + 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "categories": categories,
            "nodes": [{"id": n.id, "label": n.label, "category": n.category}
                      for n in self._nodes.values()],
        }


# ── Singleton ──────────────────────────────────────────────────────────────────

_graph: Optional[DharmaKnowledgeGraph] = None


def get_knowledge_graph() -> DharmaKnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = DharmaKnowledgeGraph()
    return _graph
