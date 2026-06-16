import { useMemo, useState } from "react";
import { ColaForm } from "./components/ColaForm";
import { ResultsView } from "./components/ResultsView";
import { HistoryView } from "./components/HistoryView";
import { Toolbar } from "./components/Toolbar";
import type { SubmitResult } from "./types";

type ViewMode = "form" | "results" | "history";

type SavedSubmission = {
  id: string;
  createdAt: string;
  result: SubmitResult;
};

const STORAGE_KEY = "ttb-submission-history";

function loadHistory(): SavedSubmission[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

function saveHistory(history: SavedSubmission[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export default function App() {
  const [view, setView] = useState<ViewMode>("form");
  const [latestResult, setLatestResult] = useState<SubmitResult | null>(null);
  const [history, setHistory] = useState<SavedSubmission[]>(() => loadHistory());

  const sortedHistory = useMemo(
    () => [...history].sort((a, b) => b.createdAt.localeCompare(a.createdAt)),
    [history]
  );

  const handleSubmitted = (result: SubmitResult) => {
    const entry: SavedSubmission = {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      result
    };

    const nextHistory = [entry, ...history];
    setLatestResult(result);
    setHistory(nextHistory);
    saveHistory(nextHistory);
    setView("results");
  };

  const handleOpenHistoryItem = (item: any) => {
    setLatestResult(item.result);
    setView("results");
  };

  const handleNewApplication = () => {
    setLatestResult(null);
    setView("form");
  };

  return (
    <div className="page-shell">
      <Toolbar
        onNewApplication={handleNewApplication}
        onViewHistory={() => setView("history")}
        onViewResults={() => latestResult && setView("results")}
        hasResults={!!latestResult}
      />

      <div className="page">
        {view === "form" && <ColaForm application={null} onSubmitted={handleSubmitted} />}

        {view === "results" && latestResult && <ResultsView result={latestResult} />}

        {view === "history" && (
          <HistoryView history={sortedHistory} onOpenItem={handleOpenHistoryItem} />
        )}
      </div>
    </div>
  );
}