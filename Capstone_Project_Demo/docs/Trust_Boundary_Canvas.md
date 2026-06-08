# Trust Boundary Canvas — Compliance Knowledge Agent

**Version:** 1.0  
**Date:** 2025-06-06  
**Owner:** Architecture Team + Chief Compliance Officer  
**Review Cycle:** Quarterly  

---

## Trust Architecture Principle

> **AI-Recommend / Human-Approve**
> 
> No AI-generated compliance answer is acted upon without review by a qualified compliance officer. The system is a decision-support tool, not a decision-making authority.

This canvas maps every system capability to its trust zone, defines the human oversight role, and specifies escalation triggers.

---

## Zone Definitions

| Zone | Name | Description |
|------|------|-------------|
| **Zone 0** | Fully Automated | No human review; system acts autonomously |
| **Zone 1** | AI-Recommend / Human-Confirm | Human briefly reviews and approves AI output |
| **Zone 2** | AI-Assist / Human-Decide | AI provides options; human makes final decision |
| **Zone 3** | Human-Only | No AI involvement; human expertise only |

---

## Capability Map

### ZONE 0 — Fully Automated (No Human in Loop)
*The Compliance Knowledge Agent does NOT operate in Zone 0 for any compliance-critical function.*

| Capability | Rationale |
|------------|-----------|
| Document ingestion (chunking, embedding, storage) | Non-consequential data processing; errors detected in evaluation |
| Health check and monitoring | System telemetry; no regulatory impact |
| Audit log generation | Automated logging required for auditability; no compliance decision |

---

### ZONE 1 — AI-Recommend / Human-Confirm

These are the core Q&A capabilities. AI generates the answer; compliance officer reviews before action.

| Capability | AI Role | Human Role | Escalation Trigger |
|------------|---------|------------|-------------------|
| **Policy lookup** (e.g., "What is the SAR filing deadline?") | Retrieve relevant chunks, generate citation-grounded answer | Compliance officer reads answer + citations, confirms accuracy, records decision | Confidence = LOW; reranker score < 0.3 |
| **Regulatory threshold queries** (e.g., "What is the CTR threshold?") | Surface exact threshold from policy doc with citation | Officer verifies threshold against source document | Any numerical threshold answer |
| **Audit finding lookup** | Retrieve finding severity, status, remediation | Officer confirms finding status is current (may have been updated) | Finding marked CRITICAL |
| **Training requirement lookup** | Surface training deadlines and requirements | Officer confirms requirement applies to the queried role/jurisdiction | Jurisdiction-specific training query |
| **Standard escalation path lookup** | Retrieve documented escalation paths from policy | Officer confirms path is current (org changes may not be in docs) | Query involves senior management escalation |

---

### ZONE 2 — AI-Assist / Human-Decide

AI provides structured information but the human makes the substantive compliance judgment.

| Capability | AI Role | Human Role | Why Zone 2 |
|------------|---------|------------|------------|
| **Risk rating determination** (e.g., customer risk tier) | Surface risk classification criteria from policy | Compliance officer applies criteria to specific customer facts | Requires judgment on specific facts not in documents |
| **Regulatory interpretation** (e.g., "Does this transaction require a SAR?") | Provide relevant policy text, thresholds, and similar-fact guidance | Officer makes final determination; may consult legal counsel | Legal interpretation requires human judgment; wrong answer = regulatory violation |
| **Jurisdiction-specific guidance** (e.g., state consumer protection laws) | Surface any federal guidance in corpus; flag jurisdiction-specific gap | Local legal counsel or jurisdiction specialist decides | System corpus may not contain all applicable state laws |
| **Policy conflict resolution** | Identify relevant sections from multiple policies | CCO resolves conflict per organizational policy hierarchy | Requires authority to resolve inter-policy ambiguity |
| **SAR filing decision** | Surface AML policy thresholds and red flag indicators | Trained AML analyst or compliance officer makes filing decision | SAR filing is a regulatory act; must be human decision |
| **New product compliance review** | Surface applicable regulations for product category | Compliance team conducts full review using AI-surfaced starting points | Novel products may not match existing corpus exactly |

---

### ZONE 3 — Human-Only (No AI Involvement)

| Capability | Rationale |
|------------|-----------|
| **Regulatory self-reporting decisions** (e.g., reporting to OCC, FinCEN) | Regulatory notification is a legal act with material consequences; requires authorized officer |
| **SAR signature and submission** | Authorized compliance officer must certify SAR before FinCEN submission |
| **Consent orders and regulatory responses** | Requires legal review and executive authorization |
| **Enforcement action responses** | Legal and regulatory strategy; cannot be delegated to AI |
| **Whistleblower investigation findings** | Requires qualified investigator and confidentiality protections |
| **Board-level risk reporting** | Human narrative, strategic judgment; AI may assist in drafting only |
| **Customer adverse action communication** | Legal notice with regulatory obligations (ECOA, Reg B) |

---

## Escalation Path Matrix

| Trigger | Escalation Path | Timeline |
|---------|----------------|----------|
| AI confidence = LOW | Compliance Business Partner → CCO SME | Within 1 business day |
| Jurisdiction-specific query | Regulatory Affairs → External legal counsel | Within 2 business days |
| Policy boundary / ambiguity | CCO (Policy owner arbitration) | Within 3 business days |
| Novel regulatory requirement (not in corpus) | Regulatory Affairs Research → Legal | Within 5 business days |
| Conflicting regulatory requirements | CCO + General Counsel | Within 5 business days |
| CRITICAL audit finding query | CCO + Board Risk Committee notification | Same day |
| Any SAR-related interpretation | AML Compliance Manager → CCO | Within 2 hours |

---

## Trust Architecture Controls

| Control | Description | Responsible |
|---------|-------------|-------------|
| **Citation Requirement** | Every AI answer must cite specific policy section | Enforced in LLM prompt |
| **Confidence Score** | Every answer carries HIGH / MEDIUM / LOW confidence | RAG pipeline |
| **Escalation Flags** | Low confidence, jurisdiction, and boundary queries flagged automatically | RAG pipeline |
| **Audit Log** | All queries and AI responses logged for 3 years | Application layer |
| **Human Approval Record** | Officers must log when they act on AI-provided guidance | Compliance workflow |
| **Trust Notice** | Every API response carries AI-Recommend / Human-Approve notice | API response model |
| **Model Validation** | System classified as Tier 1 model; annual independent validation required | MRM per REG-BUL-005 |
| **Access Control** | API access restricted to authenticated compliance officers | API security layer |

---

## What This System Is NOT

- **Not a legal advice system.** Does not constitute legal counsel.
- **Not a regulatory decision engine.** Cannot file SARs, CTRs, or regulatory reports.
- **Not a source of truth for novel regulatory questions.** Corpus is point-in-time; regulations change.
- **Not a substitute for qualified compliance expertise.** Supports, does not replace, human judgment.
