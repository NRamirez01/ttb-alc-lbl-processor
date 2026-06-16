export type OCRRegion = {
  label: string;
  text: string;
  bbox: number[];
  polygon_points?: number[][] | null;
  score?: number | null;
  order?: number | null;
};

export type ImageResult = {
  image_type: string;
  file_name: string;
  src: string;
  ocr_text: string;
  ocr_html?: string | null;
  ocr_regions: OCRRegion[];
  annotated_src?: string | null;
  width?: number | null;
  height?: number | null;
};

export type ApplicationData = {
  ttb_id: string;
  ct: string;
  or_value: string;

  rep_id_no: string;

  plant_registry_basic_permit_brewers_no: string;
  source_of_product: string;

  serial_number: string;
  serial_year_1: string;
  serial_year_2: string;
  serial_number_1: string;
  serial_number_2: string;
  serial_number_3: string;
  serial_number_4: string;

  type_of_product: string;
  brand_name: string;
  fanciful_name: string;

  name_and_address: string;
  mailing_address: string;

  formula: string;
  grape_varietal: string;
  wine_appellation: string;

  phone_number: string;
  email_address: string;
  fax_number: string;

  type_of_application: string;
  sale_in_state: string;
  bottle_capacity: string;
  resubmission_ttb_id: string;

  container_notes: string;

  date_of_application: string;
  signature: string;
  print_name_of_applicant: string;

  date_issued: string;
  authorized_signature: string;
  qualifications: string;
  expiration_date: string;

  net_contents: string;
  alcohol_content: string;
  wine_vintage_date: string;
};

export type ProcessResponse = {
  application: ApplicationData;
  images: ImageResult[];
  timing_ms: number;
  warnings?: string[];
  validation?: Record<string, unknown>;
  label_rule_results?: Array<Record<string, unknown>> | Record<string, unknown>;
  signature_image?: string | null;
};

export type ValidationCheck = {
  field: string;
  expected: string;
  found: string;
  status: string;
  message: string;
};

export type ValidationResult = {
  overall_status: string;
  checks: ValidationCheck[];
  combined_ocr_text: string;
};

export type LabelRuleSummary = {
  category: string;
  overall_status?: string;
  summary?: Record<string, string>;
  checks?: Record<string, unknown>;
};

export type SubmitResult = {
  application: ApplicationData;
  label_images: ImageResult[];
  validation: ValidationResult;
  label_rule_results: LabelRuleSummary | Record<string, unknown>;
};