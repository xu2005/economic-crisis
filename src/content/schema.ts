export type EvidenceLevel = 'Fact' | 'Strong evidence' | 'Interpretation' | 'Hypothesis' | 'Scenario' | 'Open question';
export interface Source { id: string; title: string; url?: string; date: string; accessedAt: string; status: 'Verified' | 'Source pending' | 'User brief'; }
export interface Thesis { statement: string; level: EvidenceLevel; supporting: string[]; counter: string[]; alternatives: string[]; falsifiers: string[]; watch: string[]; }
export interface Section { id: string; title: string; text: string[]; points?: string[]; sourceIds?: string[]; level?: EvidenceLevel; }
export interface ResearchEntry {
  id: string; slug: string; title: string; subtitle: string; summary: string;
  status: 'Research' | 'Draft' | 'Reviewed'; updatedAt: string; createdAt: string;
  topics: string[]; regions: string[]; period: string; evidenceLevel: EvidenceLevel;
  confidence: string; thesis: Thesis[]; mechanisms: string[][]; counterArguments: string[];
  falsifiers: string[]; sources: Source[]; related: string[]; sections: Section[];
  revisions: { version: string; date: string; change: string }[];
}
export interface Indicator { id: string; label: string; value: number | null; unit: string; date: string | null; source: string; sourceUrl?: string; frequency: string; status: 'Awaiting data' | 'Snapshot' | 'Model output'; notes: string; updatedAt: string; }
export interface Scenario { id: string; name: string; premise: string; triggers: string[]; transmission: string[]; indicators: string[]; policyResponses: string[]; implications: string[]; falsifiers: string[]; uncertainty: 'Low' | 'Medium' | 'High'; }
export interface ModelSpec { id: string; path: string; title: string; subtitle: string; status: string; purpose: string; inputs: string[]; assumptions: string[]; formula: string; output: string; limitations: string[]; version: string; updated: string; changelog: string[]; }
