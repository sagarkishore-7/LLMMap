"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CatalogTechnique {
  technique_id: string;
  family: string;
  name: string;
  tags: string[];
  has_explanation: boolean;
  scenarios: string[];
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

async function fetchTechniques(): Promise<CatalogTechnique[]> {
  const res = await fetch(`${API_BASE}/api/techniques`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function familyLabel(family: string): string {
  return family.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const FAMILY_COLORS: Record<string, string> = {
  instruction_manipulation: "emerald",
  indirect_prompt_injection_context_data: "blue",
  rag_specific_attack: "cyan",
  cognitive_control_bypass: "purple",
  social_systemic_attack: "amber",
};

function familyColor(family: string): string {
  return FAMILY_COLORS[family] || "gray";
}

function colorClasses(color: string): { badge: string; dot: string; ring: string } {
  const map: Record<string, { badge: string; dot: string; ring: string }> = {
    emerald: {
      badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      dot: "bg-emerald-400",
      ring: "border-emerald-500/30 bg-emerald-500/[0.03]",
    },
    blue: {
      badge: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      dot: "bg-blue-400",
      ring: "border-blue-500/30 bg-blue-500/[0.03]",
    },
    cyan: {
      badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
      dot: "bg-cyan-400",
      ring: "border-cyan-500/30 bg-cyan-500/[0.03]",
    },
    purple: {
      badge: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      dot: "bg-purple-400",
      ring: "border-purple-500/30 bg-purple-500/[0.03]",
    },
    amber: {
      badge: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      dot: "bg-amber-400",
      ring: "border-amber-500/30 bg-amber-500/[0.03]",
    },
    gray: {
      badge: "bg-white/5 text-gray-400 border-white/10",
      dot: "bg-gray-400",
      ring: "border-white/[0.06] bg-white/[0.01]",
    },
  };
  return map[color] || map.gray;
}

// ---------------------------------------------------------------------------
// Icons
// ---------------------------------------------------------------------------

function SearchIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
}

function CheckIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  );
}

function ShieldIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  );
}

function ArrowLeftIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function ChevronDownIcon({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
    </svg>
  );
}

function Spinner({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
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
    cyan: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
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

function TechniqueCard({
  technique,
  expanded,
  onToggle,
}: {
  technique: CatalogTechnique;
  expanded: boolean;
  onToggle: () => void;
}) {
  const color = familyColor(technique.family);
  const cc = colorClasses(color);

  return (
    <div
      className={`border rounded-xl transition-all ${
        expanded ? cc.ring : "border-white/[0.06] bg-white/[0.01] hover:border-white/[0.12]"
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full text-left px-5 py-4 flex items-start gap-3"
      >
        {/* Color dot */}
        <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${cc.dot}`} />

        <div className="flex-1 min-w-0">
          {/* Name row */}
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="font-medium text-gray-100 text-sm">
              {technique.name}
            </span>
            {technique.has_explanation && (
              <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                <CheckIcon className="w-3 h-3" />
                Explained
              </span>
            )}
          </div>

          {/* Family */}
          <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded-md border ${cc.badge}`}>
            {familyLabel(technique.family)}
          </span>
        </div>

        <ChevronDownIcon
          className={`w-4 h-4 text-gray-600 flex-shrink-0 mt-1 transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Expanded details */}
      {expanded && (
        <div className="px-5 pb-4 pt-0 border-t border-white/[0.04] mx-5 mt-0 pt-3">
          {/* ID */}
          <div className="mb-3">
            <span className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold">
              Technique ID
            </span>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              {technique.technique_id}
            </p>
          </div>

          {/* Tags */}
          {technique.tags.length > 0 && (
            <div className="mb-3">
              <span className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold">
                Tags
              </span>
              <div className="flex gap-1.5 flex-wrap mt-1">
                {technique.tags.map((tag) => (
                  <Badge key={tag} variant="gray">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Scenarios */}
          {technique.scenarios.length > 0 && (
            <div className="mb-1">
              <span className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold">
                Available in Scenarios
              </span>
              <div className="flex gap-1.5 flex-wrap mt-1">
                {technique.scenarios.map((s) => (
                  <Badge key={s} variant="green">
                    {s.replace(/_/g, " ")}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Explanation status */}
          <div className="mt-3 pt-3 border-t border-white/[0.04]">
            {technique.has_explanation ? (
              <p className="text-xs text-emerald-400/80 flex items-center gap-1.5">
                <CheckIcon className="w-3.5 h-3.5" />
                Curated explanation available &mdash; visible in the lab when you run this technique
              </p>
            ) : (
              <p className="text-xs text-gray-600">
                No curated explanation yet. The lab will show a generic description.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function TechniqueBrowserPage() {
  const [techniques, setTechniques] = useState<CatalogTechnique[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Fetch techniques
  useEffect(() => {
    fetchTechniques()
      .then(setTechniques)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Derive families list
  const families = useMemo(() => {
    const fams = new Map<string, number>();
    for (const t of techniques) {
      fams.set(t.family, (fams.get(t.family) || 0) + 1);
    }
    return Array.from(fams.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([family, count]) => ({ family, count }));
  }, [techniques]);

  // Filter
  const filtered = useMemo(() => {
    let list = techniques;
    if (selectedFamily) {
      list = list.filter((t) => t.family === selectedFamily);
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          t.technique_id.toLowerCase().includes(q) ||
          t.family.toLowerCase().includes(q)
      );
    }
    return list;
  }, [techniques, selectedFamily, search]);

  // Stats
  const explainedCount = techniques.filter((t) => t.has_explanation).length;

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0a] overflow-x-hidden">
      {/* Header */}
      <header className="border-b border-white/[0.06] px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              <span className="hidden sm:inline">Lab</span>
            </Link>
            <span className="text-gray-700">/</span>
            <div className="text-xl font-bold tracking-tight">
              <span className="text-emerald-400">Prompt</span>
              <span className="text-gray-100">Lab</span>
            </div>
            <SandboxBadge />
          </div>
          <span className="text-xs text-gray-600 hidden sm:block">
            Technique Browser
          </span>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-6 w-full">
          {/* Page header */}
          <section className="pt-12 pb-8">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
              <span className="text-white">Technique Catalog</span>
            </h1>
            <p className="text-gray-400 text-sm max-w-2xl leading-relaxed">
              Browse all {techniques.length || 227} attack techniques from the LLMMap
              prompt packs. Filter by family, search by name, and see which
              techniques have curated explanations.
            </p>

            {/* Stats bar */}
            {!loading && !error && (
              <div className="flex items-center gap-6 mt-5 text-xs text-gray-500">
                <span>
                  <span className="text-gray-200 font-semibold">{techniques.length}</span> techniques
                </span>
                <span>
                  <span className="text-gray-200 font-semibold">{families.length}</span> families
                </span>
                <span>
                  <span className="text-emerald-400 font-semibold">{explainedCount}</span> with curated explanations
                </span>
              </div>
            )}
          </section>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 mb-8 text-sm text-red-300">
              <p className="font-medium mb-1">Could not load techniques</p>
              <p className="text-red-400/80 text-xs">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading && !error && (
            <div className="border border-white/[0.06] rounded-xl p-16 text-center">
              <Spinner className="w-5 h-5 text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-500">Loading techniques...</p>
            </div>
          )}

          {/* Content */}
          {!loading && !error && (
            <div className="pb-16">
              {/* Search + family filter row */}
              <div className="flex flex-col sm:flex-row gap-3 mb-6 sticky top-0 z-10 bg-[#0a0a0a] py-3 -mx-6 px-6 border-b border-white/[0.04]">
                {/* Search */}
                <div className="relative flex-1">
                  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <input
                    type="text"
                    placeholder="Search techniques..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/[0.03] border border-white/[0.08] rounded-lg text-gray-200 placeholder-gray-600 focus:outline-none focus:border-emerald-500/40 focus:ring-1 focus:ring-emerald-500/20 transition"
                  />
                </div>

                {/* Family filter dropdown */}
                <div className="relative">
                  <select
                    value={selectedFamily || ""}
                    onChange={(e) =>
                      setSelectedFamily(e.target.value || null)
                    }
                    className="appearance-none pl-4 pr-10 py-2.5 text-sm bg-white/[0.03] border border-white/[0.08] rounded-lg text-gray-200 focus:outline-none focus:border-emerald-500/40 focus:ring-1 focus:ring-emerald-500/20 transition cursor-pointer min-w-[200px]"
                  >
                    <option value="">All families ({techniques.length})</option>
                    {families.map(({ family, count }) => (
                      <option key={family} value={family}>
                        {familyLabel(family)} ({count})
                      </option>
                    ))}
                  </select>
                  <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 pointer-events-none" />
                </div>
              </div>

              {/* Results count */}
              <div className="text-xs text-gray-600 mb-4">
                {filtered.length === techniques.length
                  ? `Showing all ${filtered.length} techniques`
                  : `${filtered.length} of ${techniques.length} techniques`}
                {selectedFamily && (
                  <button
                    onClick={() => setSelectedFamily(null)}
                    className="ml-2 text-emerald-400 hover:text-emerald-300 transition"
                  >
                    Clear filter
                  </button>
                )}
                {search && (
                  <button
                    onClick={() => setSearch("")}
                    className="ml-2 text-emerald-400 hover:text-emerald-300 transition"
                  >
                    Clear search
                  </button>
                )}
              </div>

              {/* Technique list */}
              {filtered.length === 0 ? (
                <div className="border border-white/[0.06] border-dashed rounded-xl p-12 text-center">
                  <SearchIcon className="w-8 h-8 text-gray-700 mx-auto mb-3" />
                  <p className="text-sm text-gray-500">No techniques match your filters.</p>
                </div>
              ) : (
                <div className="grid gap-2">
                  {filtered.map((t) => (
                    <TechniqueCard
                      key={t.technique_id}
                      technique={t}
                      expanded={expandedId === t.technique_id}
                      onToggle={() =>
                        setExpandedId(
                          expandedId === t.technique_id ? null : t.technique_id
                        )
                      }
                    />
                  ))}
                </div>
              )}
            </div>
          )}
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
