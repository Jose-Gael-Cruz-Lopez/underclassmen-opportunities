export type Status = "OPEN" | "CLOSING_SOON" | "OPENS_SOON" | "CLOSED";

export type Section =
  | "INTERNSHIPS"
  | "PROGRAMS"
  | "AMBASSADORS"
  | "RESEARCH"
  | "SCHOLARSHIPS"
  | "HBCU"
  | "WOMEN"
  | "RISING_FRESHMEN"
  | "STATE";

export type Opportunity = {
  id: string;
  section: Section;
  sectionLabel: string;
  status: Status;
  organization: string;
  title: string;
  type: string;
  location: string;
  url: string;
  deadlineRaw: string;
  deadlineISO: string | null;
  daysUntilDeadline: number | null;
};

export const SECTION_LABELS: Record<Section, string> = {
  INTERNSHIPS: "Internships",
  PROGRAMS: "Programs & Fellowships",
  AMBASSADORS: "Ambassadors",
  RESEARCH: "Research",
  SCHOLARSHIPS: "Scholarships",
  HBCU: "HBCU",
  WOMEN: "Women & Gender-Minority",
  RISING_FRESHMEN: "Rising Freshmen",
  STATE: "State Grants",
};

export const STATUS_LABELS: Record<Status, string> = {
  OPEN: "Open",
  CLOSING_SOON: "Closing Soon",
  OPENS_SOON: "Opens Soon",
  CLOSED: "Closed",
};
