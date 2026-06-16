type Props = {
  onFileSelected: (file: File) => void;
  loading: boolean;
};

export function UploadPanel({ onFileSelected, loading }: Props) {
  return (
    <div className="upload-panel">
      <label className="upload-label">
        <span>Upload COLA HTML</span>
        <input
          type="file"
          accept=".html,text/html"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFileSelected(file);
          }}
          disabled={loading}
        />
      </label>
    </div>
  );
}