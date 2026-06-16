import type { ProcessResponse, SubmitResult } from "./types";

export async function processApplicationUrl(sourceUrl: string): Promise<ProcessResponse> {
  const response = await fetch("/process-url?include_images=true", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ source_url: sourceUrl })
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Processing failed");
  }

  return response.json();
}

export async function submitApplicationForm(formData: FormData): Promise<SubmitResult> {
  const response = await fetch("/submit", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Application submit failed");
  }

  return response.json();
}