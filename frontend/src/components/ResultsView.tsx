import type { SubmitResult } from "../types";

type Props = {
  result: SubmitResult;
};

type PerImageItem = {
  file_name: string;
  image_type: string;
  result: {
    category: string;
    checks: Record<string, { status?: string; region_id?: string | null }>;
    combined_ocr_text?: string;
  };
};

function prettyLabel(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusClass(status?: string) {
  const normalized = (status || "").toLowerCase();
  if (normalized === "pass" || normalized === "present" || normalized === "match") {
    return "status-pill status-good";
  }
  if (normalized === "warning" || normalized === "optional_missing" || normalized === "not_checked") {
    return "status-pill status-warn";
  }
  return "status-pill status-bad";
}

function resolveAssetUrl(src?: string) {
  if (!src) return "";
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  if (src.startsWith("/static/")) return `http://127.0.0.1:8000${src}`;
  return src;
}

function groupPerImageResults(perImage: PerImageItem[]) {
  const grouped = new Map<
    string,
    {
      file_name: string;
      image_type: string;
      categoryResult?: PerImageItem["result"];
      warningResult?: PerImageItem["result"];
    }
  >();

  for (const item of perImage) {
    const existing = grouped.get(item.file_name) ?? {
      file_name: item.file_name,
      image_type: item.image_type
    };

    if (item.result.category === "warning") {
      existing.warningResult = item.result;
    } else {
      existing.categoryResult = item.result;
    }

    grouped.set(item.file_name, existing);
  }

  return Array.from(grouped.values());
}

export function ResultsView({ result }: Props) {
  const validation = result.validation;

  const labelRules = result.label_rule_results as
    | {
        summary?: {
          category?: string;
          overall_status?: string;
          summary?: Record<string, string>;
        };
        per_image?: PerImageItem[];
      }
    | undefined;

  const labelSummary = labelRules?.summary;
  const perImage = labelRules?.per_image ?? [];
  const summaryChecks = labelSummary?.summary ?? {};
  const groupedImages = groupPerImageResults(perImage);

  return (
    <div className="results-panel">
      <div className="results-header">
        <div>
          <h1 className="results-title">Results</h1>
          <p className="results-subtitle">
            {result.application.brand_name || "Untitled"} •{" "}
            {result.application.type_of_product || "Unknown Product Type"}
          </p>
        </div>
      </div>

      <div className="results-card-grid">
        <div className="result-stat-card">
          <div className="result-stat-label">Application Validation</div>
          <div className="result-stat-help">
            Compares application form values against extracted OCR text.
          </div>
          <div className={statusClass(validation?.overall_status)}>
            {validation?.overall_status || "unknown"}
          </div>
        </div>

        <div className="result-stat-card">
          <div className="result-stat-label">Label Compliance Checks</div>
          <div className="result-stat-help">
            Checks label content requirements like class, net contents, alcohol content, and warning.
          </div>
          <div className={statusClass(labelSummary?.overall_status)}>
            {labelSummary?.overall_status || "unknown"}
          </div>
        </div>

        <div className="result-stat-card">
          <div className="result-stat-label">Processed Images</div>
          <div className="result-stat-help">
            Number of label images included in this result.
          </div>
          <div className="result-stat-value">{result.label_images?.length ?? 0}</div>
        </div>

        <div className="result-stat-card">
          <div className="result-stat-label">Government Warning</div>
          <div className="result-stat-help">
            Whether any submitted label image contains the required warning statement.
          </div>
          <div className={statusClass(summaryChecks.government_warning)}>
            {summaryChecks.government_warning || "unknown"}
          </div>
        </div>
      </div>

      <section className="results-section">
        <h2>Application Summary</h2>
        <div className="results-summary-grid">
          <div><strong>Brand Name:</strong> {result.application.brand_name || "—"}</div>
          <div><strong>Product Type:</strong> {result.application.type_of_product || "—"}</div>
          <div><strong>Alcohol Content:</strong> {result.application.alcohol_content || "—"}</div>
          <div><strong>Net Contents:</strong> {result.application.net_contents || "—"}</div>
          <div><strong>Name / Address:</strong> {result.application.name_and_address || "—"}</div>
        </div>
      </section>

      <section className="results-section">
        <h2>Label Compliance Summary</h2>
        <p className="results-section-help">
          These checks are based on what was detected on the label images themselves.
        </p>
        <div className="result-badge-grid">
          {Object.entries(summaryChecks).map(([key, value]) => (
            <div className="result-badge-card" key={key}>
              <div className="result-badge-label">{prettyLabel(key)}</div>
              <div className={statusClass(value)}>{value}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="results-section">
        <h2>Application Validation Checks</h2>
        <p className="results-section-help">
          These checks compare fields from the application form to the OCR text extracted from the uploaded labels.
        </p>
        <div className="results-check-list">
          {validation?.checks?.map((check, index) => (
            <div className="results-check-row" key={`${check.field}-${index}`}>
              <div className="results-check-main">
                <div className="results-check-field">{prettyLabel(check.field)}</div>
                <div className="results-check-message">{check.message}</div>
              </div>
              <div className={statusClass(check.status)}>{check.status}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="results-section">
        <h2>Per Image Details</h2>
        <p className="results-section-help">
          Review each image individually to see extracted text and label-specific checks.
        </p>
        <div className="results-accordion-list">
          {groupedImages.map((item) => {
            const image = result.label_images?.find((img) => img.file_name === item.file_name);

            return (
              <details className="results-accordion" key={item.file_name}>
                <summary className="results-accordion-summary">
                  <div>
                    <strong>{item.file_name}</strong>
                  </div>
                </summary>

                <div className="results-accordion-body">
                  {image?.src && (
                    <img
                      className="results-image-preview"
                      src={resolveAssetUrl(image.src)}
                      alt={item.file_name}
                    />
                  )}

                  {item.categoryResult && (
                    <div>
                      <h3 className="results-subsection-title">
                        Label Content Checks: {prettyLabel(item.categoryResult.category)}
                      </h3>
                      <div className="result-badge-grid">
                        {Object.entries(item.categoryResult.checks || {}).map(([key, value]) => (
                          <div className="result-badge-card" key={key}>
                            <div className="result-badge-label">{prettyLabel(key)}</div>
                            <div className={statusClass(value?.status)}>
                              {value?.status || "unknown"}
                            </div>
                          </div>
                        ))}
                      </div>

                      {item.categoryResult.combined_ocr_text && (
                        <div className="results-ocr-block">
                          <div className="results-ocr-label">OCR Text</div>
                          <pre>{item.categoryResult.combined_ocr_text}</pre>
                        </div>
                      )}
                    </div>
                  )}

                  {item.warningResult && (
                    <div>
                      <h3 className="results-subsection-title">Government Warning Check</h3>
                      <div className="result-badge-grid">
                        {Object.entries(item.warningResult.checks || {}).map(([key, value]) => (
                          <div className="result-badge-card" key={key}>
                            <div className="result-badge-label">{prettyLabel(key)}</div>
                            <div className={statusClass(value?.status)}>
                              {value?.status || "unknown"}
                            </div>
                          </div>
                        ))}
                      </div>

                      {item.warningResult.combined_ocr_text && (
                        <div className="results-ocr-block">
                          <div className="results-ocr-label">OCR Text</div>
                          <pre>{item.warningResult.combined_ocr_text}</pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </details>
            );
          })}
        </div>
      </section>
    </div>
  );
}