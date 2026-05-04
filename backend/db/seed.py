"""
Database and vector store seeding for DharmaAI v2.

Seeds:
1. SQLite tables (glossary, cases, statutes) — kept for search API
2. ChromaDB collections — from seed_corpus JSON files
"""

import hashlib
import json
import logging
import os

from db.database import get_connection

logger = logging.getLogger(__name__)

SEED_CORPUS_DIR = os.path.join(os.path.dirname(__file__), "../data/seed_corpus")

# ── SQLite seed data ──────────────────────────────────────────────────────────

GLOSSARY = [
    ("Dharma",
     "In Indian jurisprudence, Dharma is the universal moral law or righteous duty that governs individual "
     "conduct and social order. It encompasses ethical, moral, and legal obligations.",
     "A king's Dharma includes protecting the weak — this principle underlies modern State duty-of-care doctrines."),
    ("Danda",
     "Literally 'rod' or 'punishment', Danda is the Kautilyan theory of state-sanctioned sanction. It is the "
     "coercive power of the state used to enforce Dharma and maintain social order.",
     "Arthashastra Chapter 2 discusses Danda as the basis of criminal liability."),
    ("Purushartha",
     "The four aims of human life in Indian philosophy: Dharma (righteousness), Artha (material wealth), "
     "Kama (desire), and Moksha (liberation). Together they form a situational ethics framework.",
     "Courts have referenced Purushartha to interpret personal law disputes in a holistic manner."),
    ("Prāyaścitta",
     "Expiation or atonement in Indian jurisprudence — the restorative dimension of justice. Prāyaścitta "
     "addresses the moral wrong and the restoration of the wrongdoer to social and moral standing.",
     "Prāyaścitta maps onto modern restorative justice and probation — Probation of Offenders Act 1958."),
    ("IRAC",
     "Issue, Rule, Application, Conclusion — a structured legal reasoning framework used in case analysis "
     "and legal writing.",
     "IRAC: Issue – Was the contract binding? Rule – Section 10 ICA 1872. Application – Offer was accepted. "
     "Conclusion – Valid contract."),
    ("Precedent (Stare Decisis)",
     "The doctrine that courts must follow earlier decisions of higher courts on the same point of law, "
     "ensuring consistency and predictability.",
     "In Kesavananda Bharati v. State of Kerala (1973), the Supreme Court established the Basic Structure "
     "Doctrine, which is binding precedent."),
    ("Mens Rea",
     "Latin for 'guilty mind' — the criminal intent or knowledge of wrongdoing required for a crime. "
     "Most criminal offences require both Actus Reus and Mens Rea. Maps to citta (intent) in IKS.",
     "IPC Section 300 requires proof of intention or knowledge to establish murder."),
    ("Actus Reus",
     "Latin for 'guilty act' — the physical element of a crime, i.e., the voluntary act or omission that "
     "constitutes the crime. Corresponds to karma (bodily action) in IKS.",
     "The actus reus of theft under IPC Section 378 is dishonest taking of movable property."),
    ("Fundamental Rights",
     "Rights guaranteed by Part III of the Indian Constitution (Articles 12–35) that protect individuals "
     "against arbitrary state action. They are justiciable.",
     "Article 21 guarantees the Right to Life and Personal Liberty — interpreted expansively in Maneka Gandhi v. UOI (1978)."),
    ("Writ",
     "A formal written order issued by a court commanding a party to do or refrain from doing an act. "
     "Article 32 and 226 empower Supreme Court and High Courts to issue writs.",
     "A Habeas Corpus writ compels the state to produce a detained person before the court."),
    ("Dharmashastra",
     "Ancient Indian legal treatises that codified Dharma-based law. Key texts include Manusmriti, "
     "Yajnavalkyasmriti, and Naradasmriti.",
     "Dharmashastra texts influenced family law in pre-colonial India and continue to inform academic legal discourse."),
    ("Rājadharma",
     "The duties and obligations of the king/state in classical Indian thought. The state exists for the "
     "welfare of the people (prajā-sukhe sukham rājñaḥ). Maps onto Directive Principles of State Policy.",
     "Article 38 (welfare state obligation) is the constitutional embodiment of Rājadharma."),
    ("Vyavahāra",
     "Procedural law of ancient India — the 18 titles of litigation governing dispute resolution. The "
     "Nāradasmṛti is the most systematic procedural code, containing safeguards for fair trial.",
     "The 18 titles of Vyavahāra map onto subjects covered by CPC, ICA, and specific statutes."),
]

CASES = [
    ("Kesavananda Bharati v. State of Kerala",
     "(1973) 4 SCC 225",
     "The petitioner challenged the Kerala Land Reforms Amendment Act. The question was whether "
     "Parliament's power to amend the Constitution under Article 368 was unlimited.",
     "Can Parliament amend any part of the Constitution, including Fundamental Rights?",
     "The Supreme Court held (7:6) that Parliament can amend the Constitution but cannot alter its Basic Structure.",
     "Basic Structure Doctrine — judicial review, separation of powers, federalism, secularism are inviolable.",
     "Parliament cannot abrogate the Basic Structure of the Indian Constitution."),
    ("Maneka Gandhi v. Union of India",
     "(1978) 1 SCC 248",
     "The petitioner's passport was impounded by the government without providing reasons. She challenged "
     "this as violating Article 21.",
     "Does Article 21's 'procedure established by law' require the procedure to be fair, just, and reasonable?",
     "The Supreme Court held that procedure under Article 21 must be just, fair and reasonable, not merely "
     "procedurally valid. Articles 14, 19, 21 form a 'golden triangle.'",
     "Substantive due process introduced. Right to Life includes right to live with dignity.",
     "Passports cannot be impounded without a fair procedure satisfying Articles 14, 19 and 21."),
    ("Vishaka v. State of Rajasthan",
     "(1997) 6 SCC 241",
     "Following the gang rape of Bhanwari Devi, a social worker, women's groups filed a PIL seeking "
     "enforcement of the right to work in a safe environment.",
     "Do working women have a fundamental right to a safe workplace free from sexual harassment?",
     "The Supreme Court issued binding Vishaka Guidelines to prevent sexual harassment at workplaces, "
     "laying the foundation for the POSH Act 2013.",
     "Courts can fill legislative vacuum by issuing enforceable guidelines in absence of legislation.",
     "Sexual harassment at the workplace violates Articles 14, 15, and 21 of the Constitution."),
    ("Puttaswamy v. Union of India",
     "(2017) 10 SCC 1",
     "Justice Puttaswamy challenged the Aadhaar scheme, arguing there is a fundamental right to privacy. "
     "The government argued no such right existed based on older precedents.",
     "Is the right to privacy a fundamental right under the Constitution?",
     "Unanimous 9-judge bench: privacy is a fundamental right under Article 21. It has three aspects — "
     "informational privacy, bodily integrity, and decisional autonomy.",
     "Privacy is antecedent to the Constitution — a natural right. ADM Jabalpur is wrong.",
     "Privacy grounds data protection, digital rights, and LGBTQ+ rights."),
    ("Olga Tellis v. Bombay Municipal Corporation",
     "(1985) 3 SCC 545",
     "The BMC sought to evict pavement dwellers from Bombay. Petitioners argued eviction would deprive "
     "them of their livelihood.",
     "Is the right to livelihood part of the right to life under Article 21?",
     "Right to livelihood is part of right to life under Article 21. Persons cannot be evicted without "
     "being heard — mandatory procedural fairness.",
     "Article 21's sweep includes socio-economic rights — right to livelihood, shelter, food.",
     "Mandatory hearing required before eviction of pavement dwellers from public spaces."),
    ("Navtej Singh Johar v. Union of India",
     "(2018) 10 SCC 1",
     "Section 377 IPC criminalised consensual same-sex intercourse between adults. Petitioners challenged "
     "this as violating fundamental rights.",
     "Whether Section 377 IPC violates Articles 14, 15, 19, and 21.",
     "Section 377 is unconstitutional insofar as it applies to consensual same-sex intercourse between "
     "adults. Constitutional morality overrides social morality.",
     "Sexual orientation is an essential immutable attribute protected under Article 21 privacy and dignity.",
     "LGBTQ+ persons have equal citizenship rights. Constitutional morality is superior to popular morality."),
    ("Indra Sawhney v. Union of India",
     "(1992) 3 SCC 217",
     "Mandal Commission OBC reservations challenged. Total reservations exceed 50% with OBC additions.",
     "Whether 27% OBC reservation is valid. Whether total reservations can exceed 50%.",
     "OBC reservation valid but total reservations cannot exceed 50%. Creamy layer must be excluded. "
     "Reservations in promotions not permissible (subject to constitutional amendment).",
     "50% ceiling rule; creamy layer doctrine; backwardness determined primarily by social/educational criteria.",
     "Reservations are means to equality, not ends in themselves. Cannot become the rule."),
    ("Minerva Mills Ltd. v. Union of India",
     "(1980) 3 SCC 625",
     "42nd Constitutional Amendment gave Parliament unlimited amending power and made DPSPs override "
     "Fundamental Rights. Challenged as unconstitutional.",
     "Whether 42nd Amendment's grant of unlimited amending power and DPSP supremacy violates Basic Structure.",
     "Sections 4 and 55 of 42nd Amendment are unconstitutional. Balance between rights and directives "
     "is itself part of Basic Structure. Judicial review cannot be excluded.",
     "Balance between Fundamental Rights and DPSPs is a Basic Structure feature.",
     "Parliament cannot grant itself unlimited amending power or exclude judicial review."),
    ("Mohori Bibee v. Dharmodas Ghose",
     "(1903) 30 Cal. 539 (PC)",
     "A minor mortgaged his property to a moneylender. The minor's mother sued for cancellation of "
     "the mortgage on grounds of minority.",
     "Is a contract entered into by a minor valid and enforceable?",
     "Contract by a minor is void ab initio — it has no legal effect whatsoever. Mortgagee cannot "
     "recover the money advanced.",
     "Minors lack contractual capacity under Indian Contract Act 1872 (Section 11).",
     "Agreements with minors are void and cannot be ratified upon attaining majority."),
    ("M.C. Mehta v. Union of India (Oleum Gas)",
     "(1987) 1 SCC 395",
     "Oleum gas leaked from the Shriram plant in Delhi, injuring persons. PIL filed seeking principles "
     "of liability for hazardous industries.",
     "Whether absolute liability applies to hazardous industries, stricter than Rylands v. Fletcher.",
     "Absolute liability rule created: enterprises in inherently dangerous activities are absolutely and "
     "non-derogably liable. No exceptions available unlike strict liability.",
     "Absolute liability — India's unique contribution to tort law. No defences for hazardous industry harm.",
     "Enterprise engaging in hazardous activities is absolutely liable for all harm caused."),
]

STATUTES = [
    ("Indian Contract Act, 1872",
     "Act No. 9 of 1872",
     "Governs the law of contracts in India. Defines a valid contract as an agreement enforceable by law. "
     "Covers offer, acceptance, consideration, capacity, free consent, legality, and remedies.",
     "Section 10 ICA 1872 states all agreements are contracts if made by free consent of competent parties "
     "for lawful consideration and a lawful object."),
    ("Indian Penal Code, 1860",
     "Act No. 45 of 1860",
     "India's principal criminal code defining offences and prescribing punishments. Now replaced by "
     "Bharatiya Nyaya Sanhita 2023 from 1 July 2024.",
     "IPC Section 300 defines murder; Section 378 defines theft; Section 420 defines cheating."),
    ("Constitution of India, 1950",
     "26 January 1950",
     "The supreme law of India. Contains Fundamental Rights (Part III), Directive Principles (Part IV), "
     "Fundamental Duties (Part IVA), and the federal structure. Has 470 articles and 12 schedules.",
     "Article 21: No person shall be deprived of his life or personal liberty except according to procedure "
     "established by law."),
    ("Protection of Women from Sexual Harassment Act, 2013",
     "Act No. 14 of 2013",
     "Implemented following Vishaka v. State of Rajasthan guidelines. Mandates Internal Complaints Committees "
     "in workplaces and defines sexual harassment.",
     "POSH Act Section 2(n) defines sexual harassment to include unwelcome physical contact, demand for sexual "
     "favours, and hostile work environment."),
    ("Bharatiya Nyaya Sanhita, 2023",
     "Act No. 45 of 2023",
     "Replaces the Indian Penal Code 1860 from 1 July 2024. Modernises criminal law, introduces organised "
     "crime (Section 111), terrorism (Section 113), community service as punishment.",
     "BNS Section 101 corresponds to IPC 300 (murder); Section 63 deals with rape; Section 103 with culpable homicide."),
    ("Arthashastra (Kautilya)",
     "c. 3rd century BCE",
     "Ancient Indian treatise on statecraft and economic policy. Contains detailed provisions on Danda "
     "(punishment), taxation, trade regulation, and judicial procedure. A precursor to administrative law.",
     "Arthashastra Book III discusses civil law including contracts, property, and inheritance; "
     "Book IV addresses criminal justice and sentencing guidelines."),
    ("Bharatiya Nagarik Suraksha Sanhita, 2023",
     "Act No. 46 of 2023",
     "Replaces the Code of Criminal Procedure 1973 from 1 July 2024. Key changes: mandatory videography "
     "of crime scenes; zero FIR; audio-visual recording of victim statements; 60/90-day challan filing deadline.",
     "BNSS Section 173 corresponds to CrPC Section 154 (FIR); zero FIR allows filing at any police station."),
    ("Bharatiya Sakshya Adhiniyam, 2023",
     "Act No. 47 of 2023",
     "Replaces the Indian Evidence Act 1872 from 1 July 2024. Updates electronic evidence provisions, "
     "expands definition of 'document' to include electronic records.",
     "BSA Section 57 (electronic records as evidence) updates the digital evidence framework."),
]


def seed() -> None:
    """Seed SQLite tables with initial data."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executemany(
        "INSERT OR IGNORE INTO glossary (term, definition, example) VALUES (?, ?, ?)",
        GLOSSARY
    )
    cur.executemany(
        """INSERT OR IGNORE INTO cases
           (title, citation, facts, issue, judgment, principle, snippet)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        CASES
    )
    cur.executemany(
        """INSERT OR IGNORE INTO statutes
           (title, citation, description, snippet)
           VALUES (?, ?, ?, ?)""",
        STATUTES
    )

    conn.commit()
    conn.close()
    logger.info(
        f"[Seed] {len(GLOSSARY)} glossary | {len(CASES)} cases | {len(STATUTES)} statutes inserted."
    )


def seed_chromadb() -> None:
    """
    Load seed corpus JSON files into ChromaDB collections.
    Safe to run multiple times — uses upsert with content-hash IDs.
    """
    try:
        from services.rag_engine import get_rag_engine
        engine = get_rag_engine()
    except Exception as exc:
        logger.error(f"[Seed] RAG engine unavailable — skipping ChromaDB seed: {exc}")
        return

    corpus_files = {
        "iks_texts": "iks_concepts.json",
        "modern_law": "modern_law_corpus.json",
        "case_law": "landmark_cases.json",
    }

    total_added = 0
    for collection_name, filename in corpus_files.items():
        filepath = os.path.join(SEED_CORPUS_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"[Seed] Corpus file not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            entries = json.load(f)

        documents, metadatas, ids = [], [], []
        for entry in entries:
            text = entry.get("text", "")
            if not text and "facts" in entry:
                # Case law entries
                text = (
                    f"{entry.get('title', '')}\n\n"
                    f"FACTS: {entry.get('facts', '')}\n\n"
                    f"ISSUE: {entry.get('issue', '')}\n\n"
                    f"HOLDING: {entry.get('holding', '')}\n\n"
                    f"RATIO: {entry.get('ratio', '')}\n\n"
                    f"IKS CONNECTION: {entry.get('iks_connection', '')}"
                )

            if not text:
                continue

            doc_id = entry.get("id", hashlib.md5(text.encode()).hexdigest()[:16])
            citations = entry.get("citations", [])
            modern_connections = entry.get("modern_connections", [])

            meta = {
                "title": entry.get("title", entry.get("concept", "")),
                "citation": entry.get("citation", "; ".join(citations[:2]) if citations else ""),
                "section": entry.get("concept", entry.get("title", "")),
                "source_type": collection_name,
                "category": collection_name,
                "page": "",
            }
            documents.append(text)
            metadatas.append(meta)
            ids.append(doc_id)

        if documents:
            try:
                engine.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                    collection_name=collection_name,
                )
                logger.info(f"[Seed] Added {len(documents)} docs to '{collection_name}'")
                total_added += len(documents)
            except Exception as exc:
                logger.error(f"[Seed] Failed to add to '{collection_name}': {exc}")

    # Seed glossary collection from GLOSSARY list
    if GLOSSARY:
        gloss_docs, gloss_metas, gloss_ids = [], [], []
        for term, definition, example in GLOSSARY:
            text = f"{term}: {definition}\n\nExample: {example}"
            doc_id = f"glossary_{hashlib.md5(term.encode()).hexdigest()[:10]}"
            gloss_docs.append(text)
            gloss_metas.append({
                "title": term,
                "citation": "Legal Glossary",
                "section": term,
                "source_type": "Glossary",
                "category": "glossary",
                "page": "",
            })
            gloss_ids.append(doc_id)

        try:
            engine.add_documents(
                documents=gloss_docs,
                metadatas=gloss_metas,
                ids=gloss_ids,
                collection_name="glossary",
            )
            logger.info(f"[Seed] Added {len(gloss_docs)} glossary terms to ChromaDB")
            total_added += len(gloss_docs)
        except Exception as exc:
            logger.error(f"[Seed] Failed to seed glossary: {exc}")

    logger.info(f"[Seed] ChromaDB seeding complete — {total_added} total documents added")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    logging.basicConfig(level=logging.INFO)
    seed()
    seed_chromadb()
