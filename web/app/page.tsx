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

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
);

async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${API_BASE}/api/scenarios`);
  return res.json();
}

async function fetchTechniques(scenarioId: string): Promise<Technique[]> {
  const res = await fetch(
    `${API_BASE}/api/scenarios/${scenarioId}/techniques`
  );
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
    green: "bg-emerald-900/50 text-emerald-300 border-emerald-700/60",
    red: "bg-red-900/50 text-red-300 border-red-700/60",
    blue: "bg-blue-900/50 text-blue-300 border-blue-700/60",
    amber: "bg-amber-900/50 text-amber-300 border-amber-700/60",
    gray: "bg-gray-800/60 text-gray-400 border-gray-700/60",
    purple: "bg-purple-900/50 text-purple-300 border-purple-700/60",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 text-[11px] font-medium rounded border ${styles[variant] || styles.gray}`}
    >
      {children}
    </span>
  );
}

function SandboxBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-medium rounded-full bg-emerald-950/40 text-emerald-400 border border-emerald-800/50">
      <svg
        className="w-3 h-3"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
        />
      </svg>
      Sandboxed
    </span>
  );
}

function ChatBubble({ message }: { message: Message }) {
  if (message.role === "system") {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-gray-800/40 text-gray-500 text-[11px] px-3 py-1.5 rounded-full border border-gray-700/50 font-medium tracking-wide">
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
              ? "bg-red-950/40 text-red-100 border border-red-800/40 ring-1 ring-red-900/30"
              : "bg-blue-950/40 text-blue-100 border border-blue-800/40"
            : "bg-gray-800/60 text-gray-200 border border-gray-700/50"
        }`}
      >
        {message.is_injection && (
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-red-400/80 mb-1.5 font-semibold">
            <svg
              className="w-3 h-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
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
          ? "bg-red-950/20 border-red-800/50"
          : "bg-emerald-950/20 border-emerald-800/50"
      }`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm ${
            succeeded ? "bg-red-900/50 text-red-300" : "bg-emerald-900/50 text-emerald-300"
          }`}
        >
          {succeeded ? (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          )}
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
      {/* Technique identity */}
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

      {/* Why it works */}
      <div className="border-t border-gray-800/60 pt-4">
        <SectionHeader
          title="Why This Attack Works"
          variant="attack"
        />
        <p className="text-sm text-gray-300 leading-relaxed">
          {info.why_it_works}
        </p>
      </div>

      {/* Mitigation guidance */}
      <div className="border-t border-gray-800/60 pt-4">
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
    <div className="border border-gray-800/60 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 bg-gray-800/30 hover:bg-gray-800/50 transition text-sm font-medium flex items-center justify-between"
      >
        <span className="flex items-center gap-2 text-gray-300">
          <svg
            className="w-4 h-4 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
            />
          </svg>
          View System Prompt
        </span>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19.5 8.25l-7.5 7.5-7.5-7.5"
          />
        </svg>
      </button>
      {open && (
        <pre className="px-4 py-3 text-xs text-gray-400 bg-gray-900/30 overflow-x-auto whitespace-pre-wrap border-t border-gray-800/60 font-mono leading-relaxed">
          {prompt}
        </pre>
      )}
    </div>
  );
}

function EmptyLabState() {
  return (
    <div className="border border-gray-800/40 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center min-h-[300px]">
      <svg
        className="w-10 h-10 text-gray-700 mb-3"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 010 1.972l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z"
        />
      </svg>
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
      <svg
        className="w-8 h-8 text-gray-700 mb-2"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
        />
      </svg>
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
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() =>
        setError(
          `Could not connect to the PromptLab API at ${API_BASE}. Make sure the backend is running.`
        )
      );
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
      <div className="min-h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-gray-800/60 px-6 py-4">
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-xl font-bold tracking-tight">
                <span className="text-emerald-400">Prompt</span>
                <span className="text-gray-200">Lab</span>
              </div>
              <SandboxBadge />
            </div>
            <span className="text-[11px] text-gray-600 hidden sm:block">
              Built on LLMMap
            </span>
          </div>
        </header>

        {/* Hero */}
        <main className="flex-1 max-w-5xl mx-auto px-6 w-full">
          <section className="pt-16 pb-12">
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-tight mb-4">
              Learn AI attacks safely.
              <br />
              <span className="text-emerald-400">Test defenses live.</span>
            </h1>
            <p className="text-gray-400 text-lg max-w-2xl leading-relaxed mb-8">
              PromptLab is an interactive AI security lab for exploring prompt
              injection, jailbreaks, and LLM defense strategies through
              real-time sandbox simulations.
            </p>

            <div className="flex items-center gap-3 flex-wrap mb-6">
              <a
                href="#scenarios"
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-semibold transition"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"
                  />
                </svg>
                Open the Lab
              </a>
              <span className="text-sm text-gray-600">
                No API keys required
              </span>
            </div>

            {/* Safety callout */}
            <div className="inline-flex items-start gap-2.5 px-4 py-3 rounded-lg bg-gray-900/50 border border-gray-800/60 max-w-lg">
              <svg
                className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                />
              </svg>
              <p className="text-xs text-gray-400 leading-relaxed">
                All simulations run against built-in sandbox scenarios only.
                No external systems are contacted. Designed for education and
                authorized security testing.
              </p>
            </div>
          </section>

          {error && (
            <div className="bg-red-950/30 border border-red-800/50 rounded-lg p-4 mb-6 text-sm text-red-300 flex items-start gap-3">
              <svg
                className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              {error}
            </div>
          )}

          {/* Scenarios */}
          <section id="scenarios" className="pb-16">
            <SectionHeader title="Available Scenarios" variant="default" />
            <p className="text-sm text-gray-500 mb-6">
              Each scenario is an isolated sandbox target with a specific
              vulnerability to explore.
            </p>

            {scenarios.length === 0 && !error && (
              <div className="border border-gray-800/40 border-dashed rounded-xl p-8 text-center">
                <p className="text-sm text-gray-500">
                  Loading scenarios...
                </p>
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              {scenarios.map((s) => (
                <button
                  key={s.scenario_id}
                  onClick={() => setSelectedScenario(s)}
                  className="text-left border border-gray-800/60 rounded-xl p-5 hover:border-emerald-700/60 hover:bg-emerald-950/10 transition group"
                >
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <h3 className="font-semibold text-gray-200 group-hover:text-emerald-400 transition">
                      {s.title}
                    </h3>
                    <Badge variant="green">{s.difficulty}</Badge>
                  </div>
                  <p className="text-sm text-gray-400 mb-3 leading-relaxed">
                    {s.description}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
                    <svg
                      className="w-3.5 h-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
                      />
                    </svg>
                    <span>
                      Goal: <span className="text-amber-400/80">{s.goal}</span>
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
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-800/60 px-6 py-4">
          <div className="max-w-5xl mx-auto flex items-center justify-between text-[11px] text-gray-600">
            <span>
              PromptLab &mdash; for authorized security testing and education
              only.
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
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800/60 px-6 py-3">
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
              <span className="text-gray-200">Lab</span>
            </button>
            <svg
              className="w-4 h-4 text-gray-700"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.25 4.5l7.5 7.5-7.5 7.5"
              />
            </svg>
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
          <div className="border border-gray-800/60 rounded-xl p-5">
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h2 className="font-semibold text-gray-200 mb-1">
                  {selectedScenario.title}
                </h2>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {selectedScenario.description}
                </p>
              </div>
              <Badge variant="green">{selectedScenario.difficulty}</Badge>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <svg
                className="w-3.5 h-3.5 text-amber-400/70"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
                />
              </svg>
              <span className="text-gray-500">
                Attacker goal:{" "}
                <span className="text-amber-300/90 font-medium">
                  {selectedScenario.goal}
                </span>
              </span>
            </div>
          </div>

          {/* Attack Controls */}
          <div className="border border-gray-800/60 rounded-xl p-4">
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
                  className="w-full bg-gray-900/50 border border-gray-700/60 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-600 transition"
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
                className="inline-flex items-center gap-2 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-gray-800 disabled:text-gray-500 rounded-lg text-sm font-semibold transition"
              >
                {loading ? (
                  <>
                    <svg
                      className="w-4 h-4 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Running...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 010 1.972l-11.54 6.347a1.125 1.125 0 01-1.667-.986V5.653z"
                      />
                    </svg>
                    Run Simulation
                  </>
                )}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-950/30 border border-red-800/50 rounded-lg p-3 text-sm text-red-300 flex items-start gap-2">
              <svg
                className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                />
              </svg>
              {error}
            </div>
          )}

          {/* Vulnerable / Defended Mode Toggle */}
          {result && comparisonResult && (
            <div className="flex gap-1 bg-gray-900/50 rounded-xl p-1 border border-gray-800/60">
              <button
                onClick={() => setMode("vulnerable")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  mode === "vulnerable"
                    ? "bg-red-950/40 text-red-300 border border-red-800/50 shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"
                  />
                </svg>
                Vulnerable
              </button>
              <button
                onClick={() => setMode("defended")}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
                  mode === "defended"
                    ? "bg-emerald-950/40 text-emerald-300 border border-emerald-800/50 shadow-sm"
                    : "text-gray-500 hover:text-gray-300"
                }`}
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                  />
                </svg>
                Defended
              </button>
            </div>
          )}

          {/* Chat Interaction */}
          {activeResult ? (
            <div
              ref={chatRef}
              className="border border-gray-800/60 rounded-xl p-4 flex-1 min-h-[300px] max-h-[500px] overflow-y-auto"
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
          <div className="border border-gray-800/60 rounded-xl p-5">
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
            <div className="border border-emerald-800/40 rounded-xl p-5 bg-emerald-950/10">
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
            <div className="border border-gray-800/60 rounded-xl p-5">
              <SectionHeader
                title="Comparison"
                subtitle="Same technique, different security postures"
              />
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-red-500/60" />
                    <span className="text-gray-400">Vulnerable</span>
                  </div>
                  <span
                    className={`font-semibold text-xs px-2 py-0.5 rounded ${
                      result.verdict.attack_succeeded
                        ? "bg-red-900/40 text-red-300"
                        : "bg-emerald-900/40 text-emerald-300"
                    }`}
                  >
                    {result.verdict.attack_succeeded
                      ? "Compromised"
                      : "Held"}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500/60" />
                    <span className="text-gray-400">Defended</span>
                  </div>
                  <span
                    className={`font-semibold text-xs px-2 py-0.5 rounded ${
                      comparisonResult.verdict.attack_succeeded
                        ? "bg-red-900/40 text-red-300"
                        : "bg-emerald-900/40 text-emerald-300"
                    }`}
                  >
                    {comparisonResult.verdict.attack_succeeded
                      ? "Compromised"
                      : "Blocked"}
                  </span>
                </div>
                <div className="border-t border-gray-800/40 pt-3 mt-3">
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
      <footer className="border-t border-gray-800/60 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-[11px] text-gray-600">
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
