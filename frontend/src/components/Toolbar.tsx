type Props = {
  onNewApplication: () => void;
  onViewHistory: () => void;
  onViewResults: () => void;
  hasResults: boolean;
};

export function Toolbar({ onNewApplication, onViewHistory, onViewResults, hasResults }: Props) {
  return (
    <div className="toolbar">
      <div className="toolbar-actions">
        <button type="button" onClick={onNewApplication}>New Application</button>
        <button type="button" onClick={onViewHistory}>Previous Applications</button>
        <button type="button" onClick={onViewResults} disabled={!hasResults}>Latest Results</button>
      </div>

      <div className="toolbar-title">TTB-ALC-LBL-PROCESSOR</div>
    </div>
  );
}