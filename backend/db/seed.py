from db.database import get_connection

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
     "Most criminal offences require both Actus Reus and Mens Rea.",
     "IPC Section 300 requires proof of intention or knowledge to establish murder."),
    ("Actus Reus",
     "Latin for 'guilty act' — the physical element of a crime, i.e., the voluntary act or omission that "
     "constitutes the crime.",
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
]

CASES = [
    ("Kesavananda Bharati v. State of Kerala",
     "AIR 1973 SC 1461",
     "The petitioner challenged the Kerala Land Reforms Amendment Act. The broader question was whether "
     "Parliament's power to amend the Constitution under Article 368 was unlimited.",
     "Can Parliament amend any part of the Constitution, including Fundamental Rights?",
     "The Supreme Court held (7:6) that Parliament can amend the Constitution but cannot alter its Basic Structure.",
     "Basic Structure Doctrine — certain core features of the Constitution (judicial review, separation of powers, "
     "federalism, secularism) are inviolable.",
     "Parliament cannot abrogate the Basic Structure of the Indian Constitution."),
    ("Maneka Gandhi v. Union of India",
     "AIR 1978 SC 597",
     "The petitioner's passport was impounded by the government without providing reasons. She challenged "
     "this as violating Article 21.",
     "Does Article 21's 'procedure established by law' require the procedure to be fair, just, and reasonable?",
     "The Supreme Court overruled A.K. Gopalan and held that procedure under Article 21 must satisfy "
     "Articles 14 and 19 as well. The procedure must be fair, just, and reasonable.",
     "Right to Life (Article 21) is not merely physical existence but includes the right to live with dignity.",
     "Passports cannot be impounded without a fair procedure that satisfies due process."),
    ("Vishaka v. State of Rajasthan",
     "AIR 1997 SC 3011",
     "Following the gang rape of a social worker, women's rights groups filed a PIL seeking enforcement of "
     "the fundamental right to work in a safe environment.",
     "Do working women have a fundamental right to a safe workplace free from sexual harassment?",
     "The Supreme Court issued binding guidelines (Vishaka Guidelines) to prevent sexual harassment at workplaces, "
     "laying the foundation for the POSH Act 2013.",
     "Judicial activism can fill legislative vacuum — courts can issue enforceable guidelines in absence of legislation.",
     "Sexual harassment at the workplace violates Articles 14, 15, and 21 of the Constitution."),
    ("State of Maharashtra v. Madhkar Narayan",
     "AIR 1991 SC 207",
     "A woman was forcibly subjected to an indecent act. The accused claimed she was of 'easy virtue' "
     "and hence testimony was unreliable.",
     "Can the character of a victim of sexual assault be used to discredit her testimony?",
     "The Supreme Court held that every woman, regardless of her character, has a right to privacy and bodily integrity.",
     "Character evidence of sexual assault victims is inadmissible to challenge credibility.",
     "Victim's past conduct is irrelevant to consent in sexual assault cases."),
    ("Mohori Bibee v. Dharmodas Ghose",
     "(1903) 30 IA 114 PC",
     "A minor mortgaged his property to a moneylender. Later, the minor sought to void the mortgage.",
     "Is a contract entered into by a minor valid and enforceable?",
     "The Privy Council held that a contract with a minor is void ab initio — it has no legal effect whatsoever.",
     "Minors lack contractual capacity under Indian Contract Act 1872.",
     "Agreements with minors are void and cannot be ratified upon attaining majority."),
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
     "India's principal criminal code defining offences and prescribing punishments. Covers crimes against "
     "the state, body, property, and public order. Now replaced by Bharatiya Nyaya Sanhita 2023.",
     "IPC Section 300 defines murder; Section 378 defines theft; Section 420 defines cheating."),
    ("Constitution of India, 1950",
     "26 January 1950",
     "The supreme law of India. Contains fundamental rights (Part III), directive principles (Part IV), "
     "fundamental duties (Part IVA), and the federal structure. Has 470 articles and 12 schedules.",
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
     "Replaces the Indian Penal Code 1860. Modernises criminal law, introduces new offences including "
     "organised crime and terrorism, and aligns punishment with constitutional values.",
     "BNS Section 103 corresponds to IPC 300 (murder); Section 316 deals with organised crime."),
    ("Arthashastra (Kautilya)",
     "c. 3rd century BCE",
     "Ancient Indian treatise on statecraft and economic policy. Contains detailed provisions on Danda "
     "(punishment), taxation, trade regulation, and judicial procedure. A precursor to administrative law.",
     "Arthashastra Book III discusses civil law including contracts, property, and inheritance — "
     "remarkably modern in conception."),
]

def seed():
    conn = get_connection()
    cur = conn.cursor()

    # Glossary
    cur.executemany(
        "INSERT OR IGNORE INTO glossary (term, definition, example) VALUES (?, ?, ?)",
        GLOSSARY
    )

    # Cases
    cur.executemany(
        """INSERT OR IGNORE INTO cases
           (title, citation, facts, issue, judgment, principle, snippet)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        CASES
    )

    # Statutes
    cur.executemany(
        """INSERT OR IGNORE INTO statutes
           (title, citation, description, snippet)
           VALUES (?, ?, ?, ?)""",
        STATUTES
    )

    conn.commit()
    conn.close()
    print(f"[Seed] {len(GLOSSARY)} glossary | {len(CASES)} cases | {len(STATUTES)} statutes inserted.")


if __name__ == "__main__":
    seed()
