"use client";

import { useState, useEffect, useRef } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Scenario {
  scenario_id: string;
  title: string;
  description: string;
  goal: string;
  difficulty: string;
  attack_families: string[];
  defense_description: string;
  tags: string[];
}

interface Technique {
  technique_id: string;
  family: string;
  name: string;
  description: string;
  tags: string[];
}

interface Message {
  role: string;
  content: string;
  is_injection: boolean;
}

interface Verdict {
  attack_succeeded: boolean;
  confidence: number;
  reasoning: string;
  method: string;
}

interface TechniqueInfo {
  technique_id: string;
  family: string;
  name: string;
  description: string;
  owasp_tag: string;
  why_it_works: string;
  how_to_mitigate: string;
}

interface SimulationResult {
  scenario_id: string;
  technique_id: string;
  mode: string;
  messages: Message[];
  verdict: Verdict;
  technique_info: TechniqueInfo | null;
  target_system_prompt: string;
  defense_description: string;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/api/scenarios`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

async function fetchTechniques(scenarioId: string): Promise<Technique[]> {
  const res = await fetch(
    `${API_BASE}/api/scenarios/${scenarioId}/techniques`
  );
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

async function runSimulation(
  scenarioId: string,
  techniqueId: string,
  mode: string
): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      scenario_id: scenarioId,
      technique_id: techniqueId,
      mode,
    }),
  });
  if (!res.ok) throw new Error(`Simulation failed: ${res.statusText}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Icons (inline SVG)
// ---------------------------------------------------------------------------

function ShieldIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  );
}

function WarningIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  );
}

function PlayIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 010 1.972l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z" />
    </svg>
  );
}

function TargetIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
    </svg>
  );
}

function ChevronIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  );
}

function UnlockIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
    </svg>
  );
}

function CodeIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
    </svg>
  );
}

function BookIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
    </svg>
  );
}

function FlaskIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  );
}

function Spinner({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={`${className} animate-spin`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}

function InfoIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
    </svg>
  );
}

function ChevronDownIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function Badge({
  children,
  variant = "gray",
}: {
  children: React.ReactNode;
  variant?: string;
}) {
  const styles: Record<string, string> = {
    green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    red: "bg-red-500/10 text-red-400 border-red-500/20",
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    gray: "bg-white/5 text-gray-400 border-white/10",
    purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded-md border ${styles[variant] || styles.gray}`}
    >
      {children}
    </span>
  );
}

function SandboxBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
      <ShieldIcon className="w-3 h-3" />
      Sandboxed
    </span>
  );
}

function ChatBubble({ message }: { message: Message }) {
  if (message.role === "system") {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-white/5 text-gray-500 text-[11px] px-3 py-1.5 rounded-full border border-white/10 font-medium tracking-wide">
          System Prompt
        </div>
      </div>
    );
  }

  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} my-2.5`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? message.is_injection
              ? "bg-red-500/10 text-red-100 border border-red-500/20 ring-1 ring-red-500/10"
              : "bg-blue-500/10 text-blue-100 border border-blue-500/20"
            : "bg-white/5 text-gray-200 border border-white/10"
        }`}
      >
        {message.is_injection && (
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-red-400/80 mb-1.5 font-semibold">
            <WarningIcon className="w-3 h-3" />
            Injection Payload
          </div>
        )}
        <div className="whitespace-pre-wrap">{message.content}</div>
      </div>
    </div>
  );
}

function VerdictCard({ verdict, mode }: { verdict: Verdict; mode: string }) {
  const succeeded = verdict.attack_succeeded;
  return (
    <div
      className={`rounded-xl border p-4 ${
        succeeded
          ? "bg-red-500/5 border-red-500/20"
          : "bg-emerald-500/5 border-emerald-500/20"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${
            succeeded ? "bg-red-500/15 text-red-400" : "bg-emerald-500/15 text-emerald-400"
          }`}
        >
          {succeeded ? <WarningIcon /> : <ShieldIcon />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-sm">
              {succeeded ? "Attack Succeeded" : "Attack Blocked"}
            </span>
            <Badge variant={succeeded ? "red" : "green"}>
              {Math.round(verdict.confidence * 100)}% confidence
            </Badge>
          </div>
          <p className="text-xs text-gray-500 mb-2">
            Mode: <span className="capitalize">{mode}</span>
          </p>
          <p className="text-sm text-gray-300">{verdict.reasoning}</p>
        </div>
      </div>
    </div>
  );
}

function SectionHeader({
  title,
  subtitle,
  variant = "default",
}: {
  title: string;
  subtitle?: string;
  variant?: "default" | "attack" | "defense" | "info";
}) {
  const colors = {
    default: "text-gray-500",
    attack: "text-red-400/80",
    defense: "text-emerald-400/80",
    info: "text-blue-400/80",
  };
  return (
    <div className="mb-3">
      <h3
        className={`text-[11px] uppercase tracking-widest font-semibold ${colors[variant]}`}
      >
        {title}
      </h3>
      {subtitle && (
        <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
      )}
    </div>
  );
}

function ExplanationPanel({ info }: { info: TechniqueInfo }) {
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-2 mb-2 flex-wrap">
          <h3 className="text-sm font-semibold text-gray-200">{info.name}</h3>
          <Badge variant="blue">{info.owasp_tag}</Badge>
          <Badge variant="gray">{info.family.replace(/_/g, " ")}</Badge>
        </div>
        <p className="text-sm text-gray-400 leading-relaxed">
          {info.description}
        </p>
      </div>

      <div className="border-t border-white/5 pt-4">
        <SectionHeader title="Why This Attack Works" variant="attack" />
        <p className="text-sm text-gray-300 leading-relaxed">
          {info.why_it_works}
        </p>
      </div>

      <div className="border-t border-white/5 pt-4">
        <SectionHeader
          title="Mitigation Guidance"
          subtitle="How to defend against this technique"
          variant="defense"
        />
        <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
          {info.how_to_mitigate}
        </div>
      </div>
    </div>
  );
}

function SystemPromptReveal({ prompt }: { prompt: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-white/10 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 bg-white/[0.02] hover:bg-white/[0.04] transition text-sm font-medium flex items-center justify-between"
      >
        <span className="flex items-center gap-2 text-gray-300">
          <CodeIcon className="w-4 h-4 text-gray-500" />
          View System Prompt
        </span>
        <ChevronDownIcon
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs text-gray-400 bg-black/20 overflow-x-auto whitespace-pre-wrap border-t border-white/5 font-mono leading-relaxed">
          {prompt}
        </pre>
      )}
    </div>
  );
}

function EmptyLabState() {
  return (
    <div className="border border-white/10 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[300px]">
      <PlayIcon className="w-10 h-10 text-gray-700 mb-3" />
      <p className="text-sm text-gray-500 font-medium mb-1">
        No simulation running
      </p>
      <p className="text-xs text-gray-600 max-w-[240px]">
        Select an attack technique above and run the simulation to see the
        interaction unfold.
      </p>
    </div>
  );
}

function EmptyExplanationState() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-6">
      <BookIcon className="w-8 h-8 text-gray-700 mb-2" />
      <p className="text-xs text-gray-500 max-w-[200px]">
        Run a simulation to see a detailed breakdown of the attack technique,
        why it works, and how to defend against it.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function PromptLabPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(
    null
  );
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [selectedTechnique, setSelectedTechnique] = useState<string>("");
  const [mode, setMode] = useState<"vulnerable" | "defended">("vulnerable");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [comparisonResult, setComparisonResult] =
    useState<SimulationResult | null>(null);
  const [scenariosLoading, setScenariosLoading] = useState(true);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchScenarios()
      .then((s) => {
        setScenarios(s);
        setScenariosLoading(false);
      })
      .catch(() => {
        setError(
          `Could not connect to the PromptLab API at ${API_BASE}. Make sure the backend is running.`
        );
        setScenariosLoading(false);
      });
  }, []);

  useEffect(() => {
    if (selectedScenario) {
      fetchTechniques(selectedScenario.scenario_id).then((t) => {
        setTechniques(t);
        if (t.length > 0) setSelectedTechnique(t[0].technique_id);
      });
    }
  }, [selectedScenario]);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [result, comparisonResult, mode]);

  const handleRun = async () => {
    if (!selectedScenario || !selectedTechnique) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setComparisonResult(null);

    try {
      const vulnResult = await runSimulation(
        selectedScenario.scenario_id,
        selectedTechnique,
        "vulnerable"
      );
      setResult(vulnResult);
      setMode("vulnerable");

      const defResult = await runSimulation(
        selectedScenario.scenario_id,
        selectedTechnique,
        "defended"
      );
      setComparisonResult(defResult);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  const activeResult = mode === "vulnerable" ? result : comparisonResult;
  const techniqueInfo =
    result?.technique_info || comparisonResult?.technique_info || null;

  // -------------------------------------------------------------------------
  // Landing Page
  // -------------------------------------------------------------------------
  if (!selectedScenario) {
    return (
      <div className="min-h-screen flex flex-col bg-[#0a0a0a]">
        {/* Header */}
        <header className="border-b border-white/[0.06] px-6 py-4">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-xl font-bold tracking-tight">
                <span className="text-emerald-400">Prompt</span>
                <span className="text-gray-100">Lab</span>
              </div>
              <SandboxBadge />
            </div>
            <span className="text-xs text-gray-600 hidden sm:block">
              Built on LLMMap
            </span>
          </div>
        </header>

        {/* Hero */}
        <main className="flex-1">
          <div className="max-w-5xl mx-auto px-6 w-full">
            {/* Hero section with subtle gradient background */}
            <section className="relative pt-20 pb-16">
              {/* Decorative gradient blob */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-emerald-500/[0.04] rounded-full blur-3xl pointer-events-none" />

              <div className="relative">
                <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight leading-[1.1] mb-6">
                  <span className="text-white">Learn AI attacks safely.</span>
                  <br />
                  <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">
                    Test defenses live.
                  </span>
                </h1>
                <p className="text-gray-400 text-lg max-w-xl leading-relaxed mb-10">
                  PromptLab is an interactive AI security lab for exploring prompt
                  injection, jailbreaks, and LLM defense strategies through
                  real-time sandbox simulations.
                </p>

                <div className="flex items-center gap-4 flex-wrap mb-10">
                  <a
                    href="#scenarios"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-black rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-400/30"
                  >
                    <FlaskIcon className="w-4 h-4" />
                    Open the Lab
                  </a>
                  <span className="text-sm text-gray-500">
                    No API keys required
                  </span>
                </div>

                {/* Feature highlights */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <ShieldIcon className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Sandboxed</p>
                      <p className="text-xs text-gray-500 mt-0.5">No external systems contacted</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <TargetIcon className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-200">227 Techniques</p>
                      <p className="text-xs text-gray-500 mt-0.5">Across 18 attack families</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <BookIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-gray-200">Learn by doing</p>
                      <p className="text-xs text-gray-500 mt-0.5">Attack, then defend, then understand</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Error */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-8 text-sm text-red-300 flex items-start gap-3">
                <InfoIcon className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium mb-1">Backend unavailable</p>
                  <p className="text-red-400/80 text-xs">{error}</p>
                </div>
              </div>
            )}

            {/* Scenarios */}
            <section id="scenarios" className="pb-20">
              <div className="flex items-center gap-3 mb-2">
                <h2 className="text-xs uppercase tracking-widest font-semibold text-gray-500">
                  Available Scenarios
                </h2>
                <div className="flex-1 h-px bg-white/[0.06]" />
              </div>
              <p className="text-sm text-gray-500 mb-8">
                Each scenario is an isolated sandbox target with a specific
                vulnerability to explore.
              </p>

              {scenariosLoading && !error && (
                <div className="border border-white/[0.06] rounded-xl p-12 text-center">
                  <Spinner className="w-5 h-5 text-gray-600 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">Loading scenarios...</p>
                </div>
              )}

              {!scenariosLoading && scenarios.length === 0 && !error && (
                <div className="border border-white/[0.06] border-dashed rounded-xl p-12 text-center">
                  <FlaskIcon className="w-8 h-8 text-gray-700 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No scenarios available.</p>
                </div>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                {scenarios.map((s) => (
                  <button
                    key={s.scenario_id}
                    onClick={() => setSelectedScenario(s)}
                    className="text-left border border-white/[0.06] rounded-xl p-6 hover:border-emerald-500/30 hover:bg-emerald-500/[0.03] transition-all group"
                  >
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <h3 className="font-semibold text-gray-100 group-hover:text-emerald-400 transition">
                        {s.title}
                      </h3>
                      <Badge variant="green">{s.difficulty}</Badge>
                    </div>
                    <p className="text-sm text-gray-400 mb-4 leading-relaxed">
                      {s.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-4">
                      <TargetIcon className="w-3.5 h-3.5 text-amber-400/70" />
                      <span>
                        Goal: <span className="text-amber-300/80 font-medium">{s.goal}</span>
                      </span>
                    </div>
                    <div className="flex gap-1.5 flex-wrap">
                      {s.tags.map((tag) => (
                        <Badge key={tag} variant="gray">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </section>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-white/[0.06] px-6 py-5">
          <div className="max-w-5xl mx-auto flex items-center justify-between text-xs text-gray-600">
            <span>
              PromptLab &mdash; for authorized security testing and education only.
            </span>
            <span className="hidden sm:block">
              Part of the LLMMap project
            </span>
          </div>
        </footer>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Lab View
  // -------------------------------------------------------------------------
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0a]">
      {/* Header */}
      <header className="border-b border-white/[0.06] px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setSelectedScenario(null);
                setResult(null);
                setComparisonResult(null);
                setTechniques([]);
              }}
              className="text-lg font-bold tracking-tight hover:opacity-80 transition"
            >
              <span className="text-emerald-400">Prompt</span>
              <span className="text-gray-100">Lab</span>
            </button>
            <ChevronIcon className="w-4 h-4 text-gray-700" />
            <span className="text-sm text-gray-400">
              {selectedScenario.title}
            </span>
          </div>
          <SandboxBadge />
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-6 py-6 w-full grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ---- Left Column: Scenario + Controls + Chat ---- */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {/* Scenario Description */}
          <div className="border border-white/[0.06] rounded-xl p-5 bg-white/[0.01]">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h2 className="font-semibold text-gray-100 mb-1">
                  {selectedScenario.title}
                </h2>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {selectedScenario.description}
                </p>
              </div>
              <Badge variant="green">{selectedScenario.difficulty}</Badge>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <TargetIcon className="w-3.5 h-3.5 text-amber-400/70" />
              <span className="text-gray-500">
                Attacker goal:{" "}
                <span className="text-amber-300/80 font-medium">
                  {selectedScenario.goal}
                </span>
              </span>
            </div>
          </div>

          {/* Attack Controls */}
          <div className="border border-white/[0.06] rounded-xl p-4 bg-white/[0.01]">
            <SectionHeader
              title="Attack Configuration"
              subtitle="Select a technique and run the simulation against both modes"
              variant="attack"
            />
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[200px]">
                <label className="text-xs text-gray-500 mb-1.5 block font-medium">
                  Technique
                </label>
                <select
                  value={selectedTechnique}
                  onChange={(e) => setSelectedTechnique(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 transition"
                >
                  {techniques.map((t) => (
                    <option key={t.technique_id} value={t.technique_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleRun}
                disabled={loading}
                className="inline-flex items-center gap-2 px-5 py-2 bg-emerald-500 hover:bg-emerald-400 text-black disabled:bg-gray-800 disabled:text-gray-500 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-500/20 hover:shadow-emerald-400/30 disabled:shadow-none"
              >
                {loading ? (
                  <>
                    <Spinner />
                    Running...
                  </>
                ) : (
                  <>
                    <PlayIcon />
                    Run Simulation
                  </>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm text-red-300 flex items-start gap-2">
              <InfoIcon className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          {/* Vulnerable / Defended Mode Toggle */}
          {result && comparisonResult && (
            <div className="flex gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/[0.06]">
              <button
                onClick={() => setMode("vulnerable")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  mode === "vulnerable"
                    ? "bg-red-500/10 text-red-300 border border-red-500/20 shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                <UnlockIcon className="w-3.5 h-3.5" />
                Vulnerable
              </button>
              <button
                onClick={() => setMode("defended")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  mode === "defended"
                    ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                <ShieldIcon className="w-3.5 h-3.5" />
                Defended
              </button>
            </div>
          )}

          {/* Chat Interaction */}
          {activeResult ? (
            <div
              ref={chatRef}
              className="border border-white/[0.06] rounded-xl p-4 flex-1 min-h-[300px] max-h-[500px] overflow-y-auto bg-white/[0.01]"
            >
              <div className="mb-3">
                <SectionHeader
                  title="Simulation Trace"
                  subtitle="Messages exchanged between the attacker and target"
                  variant={mode === "vulnerable" ? "attack" : "defense"}
                />
              </div>
              {activeResult.messages.map((msg, i) => (
                <ChatBubble key={i} message={msg} />
              ))}
            </div>
          ) : (
            <EmptyLabState />
          )}

          {/* Verdict */}
          {activeResult && (
            <VerdictCard
              verdict={activeResult.verdict}
              mode={activeResult.mode}
            />
          )}

          {/* System prompt reveal */}
          {activeResult?.target_system_prompt && (
            <SystemPromptReveal prompt={activeResult.target_system_prompt} />
          )}
        </div>

        {/* ---- Right Column: Analysis ---- */}
        <div className="flex flex-col gap-4">
          {/* Attack Explanation */}
          <div className="border border-white/[0.06] rounded-xl p-5 bg-white/[0.01]">
            <SectionHeader
              title="Attack Explanation"
              subtitle="Technique details and OWASP classification"
              variant="info"
            />
            {techniqueInfo ? (
              <ExplanationPanel info={techniqueInfo} />
            ) : (
              <EmptyExplanationState />
            )}
          </div>

          {/* Active Defense Info */}
          {activeResult?.defense_description && mode === "defended" && (
            <div className="border border-emerald-500/20 rounded-xl p-5 bg-emerald-500/[0.03]">
              <SectionHeader
                title="Active Defense"
                subtitle="Protection measures applied in defended mode"
                variant="defense"
              />
              <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {activeResult.defense_description}
              </div>
            </div>
          )}

          {/* Vulnerable vs Defended Comparison */}
          {result && comparisonResult && (
            <div className="border border-white/[0.06] rounded-xl p-5 bg-white/[0.01]">
              <SectionHeader
                title="Comparison"
                subtitle="Same technique, different security postures"
              />
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-400/60" />
                    <span className="text-gray-400">Vulnerable</span>
                  </div>
                  <span
                    className={`font-semibold text-xs px-2 py-0.5 rounded ${
                      result.verdict.attack_succeeded
                        ? "bg-red-500/15 text-red-400"
                        : "bg-emerald-500/15 text-emerald-400"
                    }`}
                  >
                    {result.verdict.attack_succeeded ? "Compromised" : "Held"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400/60" />
                    <span className="text-gray-400">Defended</span>
                  </div>
                  <span
                    className={`font-semibold text-xs px-2 py-0.5 rounded ${
                      comparisonResult.verdict.attack_succeeded
                        ? "bg-red-500/15 text-red-400"
                        : "bg-emerald-500/15 text-emerald-400"
                    }`}
                  >
                    {comparisonResult.verdict.attack_succeeded
                      ? "Compromised"
                      : "Blocked"}
                  </span>
                </div>
                <div className="border-t border-white/5 pt-3 mt-3">
                  <p className="text-[11px] text-gray-600 leading-relaxed">
                    {result.verdict.attack_succeeded &&
                    !comparisonResult.verdict.attack_succeeded
                      ? "The defense successfully mitigated this attack. Toggle between modes to compare the interaction traces."
                      : result.verdict.attack_succeeded &&
                          comparisonResult.verdict.attack_succeeded
                        ? "The defense did not stop this technique. Consider layering additional mitigations."
                        : "This technique was ineffective against both configurations."}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <span>
            PromptLab &mdash; sandboxed simulations for education and authorized
            security testing only.
          </span>
          <span className="hidden sm:block">
            No external systems contacted
          </span>
        </div>
      </footer>
    </div>
  );
}
