import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {
  Opportunity,
  Section,
  Status,
  SECTION_LABELS,
} from "./types";

const README_PATH = path.join(process.cwd(), "..", "README.md");

const TABLE_RE = /<!-- (\w+)_TABLE_START -->([\s\S]*?)<!-- \1_TABLE_END -->/g;

const MONTH_MAP: Record<string, number> = {
  january: 0, february: 1, march: 2, april: 3, may: 4, june: 5,
  july: 6, august: 7, september: 8, october: 9, november: 10, december: 11,
  jan: 0, feb: 1, mar: 2, apr: 3, jun: 5, jul: 6, aug: 7,
  sep: 8, sept: 8, oct: 9, nov: 10, dec: 11,
};

const DATE_RE =
  /\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})\b/g;

function parseStatus(cell: string): Status {
  if (cell.includes("CLOSING SOON")) return "CLOSING_SOON";
  if (cell.includes("OPENS SOON")) return "OPENS_SOON";
  if (cell.includes("CLOSED")) return "CLOSED";
  return "OPEN";
}

function extractUrl(cell: string): string {
  const m = cell.match(/href="([^"]+)"/);
  return m ? m[1] : "";
}

function earliestUpcomingDate(text: string, today: Date): Date | null {
  let earliest: Date | null = null;
  const re = new RegExp(DATE_RE.source, "g");
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const monthIdx = MONTH_MAP[m[1].toLowerCase().replace(".", "")];
    if (monthIdx === undefined) continue;
    const day = parseInt(m[2], 10);
    const year = parseInt(m[3], 10);
    const d = new Date(year, monthIdx, day);
    if (d >= today && (!earliest || d < earliest)) earliest = d;
  }
  return earliest;
}

function cleanTitle(text: string): string {
  return text
    .replace(/\s*—\s*Deadline:.*$/i, "")
    .replace(/\s*—\s*"?Application Coming.*$/i, "")
    .trim();
}

function inlineDeadline(text: string): string {
  const m = text.match(/Deadline:\s*([^|]+?)(?:\s*\(Event:|$)/i);
  return m ? m[1].trim() : "";
}

function stableId(...parts: string[]): string {
  return crypto.createHash("md5").update(parts.join("|")).digest("hex").slice(0, 10);
}

function parseTableRows(
  sectionKey: Section,
  body: string,
  today: Date,
): Opportunity[] {
  const lines = body
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.startsWith("|"));
  if (lines.length < 3) return [];

  const headers = lines[0]
    .split("|")
    .slice(1, -1)
    .map((s) => s.trim());

  const headerIdx = (...names: string[]) => {
    for (const name of names) {
      const idx = headers.findIndex((h) =>
        h.toLowerCase().includes(name.toLowerCase()),
      );
      if (idx >= 0) return idx;
    }
    return -1;
  };

  const idx = {
    status: headerIdx("Status"),
    org: headerIdx("Company", "Organization", "State", "University"),
    title: headerIdx("Role", "Program", "Scholarship", "Opportunity"),
    type: headerIdx("Type", "Field", "Amount", "Award"),
    location: headerIdx("Location", "Eligibility"),
    application: headerIdx("Application"),
    deadline: headerIdx("Deadline"),
    datePosted: headerIdx("Date Posted"),
  };

  const dataLines = lines.slice(1).filter((l) => !/^\|\s*-+/.test(l));

  return dataLines.map((line) => {
    const cells = line.split("|").slice(1, -1).map((s) => s.trim());
    const get = (i: number) => (i >= 0 ? cells[i] || "" : "");

    const status = parseStatus(get(idx.status));
    const organization = get(idx.org);
    const rawTitle = get(idx.title);
    const title = cleanTitle(rawTitle);
    const type = get(idx.type);
    const location = get(idx.location);
    const url = extractUrl(get(idx.application));

    const deadlineRaw =
      idx.deadline >= 0
        ? get(idx.deadline)
        : inlineDeadline(rawTitle);

    const deadlineDate = earliestUpcomingDate(deadlineRaw, today);
    const deadlineISO = deadlineDate
      ? deadlineDate.toISOString().slice(0, 10)
      : null;
    const daysUntilDeadline = deadlineDate
      ? Math.round(
          (deadlineDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
        )
      : null;

    return {
      id: stableId(sectionKey, organization, title, url),
      section: sectionKey,
      sectionLabel: SECTION_LABELS[sectionKey],
      status,
      organization,
      title,
      type,
      location,
      url,
      deadlineRaw,
      deadlineISO,
      daysUntilDeadline,
    };
  });
}

const SECTION_ALIAS: Record<string, Section> = {
  INTERNSHIPS: "INTERNSHIPS",
  PROGRAMS: "PROGRAMS",
  RESEARCH: "RESEARCH",
  SCHOLARSHIPS: "SCHOLARSHIPS",
  HBCU: "HBCU",
  WOMEN: "WOMEN",
  RISING_FRESHMEN: "RISING_FRESHMEN",
  STATE: "STATE",
};

export function loadOpportunities(): Opportunity[] {
  const md = fs.readFileSync(README_PATH, "utf-8");
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const all: Opportunity[] = [];
  let m: RegExpExecArray | null;
  const re = new RegExp(TABLE_RE.source, "g");
  while ((m = re.exec(md)) !== null) {
    const key = SECTION_ALIAS[m[1]];
    if (!key) continue;
    all.push(...parseTableRows(key, m[2], today));
  }
  return all;
}
