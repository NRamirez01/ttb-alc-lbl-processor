import { useEffect, useRef, useState } from "react";
import { processApplicationUrl, submitApplicationForm } from "../api";
import type { ApplicationData, SubmitResult } from "../types";

type Props = {
  application: ApplicationData | null;
  onSubmitted: (result: SubmitResult) => void;
};

type LabelPreview = {
  id: string;
  url: string;
  name: string;
  file: File | null;
};

function v(value?: string) {
  return value?.trim() || "";
}

function checked(actual: string | undefined, expected: string) {
  return (actual || "").toLowerCase().includes(expected.toLowerCase());
}

export function ColaForm({ application, onSubmitted }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState("");
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [labelPreviews, setLabelPreviews] = useState<LabelPreview[]>([]);
  const [applicationUrl, setApplicationUrl] = useState("");

  const [formApplication, setFormApplication] = useState<ApplicationData | null>(application);
  const [processingHtml, setProcessingHtml] = useState(false);
  const [htmlError, setHtmlError] = useState("");

  const a = formApplication;
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setFormApplication(application);
  }, [application]);

  useEffect(() => {
    return () => {
      labelPreviews.forEach((preview) => {
        if (preview.file) {
          URL.revokeObjectURL(preview.url);
        }
      });
    };
  }, [labelPreviews]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setHasSubmitted(true);
    setSubmitting(true);
    setSubmitError("");
    setSubmitSuccess("");

    try {
      const formData = new FormData(event.currentTarget);
      formData.delete("label_images");

      labelPreviews.forEach((preview) => {
        if (preview.file) {
          formData.append("label_images", preview.file);
        }
      });

      const remoteImageUrls = labelPreviews
        .filter((preview) => !preview.file)
        .map((preview) => preview.url);

      formData.append("remote_image_urls", JSON.stringify(remoteImageUrls));

      const result = await submitApplicationForm(formData);

      setSubmitSuccess("Application submitted.");
      onSubmitted(result);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplicationLoadFromUrl = async () => {
    if (!applicationUrl.trim()) return;

    setProcessingHtml(true);
    setHtmlError("");
    setSubmitSuccess("");
    setSubmitError("");
    setHasSubmitted(false);

    try {
      const result = await processApplicationUrl(applicationUrl.trim());

      setFormApplication({
        ...result.application,
        plant_registry_basic_permit_brewers_no:
          (result.application.plant_registry_basic_permit_brewers_no ?? "")
            .split(/\s+/)
            .filter(Boolean)
            .join("\n")
      });

      const remotePreviews = (result.images ?? []).map((image, index) => ({
        id: `remote-${index}-${image.file_name || "image"}`,
        url: image.src,
        name: `label-${index + 1}`,
        file: null
      }));

      setLabelPreviews(remotePreviews);
    } catch (err) {
      setHtmlError(err instanceof Error ? err.message : "Application load failed");
    } finally {
      setProcessingHtml(false);
    }
  };

  const handleOpenFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleLabelImagesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) return;

    const nextPreviews = files.map((file) => ({
      file,
      id: `${file.name}-${file.size}-${file.lastModified}-${crypto.randomUUID()}`,
      url: URL.createObjectURL(file),
      name: file.name
    }));

    setLabelPreviews((current) => [...current, ...nextPreviews]);
    event.target.value = "";
  };

  const handleRemoveImage = (id: string) => {
    setLabelPreviews((current) => {
      const preview = current.find((item) => item.id === id);
      if (preview && preview.file) {
        URL.revokeObjectURL(preview.url);
      }
      return current.filter((item) => item.id !== id);
    });
  };

  return (
    <form className="ttb-form" onSubmit={handleSubmit}>
      <div className="html-upload-test-panel">
        <div className="part-title">UPLOAD APPLICATION</div>
        <div className="html-upload-test-inner">
          <input
            type="text"
            className="field-input application-url-input"
            placeholder="Paste TTB application URL"
            value={applicationUrl}
            onChange={(e) => setApplicationUrl(e.target.value)}
          />

          <button
            type="button"
            className="upload-images-dropzone"
            onClick={handleApplicationLoadFromUrl}
            disabled={processingHtml || !applicationUrl.trim()}
          >
            {processingHtml ? "loading application..." : "load application"}
          </button>

          {htmlError && <div className="error">{htmlError}</div>}
        </div>
      </div>

      <div className="ttb-topline" />

      <div className="ttb-header-grid">
        <div className="ttb-use-only">
          <div className="section-cap">FOR TTB USE ONLY</div>

          <div className="field-box ttb-id-box">
            <div className="field-label">TTB ID</div>
            <div className="field-value grey-fill ttb-readonly-box">{v(a?.ttb_id)}</div>
          </div>
          <div className="mini-row three top-meta-row">
            <div className="field-box">
              <div className="field-label">
                1. REP. ID. NO. <span className="inline-italic">(If any)</span>
              </div>
              <input
                className="field-input"
                name="rep_id_no"
                value={a?.rep_id_no ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    rep_id_no: e.target.value
                  }))
                }
              />
            </div>
            <div className="field-box small-center grey-box">
              <div className="field-label">CT</div>
              <div className="field-value grey-fill">{v(a?.ct)}</div>
            </div>
            <div className="field-box small-center grey-box">
              <div className="field-label">OR</div>
              <div className="field-value grey-fill">{v(a?.or_value)}</div>
            </div>
          </div>
        </div>

        <div className="ttb-title-block">
          <div className="dept">DEPARTMENT OF THE TREASURY</div>
          <div className="bureau">ALCOHOL AND TOBACCO TAX AND TRADE BUREAU</div>
          <div className="title">
            APPLICATION FOR AND CERTIFICATION/EXEMPTION OF
            <br />
            LABEL/BOTTLE APPROVAL
          </div>
        </div>
      </div>

      <div className="part-title">PART I - APPLICATION</div>

      <div className="part1-grid">
        <div className="left-col">
          <div className="mini-row two">
            <div className="field-box">
              <div className="field-label">2. PLANT REGISTRY/BASIC PERMIT/BREWER'S NO. (Required)</div>
              <textarea
                className="field-textarea plant-registry-textarea"
                name="plant_registry_basic_permit_brewers_no"
                value={a?.plant_registry_basic_permit_brewers_no ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    plant_registry_basic_permit_brewers_no: e.target.value
                  }))
                }
              />
            </div>

            <div className="field-box">
              <div className="field-label">3. SOURCE OF PRODUCT (Required)</div>
              <div className="checkbox-group">
                <label>
                  <input
                    type="radio"
                    name="source_of_product"
                    value="Domestic"
                    checked={checked(a?.source_of_product, "Domestic")}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        source_of_product: e.target.value
                      }))
                    }
                  />
                  Domestic
                </label>
                <label>
                  <input
                    type="radio"
                    name="source_of_product"
                    value="Imported"
                    checked={checked(a?.source_of_product, "Imported")}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        source_of_product: e.target.value
                      }))
                    }
                  />
                  Imported
                </label>
              </div>
            </div>
          </div>

          <div className="mini-row two serial-product-row">
            <div className="field-box serial-box">
              <div className="field-label">
                4. SERIAL NUMBER <span className="inline-italic">(Required)</span>
              </div>

              <div className="serial-layout">
                <div className="serial-year-box">YEAR</div>
                <div className="serial-top-filler" />

                <div className="serial-cell serial-year-cell">
                  <input
                    className="serial-input"
                    name="serial_year_1"
                    value={a?.serial_year_1 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_year_1: e.target.value
                      }))
                    }
                  />
                </div>
                <div className="serial-cell serial-year-cell">
                  <input
                    className="serial-input"
                    name="serial_year_2"
                    value={a?.serial_year_2 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_year_2: e.target.value
                      }))
                    }
                  />
                </div>

                <div className="serial-dash">-</div>

                <div className="serial-cell serial-main-cell">
                  <input
                    className="serial-input"
                    name="serial_number_1"
                    value={a?.serial_number_1 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_number_1: e.target.value
                      }))
                    }
                  />
                </div>
                <div className="serial-cell serial-main-cell">
                  <input
                    className="serial-input"
                    name="serial_number_2"
                    value={a?.serial_number_2 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_number_2: e.target.value
                      }))
                    }
                  />
                </div>
                <div className="serial-cell serial-main-cell">
                  <input
                    className="serial-input"
                    name="serial_number_3"
                    value={a?.serial_number_3 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_number_3: e.target.value
                      }))
                    }
                  />
                </div>
                <div className="serial-cell serial-main-cell">
                  <input
                    className="serial-input"
                    name="serial_number_4"
                    value={a?.serial_number_4 ?? ""}
                    maxLength={1}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        serial_number_4: e.target.value
                      }))
                    }
                  />
                </div>
              </div>

              <input
                className="field-input serial-hidden-value"
                name="serial_number"
                value={v(a?.serial_number)}
                readOnly
              />
            </div>

            <div className="field-box product-box">
              <div className="field-label">
                5. TYPE OF PRODUCT <span className="inline-italic">(Required)</span>
              </div>
              <div className="checkbox-stack">
                <label>
                  <input
                    type="radio"
                    name="type_of_product"
                    value="WINE"
                    checked={checked(a?.type_of_product, "WINE")}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        type_of_product: e.target.value
                      }))
                    }
                  />
                  WINE
                </label>
                <label>
                  <input
                    type="radio"
                    name="type_of_product"
                    value="DISTILLED SPIRITS"
                    checked={checked(a?.type_of_product, "DISTILLED")}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        type_of_product: e.target.value
                      }))
                    }
                  />
                  DISTILLED SPIRITS
                </label>
                <label>
                  <input
                    type="radio"
                    name="type_of_product"
                    value="MALT BEVERAGES"
                    checked={checked(a?.type_of_product, "MALT")}
                    onChange={(e) =>
                      setFormApplication((current) => ({
                        ...(current ?? {} as ApplicationData),
                        type_of_product: e.target.value
                      }))
                    }
                  />
                  MALT BEVERAGES
                </label>
              </div>
            </div>
          </div>

          <div className="field-box">
            <div className="field-label">6. BRAND NAME (Required)</div>
            <input
              className="field-input"
              name="brand_name"
              value={a?.brand_name ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  brand_name: e.target.value
                }))
              }
            />
          </div>

          <div className="field-box">
            <div className="field-label">7. FANCIFUL NAME (If any)</div>
            <input
              className="field-input"
              name="fanciful_name"
              value={a?.fanciful_name ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  fanciful_name: e.target.value
                }))
              }
            />
          </div>

          <div className="mini-row two uneven">
            <div className="field-box">
              <div className="field-label">9. FORMULA</div>
              <input
                className="field-input"
                name="formula"
                value={a?.formula ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    formula: e.target.value
                  }))
                }
              />
            </div>
            <div className="field-box">
              <div className="field-label">10. GRAPE VARIETAL(S) Wine only</div>
              <input
                className="field-input"
                name="grape_varietal"
                value={a?.grape_varietal ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    grape_varietal: e.target.value
                  }))
                }
              />
            </div>
          </div>

          <div className="field-box">
            <div className="field-label">11. WINE APPELLATION (If on label)</div>
            <input
              className="field-input"
              name="wine_appellation"
              value={a?.wine_appellation ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  wine_appellation: e.target.value
                }))
              }
            />
          </div>

          <div className="mini-row two">
            <div className="field-box">
              <div className="field-label">12. PHONE NUMBER</div>
              <input
                className="field-input"
                name="phone_number"
                value={a?.phone_number ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    phone_number: e.target.value
                  }))
                }
              />
            </div>
            <div className="field-box">
              <div className="field-label">13. EMAIL ADDRESS</div>
              <input
                className="field-input"
                name="email_address"
                value={a?.email_address ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    email_address: e.target.value
                  }))
                }
              />
            </div>
          </div>
        </div>

        <div className="right-col">
          <div className="field-box big-area">
            <div className="field-label">
              8. NAME AND ADDRESS OF APPLICANT AS SHOWN ON PLANT REGISTRY, BASIC
              PERMIT, OR BREWER'S NOTICE. INCLUDE APPROVED DBA OR TRADENAME IF
              USED ON THE LABEL (Required)
            </div>
            <textarea
              className="field-textarea"
              name="name_and_address"
              value={a?.name_and_address ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  name_and_address: e.target.value
                }))
              }
            />
          </div>

          <div className="field-box medium-area">
            <div className="field-label">8a. MAILING ADDRESS, IF DIFFERENT</div>
            <textarea
              className="field-textarea"
              name="mailing_address"
              value={a?.mailing_address ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  mailing_address: e.target.value
                }))
              }
            />
          </div>

          <div className="application-type-box">
            <div className="application-type-title">
              14. TYPE OF APPLICATION <span className="inline-italic">(Check applicable box(es))</span>
            </div>

            <div className="application-option-row">
              <span className="option-prefix">a.</span>
              <input
                type="radio"
                name="type_of_application"
                value="CERTIFICATE OF LABEL APPROVAL"
                checked={checked(a?.type_of_application, "CERTIFICATE OF LABEL APPROVAL")}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    type_of_application: e.target.value
                  }))
                }
              />
              <span className="option-text">CERTIFICATE OF LABEL APPROVAL</span>
            </div>

            <div className="application-option-row">
              <span className="option-prefix">b.</span>
              <input
                type="radio"
                name="type_of_application"
                value="CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL"
                checked={checked(a?.type_of_application, "EXEMPTION")}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    type_of_application: e.target.value
                  }))
                }
              />
              <span className="option-text">CERTIFICATE OF EXEMPTION FROM LABEL APPROVAL</span>
            </div>

            <div className="application-subline tight-subline">
              <span className="quoted">"For sale in</span>
              <input
                className="inline-line-input state-input"
                name="sale_in_state"
                value={a?.sale_in_state ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    sale_in_state: e.target.value
                  }))
                }
              />
              <span className="quoted">only"</span>
              <span className="inline-italic">(Fill in State abbreviation)</span>
            </div>

            <div className="application-option-row capacity-row">
              <span className="option-prefix">c.</span>
              <input
                type="radio"
                name="type_of_application"
                value="DISTINCTIVE LIQUOR BOTTLE APPROVAL"
                checked={checked(a?.type_of_application, "DISTINCTIVE")}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    type_of_application: e.target.value
                  }))
                }
              />
              <span className="option-text">
                DISTINCTIVE LIQUOR BOTTLE APPROVAL. TOTAL BOTTLE CAPACITY
                <br />
                BEFORE CLOSURE
              </span>
              <input
                className="inline-line-input capacity-input"
                name="bottle_capacity"
                value={a?.bottle_capacity ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    bottle_capacity: e.target.value
                  }))
                }
              />
            </div>

            <div className="application-subline tight-subline">
              <span className="inline-italic">(Fill in amount)</span>
            </div>

            <div className="application-option-row">
              <span className="option-prefix">d.</span>
              <input
                type="radio"
                name="type_of_application"
                value="RESUBMISSION AFTER REJECTION"
                checked={checked(a?.type_of_application, "RESUBMISSION")}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    type_of_application: e.target.value
                  }))
                }
              />
              <span className="option-text">RESUBMISSION AFTER REJECTION</span>
            </div>

            <div className="application-subline tight-subline">
              <span>TTB ID</span>
              <input
                className="inline-line-input ttb-inline-input"
                name="resubmission_ttb_id"
                value={a?.resubmission_ttb_id ?? ""}
                onChange={(e) =>
                  setFormApplication((current) => ({
                    ...(current ?? {} as ApplicationData),
                    resubmission_ttb_id: e.target.value
                  }))
                }
              />
            </div>
          </div>
        </div>
      </div>

      <div className="field-box notes-box">
        <div className="field-label">
          15. SHOW ANY INFORMATION THAT IS BLOWN, BRANDED, OR EMBOSSED ON THE CONTAINER (e.g., net contents) ONLY IF IT DOES NOT APPEAR ON THE LABELS
          AFFIXED BELOW. ALSO, SHOW TRANSLATIONS OF FOREIGN LANGUAGE TEXT APPEARING ON LABELS
        </div>
        <textarea
          className="field-textarea notes-textarea"
          name="container_notes"
          value={a?.container_notes ?? ""}
          onChange={(e) =>
            setFormApplication((current) => ({
              ...(current ?? {} as ApplicationData),
              container_notes: e.target.value
            }))
          }
        />
      </div>

      <div className="part-title">PART II - APPLICANT'S CERTIFICATION</div>

      <div className="cert-text">
        Under the penalties of perjury, I declare: that all statements appearing on this application are true and correct to the best of my knowledge and belief;
        and, that the representations on the labels attached to this form, including supplemental documents, truly and correctly represent the content of the
        containers to which these labels will be applied. I also certify that I have read, understood, and complied with the conditions and instructions which are
        attached to an original TTBF5100.31, Certificate/Exemption of Label/Bottle Approval. I consent to the return of processed applications in the manner
        indicated on this application and set forth in the applicable instructions.
      </div>

      <div className="mini-row three cert-row">
        <div className="field-box">
          <div className="field-label">16. DATE OF APPLICATION</div>
          <input
            className="field-input"
            name="date_of_application"
            value={a?.date_of_application ?? ""}
            onChange={(e) =>
              setFormApplication((current) => ({
                ...(current ?? {} as ApplicationData),
                date_of_application: e.target.value
              }))
            }
          />
        </div>

        <div className="field-box">
          <div className="field-label">17. SIGNATURE OF APPLICANT OR AUTHORIZED AGENT</div>

          {a?.signature?.startsWith("/static/") || a?.signature?.startsWith("http") ? (
            <>
              <div className="signature-preview-box">
                <img
                  src={a.signature}
                  alt="Applicant or authorized agent signature"
                  className="signature-preview-image"
                />
              </div>
              <input type="hidden" name="signature" value={a.signature} />
            </>
          ) : (
            <input
              className="field-input"
              name="signature"
              value={a?.signature ?? ""}
              onChange={(e) =>
                setFormApplication((current) => ({
                  ...(current ?? {} as ApplicationData),
                  signature: e.target.value
                }))
              }
            />
          )}
        </div>

        <div className="field-box">
          <div className="field-label">18. PRINT NAME OF APPLICANT OR AUTHORIZED AGENT</div>
          <input
            className="field-input"
            name="print_name_of_applicant"
            value={a?.print_name_of_applicant ?? ""}
            onChange={(e) =>
              setFormApplication((current) => ({
                ...(current ?? {} as ApplicationData),
                print_name_of_applicant: e.target.value
              }))
            }
          />
        </div>
      </div>

      <div className="part-title">PART III - TTB CERTIFICATE</div>

      <div className="cert-text ttb-readonly-section">
        This certificate is issued subject to applicable laws, regulations, and conditions as set forth in the
        instructions portion of this form.
      </div>

      <div className="mini-row two ttb-readonly-section">
        <div className="field-box">
          <div className="field-label">19. DATE ISSUED</div>
          <div className="field-value ttb-readonly-box" />
        </div>
        <div className="field-box">
          <div className="field-label">20. AUTHORIZED SIGNATURE, ALCOHOL AND TOBACCO TAX AND TRADE BUREAU</div>
          <div className="field-value ttb-readonly-box" />
        </div>
      </div>

      <div className="part-title">FOR TTB USE ONLY</div>

      <div className="ttb-bottom-grid ttb-readonly-section">
        <div className="field-box qualifications-box">
          <div className="field-label">QUALIFICATIONS</div>
          <div className="field-value large-readonly-box ttb-readonly-box" />
        </div>

        <div className="field-box expiration-box">
          <div className="field-label">
            EXPIRATION DATE <span className="inline-italic">(If any)</span>
          </div>
          <div className="field-value expiration-value ttb-readonly-box" />
        </div>
      </div>

      <div className="upload-images-section">
        <div className="part-title">AFFIX COMPLETE SET OF LABELS BELOW</div>
        <div className="upload-images-inner">
          <input
            ref={fileInputRef}
            id="label_images"
            name="label_images"
            type="file"
            accept="image/*"
            multiple
            onChange={handleLabelImagesChange}
            className="visually-hidden-file-input"
          />

          <button
            type="button"
            className="upload-images-dropzone"
            onClick={handleOpenFilePicker}
          >
            upload images here
          </button>

          <div className="label-preview-sheet">
            {labelPreviews.length === 0 ? (
              <div className="label-preview-empty">No images uploaded.</div>
            ) : (
              labelPreviews.map((preview) => (
                <div className="label-preview-card" key={preview.id}>
                  <button
                    type="button"
                    className="label-preview-remove"
                    onClick={() => handleRemoveImage(preview.id)}
                    aria-label={`Remove ${preview.name}`}
                  >
                    ×
                  </button>
                  <img
                    src={preview.url}
                    alt={preview.name}
                    className="label-preview-image"
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="form-actions">
        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting..." : "Submit Application"}
        </button>
      </div>

      {hasSubmitted && submitSuccess && <div className="status">{submitSuccess}</div>}
      {hasSubmitted && submitError && <div className="error">{submitError}</div>}
    </form>
  );
}