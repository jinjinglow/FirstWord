import React from "react";
import ReactDOM from "react-dom/client";
import { AlertTriangle, CheckCircle2, Clock, Database, FileAudio, History, Loader2, Mic, MicOff, Pause, Play, RefreshCcw, RotateCw, Search, ShieldCheck, Square, Trash2 } from "lucide-react";
import clsx from "clsx";
import "./styles.css";

type UserMode = "SSSG" | "CARG";

type Summary = {
  case_overview: string;
  key_concerns: string[];
  observations: string[];
  reported_statements: string[];
  protective_factors: string[];
  risk_indicators: string[];
  recommended_follow_up: string[];
  uncertainty: string[];
};

type Recommendation = {
  label: string;
  risk_level: string;
  rationale: string;
  contributing_indicators: string[];
  uncertainty: string[];
  guidance_refs: string[];
  advisory_notice: string;
};

type CaseOut = {
  case_id: string;
  created_at: string;
  updated_at: string;
  user_mode: UserMode;
  latest_recommendation_label?: string | null;
  latest_risk_level?: string | null;
  latest_recommendation_at?: string | null;
  latest_case_update_id?: number | null;
};

type CaseUpdate = {
  id: number;
  created_at: string;
  user_mode: UserMode;
  summary: Summary;
  recommendation: Recommendation;
};

type ProcessResponse = {
  case_id: string;
  update: CaseUpdate;
};

type CaseDetail = CaseOut & {
  updates: CaseUpdate[];
};

declare global {
  interface Window {
    desktop?: { platform: string; apiBaseUrl: string };
  }
}

const apiBase = window.desktop?.apiBaseUrl ?? import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8766";
const singaporeDateFormatter = new Intl.DateTimeFormat("en-SG", {
  timeZone: "Asia/Singapore",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false
});

function formatSingaporeTime(value: string) {
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value);
  const date = new Date(hasTimezone ? value : `${value}+08:00`);
  if (Number.isNaN(date.getTime())) return value;
  return `${singaporeDateFormatter.format(date)} SGT`;
}

function App() {
  const [mode, setMode] = React.useState<UserMode | null>(null);
  const [cases, setCases] = React.useState<CaseOut[]>([]);
  const [selectedCaseId, setSelectedCaseId] = React.useState<string>("");
  const [selectedCaseDetail, setSelectedCaseDetail] = React.useState<CaseDetail | null>(null);
  const [selectedUpdateId, setSelectedUpdateId] = React.useState<number | null>(null);
  const [caseLoading, setCaseLoading] = React.useState(false);
  const [caseError, setCaseError] = React.useState("");
  const [latest, setLatest] = React.useState<ProcessResponse | null>(null);
  const [aiStatus, setAiStatus] = React.useState<string>("Checking local AI services...");

  const loadCases = React.useCallback(async (query = "") => {
    const params = new URLSearchParams({ limit: "100" });
    if (query) params.set("query", query);
    const response = await fetch(`${apiBase}/cases?${params.toString()}`);
    if (response.ok) setCases(await response.json());
  }, []);

  React.useEffect(() => {
    loadCases().catch(() => setCases([]));
    fetch(`${apiBase}/ai/health`)
      .then((res) => res.json())
      .then((data) => setAiStatus(data.message))
      .catch(() => setAiStatus("FastAPI or Ollama is not reachable yet."));
  }, [loadCases]);

  React.useEffect(() => {
    if (!selectedCaseId) {
      setSelectedCaseDetail(null);
      setSelectedUpdateId(null);
      setCaseError("");
      return;
    }

    let cancelled = false;
    setSelectedCaseDetail(null);
    setSelectedUpdateId(null);
    setCaseLoading(true);
    setCaseError("");
    fetch(`${apiBase}/cases/${selectedCaseId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Case not found.");
        return res.json();
      })
      .then((detail: CaseDetail) => {
        if (cancelled) return;
        if (detail.case_id !== selectedCaseId) {
          throw new Error("Loaded case did not match the selected Case ID.");
        }
        setSelectedCaseDetail(detail);
        setSelectedUpdateId((current) => {
          if (current && detail.updates.some((update) => update.id === current)) return current;
          return detail.updates[0]?.id ?? null;
        });
      })
      .catch((error: Error) => {
        if (cancelled) return;
        setSelectedCaseDetail(null);
        setSelectedUpdateId(null);
        setCaseError(error.message || "Could not load case.");
      })
      .finally(() => {
        if (!cancelled) setCaseLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedCaseId, latest]);

  if (!mode) return <ModeSelection onSelect={setMode} aiStatus={aiStatus} />;

  const selectedUpdate = selectedCaseDetail?.updates.find((update) => update.id === selectedUpdateId) ?? selectedCaseDetail?.updates[0] ?? null;

  return (
    <div className="min-h-screen bg-[#f7f8fa] text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-semibold">FirstWord</h1>
          </div>
          <div className="flex items-center gap-3">
            <ModeBadge mode={mode} />
            <button className="btn-secondary" onClick={() => setMode(null)}>Switch mode</button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-[320px_1fr] gap-6 px-6 py-6">
        <aside className="space-y-4">
          <StatusPanel aiStatus={aiStatus} />
          <CaseSearch
            cases={cases}
            selectedCaseId={selectedCaseId}
            onSearch={loadCases}
            onRefresh={() => loadCases()}
            onSelect={(caseId) => {
              setLatest(null);
              setSelectedUpdateId(null);
              setSelectedCaseId(caseId);
            }}
            onNew={() => {
              setLatest(null);
              setSelectedCaseId("");
              setSelectedCaseDetail(null);
              setSelectedUpdateId(null);
            }}
          />
        </aside>

        <section className="space-y-5">
          <RecorderPanel
            mode={mode}
            selectedCaseId={selectedCaseId}
            onProcessed={(result) => {
              setLatest(result);
              setSelectedCaseId(result.case_id);
              setSelectedUpdateId(result.update.id);
              loadCases().catch(() => undefined);
            }}
          />
          {caseLoading ? (
            <LoadingReview />
          ) : caseError ? (
            <CaseLoadError message={caseError} />
          ) : selectedCaseId && selectedUpdate ? (
            <ReviewPanels caseId={selectedCaseId} update={selectedUpdate} />
          ) : (
            <EmptyReview />
          )}
          <CaseTimeline
            selectedCaseId={selectedCaseId}
            detail={selectedCaseDetail}
            selectedUpdateId={selectedUpdateId}
            onSelectUpdate={setSelectedUpdateId}
          />
        </section>
      </main>
    </div>
  );
}

function ModeSelection({ onSelect, aiStatus }: { onSelect: (mode: UserMode) => void; aiStatus: string }) {
  return (
    <main className="min-h-screen bg-[#f7f8fa] px-6 py-10 text-ink">
      <section className="mx-auto max-w-5xl">
        <div className="mb-8">
          <p className="text-sm font-medium uppercase tracking-wide text-brand">Session mode</p>
          <h1 className="mt-2 text-3xl font-semibold">Select the user pathway for this session</h1>
          <p className="mt-3 max-w-3xl text-base text-muted">
            The mode controls how recommendation support is worded. It does not make final decisions, confirm abuse, or replace organisational procedures.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <button className="choice-card text-left" onClick={() => onSelect("SSSG")}>
            <ShieldCheck className="h-8 w-8 text-action" />
            <h2 className="mt-4 text-xl font-semibold">SSSG User</h2>
            <p className="mt-2 text-sm text-muted">For teachers, healthcare workers, and social workers who regularly encounter children and need structured screening support.</p>
            <p className="mt-4 text-sm font-medium text-brand">Supports whether to consult a trained CARG user.</p>
          </button>
          <button className="choice-card text-left" onClick={() => onSelect("CARG")}>
            <Database className="h-8 w-8 text-action" />
            <h2 className="mt-4 text-xl font-semibold">CARG User</h2>
            <p className="mt-2 text-sm text-muted">For designated child-protection personnel trained to use CARG within their organisation.</p>
            <p className="mt-4 text-sm font-medium text-brand">Supports review of whether to report or take alternative action.</p>
          </button>
        </div>

        <div className="mt-6 rounded border border-line bg-white p-4 text-sm text-muted">
          <strong className="text-ink">Local AI status:</strong> {aiStatus}
        </div>
      </section>
    </main>
  );
}

function RecorderPanel({ mode, selectedCaseId, onProcessed }: { mode: UserMode; selectedCaseId: string; onProcessed: (result: ProcessResponse) => void }) {
  const [permission, setPermission] = React.useState<"idle" | "ready" | "denied">("idle");
  const [status, setStatus] = React.useState<"idle" | "recording" | "paused" | "stopped" | "processing">("idle");
  const [elapsed, setElapsed] = React.useState(0);
  const [audioBlob, setAudioBlob] = React.useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = React.useState<string>("");
  const [error, setError] = React.useState<string>("");
  const recorderRef = React.useRef<MediaRecorder | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const chunksRef = React.useRef<BlobPart[]>([]);

  React.useEffect(() => {
    let timer: number | undefined;
    if (status === "recording") {
      timer = window.setInterval(() => setElapsed((value) => value + 1), 1000);
    }
    return () => window.clearInterval(timer);
  }, [status]);

  React.useEffect(() => () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  async function start() {
    setError("");
    setAudioBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl("");
    chunksRef.current = [];
    setElapsed(0);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      streamRef.current = stream;
      setPermission("ready");
      const candidates = ["audio/wav", "audio/webm;codecs=opus", "audio/webm"];
      const mimeType = candidates.find((item) => MediaRecorder.isTypeSupported(item)) ?? "";
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType || "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start(30_000);
      setStatus("recording");
    } catch {
      setPermission("denied");
      setError("Microphone access was not granted. Check Windows and Electron microphone permissions.");
    }
  }

  function pause() {
    recorderRef.current?.pause();
    setStatus("paused");
  }

  function resume() {
    recorderRef.current?.resume();
    setStatus("recording");
  }

  function stop() {
    recorderRef.current?.stop();
    setStatus("stopped");
  }

  function discard() {
    setAudioBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl("");
    setStatus("idle");
    setElapsed(0);
  }

  async function process() {
    if (!audioBlob) return;
    setStatus("processing");
    setError("");
    const form = new FormData();
    form.append("user_mode", mode);
    if (selectedCaseId) form.append("case_id", selectedCaseId);
    const extension = audioBlob.type.includes("wav") ? "wav" : "webm";
    form.append("audio", audioBlob, `recording.${extension}`);

    const response = await fetch(`${apiBase}/process-audio`, { method: "POST", body: form });
    if (!response.ok) {
      const detail = await response.json().catch(() => ({ detail: "Processing failed." }));
      setError(detail.detail ?? "Processing failed.");
      setStatus("stopped");
      return;
    }
    onProcessed(await response.json());
    discard();
  }

  return (
    <section className="panel">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Audio Recording</h2>
          <p className="mt-1 text-sm text-muted">Temporary local recording for transcription, summary, and recommendation support.</p>
        </div>
        <RecordingStatus status={status} permission={permission} elapsed={elapsed} />
      </div>

      <div className="mt-4 rounded border border-caution/30 bg-[#fff8ed] p-3 text-sm text-[#70410f]">
        Confirm consent and comply with organisational recording policies before starting.
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        {status === "idle" && <IconButton icon={Mic} label="Start recording" onClick={start} primary />}
        {status === "recording" && <IconButton icon={Pause} label="Pause" onClick={pause} />}
        {status === "paused" && <IconButton icon={Play} label="Resume" onClick={resume} />}
        {(status === "recording" || status === "paused") && <IconButton icon={Square} label="Stop" onClick={stop} danger />}
        {status === "stopped" && <IconButton icon={RefreshCcw} label="Re-record" onClick={start} />}
        {status === "stopped" && <IconButton icon={Trash2} label="Discard" onClick={discard} />}
        {status === "stopped" && <IconButton icon={FileAudio} label="Process recording" onClick={process} primary />}
        {status === "processing" && <span className="inline-flex items-center gap-2 text-sm font-medium text-brand"><Loader2 className="h-4 w-4 animate-spin" /> Processing locally</span>}
      </div>

      {audioUrl && (
        <div className="mt-5">
          <audio className="w-full" controls src={audioUrl} />
        </div>
      )}
      {error && <div className="mt-4 rounded border border-danger/30 bg-[#fff1f0] p-3 text-sm text-danger">{error}</div>}
    </section>
  );
}

function CaseSearch({ cases, selectedCaseId, onSearch, onRefresh, onSelect, onNew }: { cases: CaseOut[]; selectedCaseId: string; onSearch: (query?: string) => void; onRefresh: () => void; onSelect: (caseId: string) => void; onNew: () => void }) {
  const [query, setQuery] = React.useState("");
  return (
    <section className="panel">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">All Cases</h2>
          <p className="text-xs text-muted">{cases.length} shown</p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary" onClick={onRefresh} title="Refresh cases"><RotateCw className="h-4 w-4" /></button>
          <button className="btn-secondary" onClick={onNew}>New</button>
        </div>
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted" />
        <input
          className="input pl-9"
          placeholder="Search Case ID"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            onSearch(event.target.value);
          }}
        />
      </div>
      <div className="mt-4 space-y-2">
        {cases.length === 0 && <p className="text-sm text-muted">{query ? "No matching cases found." : "No cases yet. Processing a recording can create one."}</p>}
        {cases.map((item) => (
          <button key={item.case_id} className={clsx("case-row", selectedCaseId === item.case_id && "case-row-active")} onClick={() => onSelect(item.case_id)}>
            <span className="font-medium">{item.case_id}</span>
            <span className={clsx("mt-1 text-xs font-medium", decisionTextClass(item.latest_risk_level))}>
              {item.latest_recommendation_label ?? "No current recommendation"}
            </span>
            <span className="text-xs text-muted">{formatSingaporeTime(item.updated_at)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function ReviewPanels({ caseId, update }: { caseId: string; update: CaseUpdate }) {
  return (
    <section className="grid gap-5 lg:grid-cols-2">
      <SummaryPanel summary={update.summary} caseId={caseId} createdAt={update.created_at} />
      <RecommendationPanel recommendation={update.recommendation} />
    </section>
  );
}

function SummaryPanel({ summary, caseId, createdAt }: { summary: Summary; caseId: string; createdAt: string }) {
  return (
    <article className="panel">
      <h2 className="text-xl font-semibold">Structured Summary</h2>
      <p className="mt-1 text-sm text-muted">{caseId} - {formatSingaporeTime(createdAt)}</p>
      <div className="mt-4 space-y-4">
        <Section title="Case Overview" text={summary.case_overview} />
        <Section title="Key Concerns" items={summary.key_concerns} />
        <Section title="Observations" items={summary.observations} />
        <Section title="Reported Statements" items={summary.reported_statements} />
        <Section title="Protective Factors" items={summary.protective_factors} />
        <Section title="Risk Indicators" items={summary.risk_indicators} tone="risk" />
        <Section title="Uncertainty" items={summary.uncertainty} tone="uncertain" />
        <Section title="Recommended Follow-Up" items={summary.recommended_follow_up} />
      </div>
    </article>
  );
}

function RecommendationPanel({ recommendation }: { recommendation: Recommendation }) {
  const tone = recommendation.risk_level.startsWith("Serious") ? "danger" : recommendation.risk_level.startsWith("Moderate") ? "caution" : "action";
  return (
    <article className="panel">
      <div className={clsx("recommendation-band", `tone-${tone}`)}>
        <p className="text-sm font-medium">{recommendation.risk_level}</p>
        <h2 className="mt-1 text-xl font-semibold">{recommendation.label}</h2>
      </div>
      <p className="mt-4 text-sm leading-6 text-ink">{recommendation.rationale}</p>
      <div className="mt-4 rounded border border-line bg-[#f7f8fa] p-3 text-sm font-medium text-ink">{recommendation.advisory_notice}</div>
      <div className="mt-4 space-y-4">
        <Section title="Contributing Indicators" items={recommendation.contributing_indicators} tone="risk" />
        <Section title="Uncertainty" items={recommendation.uncertainty} tone="uncertain" />
        <Section title="Guidance References" items={recommendation.guidance_refs} />
      </div>
    </article>
  );
}

function CaseTimeline({ selectedCaseId, detail, selectedUpdateId, onSelectUpdate }: { selectedCaseId: string; detail: CaseDetail | null; selectedUpdateId: number | null; onSelectUpdate: (updateId: number) => void }) {
  const isSelectedCaseDetail = Boolean(detail && detail.case_id === selectedCaseId);
  const updates = isSelectedCaseDetail ? detail?.updates ?? [] : [];
  return (
    <section className="panel">
      <div className="flex items-center gap-2">
        <History className="h-5 w-5 text-brand" />
        <h2 className="text-xl font-semibold">Outcome History</h2>
      </div>
      {selectedCaseId && <p className="mt-1 text-sm text-muted">{selectedCaseId}</p>}
      {!selectedCaseId && <p className="mt-3 text-sm text-muted">Select an existing case or process a recording to create a new case.</p>}
      {isSelectedCaseDetail && detail?.latest_recommendation_label && (
        <div className={clsx("mt-4 rounded border p-4", decisionBandClass(detail.latest_risk_level))}>
          <p className="text-xs font-medium uppercase tracking-wide">Current case recommendation</p>
          <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
            <p className="text-base font-semibold">{detail.latest_recommendation_label}</p>
            {detail.latest_recommendation_at && <span className="text-xs">{formatSingaporeTime(detail.latest_recommendation_at)}</span>}
          </div>
          {detail.latest_risk_level && <p className="mt-1 text-sm">{detail.latest_risk_level}</p>}
        </div>
      )}
      {isSelectedCaseDetail && updates.length === 0 && <p className="mt-3 text-sm text-muted">No saved outcomes found for this case.</p>}
      <div className="mt-4 space-y-3">
        {updates.map((update) => (
          <button
            key={update.id}
            className={clsx("timeline-row w-full text-left", selectedUpdateId === update.id && "border-brand bg-[#edf7f6]")}
            onClick={() => onSelectUpdate(update.id)}
          >
            <div>
              <p className="font-medium">{update.recommendation.label}</p>
              <p className="text-sm text-muted">{update.summary.case_overview || "No overview available."}</p>
            </div>
            <span className="text-xs text-muted">{formatSingaporeTime(update.created_at)}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

function StatusPanel({ aiStatus }: { aiStatus: string }) {
  return (
    <section className="panel">
      <div className="flex items-start gap-3">
        <CheckCircle2 className="mt-0.5 h-5 w-5 text-action" />
        <div>
          <h2 className="font-semibold">Offline Runtime</h2>
          <p className="mt-1 text-sm text-muted">{aiStatus}</p>
        </div>
      </div>
    </section>
  );
}

function EmptyReview() {
  return (
    <section className="panel border-dashed">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-5 w-5 text-caution" />
        <p className="text-sm text-muted">No processed summary in this session yet. Record, review playback, and process locally to append a case update.</p>
      </div>
    </section>
  );
}

function LoadingReview() {
  return (
    <section className="panel">
      <span className="inline-flex items-center gap-2 text-sm font-medium text-brand"><Loader2 className="h-4 w-4 animate-spin" /> Loading case details</span>
    </section>
  );
}

function CaseLoadError({ message }: { message: string }) {
  return (
    <section className="panel border-danger/30 bg-[#fff1f0]">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-5 w-5 text-danger" />
        <p className="text-sm text-danger">{message}</p>
      </div>
    </section>
  );
}

function RecordingStatus({ status, permission, elapsed }: { status: string; permission: string; elapsed: number }) {
  const minutes = Math.floor(elapsed / 60).toString().padStart(2, "0");
  const seconds = (elapsed % 60).toString().padStart(2, "0");
  return (
    <div className="grid min-w-48 gap-2 text-sm">
      <span className="inline-flex items-center justify-end gap-2"><Clock className="h-4 w-4 text-muted" /> {minutes}:{seconds}</span>
      <span className="inline-flex items-center justify-end gap-2">
        {permission === "denied" ? <MicOff className="h-4 w-4 text-danger" /> : <Mic className="h-4 w-4 text-action" />}
        {status}
      </span>
    </div>
  );
}

function ModeBadge({ mode }: { mode: UserMode }) {
  return <span className="rounded border border-line bg-[#f7f8fa] px-3 py-1 text-sm font-medium">{mode} session</span>;
}

function IconButton({ icon: Icon, label, onClick, primary, danger }: { icon: React.ElementType; label: string; onClick: () => void; primary?: boolean; danger?: boolean }) {
  return (
    <button className={clsx("icon-btn", primary && "icon-btn-primary", danger && "icon-btn-danger")} onClick={onClick} title={label}>
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );
}

function Section({ title, text, items, tone }: { title: string; text?: string; items?: string[]; tone?: "risk" | "uncertain" }) {
  const visible = items?.filter(Boolean) ?? [];
  return (
    <div>
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {text && <p className="mt-1 text-sm leading-6 text-muted">{text}</p>}
      {visible.length > 0 ? (
        <ul className="mt-2 space-y-2">
          {visible.map((item, index) => (
            <li key={`${title}-${index}`} className={clsx("summary-item", tone === "risk" && "summary-risk", tone === "uncertain" && "summary-uncertain")}>{item}</li>
          ))}
        </ul>
      ) : !text ? (
        <p className="mt-1 text-sm text-muted">No information recorded.</p>
      ) : null}
    </div>
  );
}

function decisionTextClass(riskLevel?: string | null) {
  if (riskLevel?.startsWith("Serious")) return "text-danger";
  if (riskLevel?.startsWith("Moderate")) return "text-caution";
  if (riskLevel) return "text-action";
  return "text-muted";
}

function decisionBandClass(riskLevel?: string | null) {
  if (riskLevel?.startsWith("Serious")) return "border-danger/30 bg-[#fff1f0] text-danger";
  if (riskLevel?.startsWith("Moderate")) return "border-caution/30 bg-[#fff8ed] text-caution";
  return "border-action/30 bg-[#edf7f6] text-action";
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
