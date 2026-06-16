type HistoryItem = {
  id: string;
  createdAt: string;
  result: {
    application: {
      brand_name: string;
      type_of_product: string;
    };
  };
};

type Props = {
  history: HistoryItem[];
  onOpenItem: (item: HistoryItem) => void;
};

export function HistoryView({ history, onOpenItem }: Props) {
  return (
    <div className="results-panel">
      <h2>Previous Applications</h2>

      {history.length === 0 ? (
        <p>No previous applications yet.</p>
      ) : (
        <ul className="history-list">
          {history.map((item) => (
            <li key={item.id}>
              <button type="button" onClick={() => onOpenItem(item)}>
                {item.result.application.brand_name || "Untitled"} — {item.result.application.type_of_product || "Unknown"} — {new Date(item.createdAt).toLocaleString()}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}