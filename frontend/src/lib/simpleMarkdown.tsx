import type { ReactNode } from "react";

/** Split a GFM table row into cells (handles optional leading/trailing pipes). */
function splitTableRow(line: string): string[] {
  let s = line.trim();
  if (s.startsWith("|")) s = s.slice(1);
  if (s.endsWith("|")) s = s.slice(0, -1);
  return s.split("|").map((c) => c.trim());
}

/** True when a line is a markdown table separator (|---|:---:|). */
function isTableSeparator(line: string | undefined): boolean {
  if (!line) return false;
  const cells = splitTableRow(line);
  if (cells.length < 1) return false;
  return cells.every((c) => /^:?-{3,}:?$/.test(c.trim()));
}

function looksLikeTableRow(line: string): boolean {
  const t = line.trim();
  if (!t.includes("|")) return false;
  // Require at least one pipe that isn't only at the edge of a single token.
  return splitTableRow(t).length >= 2;
}

type Align = "left" | "center" | "right";

function parseAlignments(sepLine: string, colCount: number): Align[] {
  const cells = splitTableRow(sepLine);
  const aligns: Align[] = [];
  for (let i = 0; i < colCount; i++) {
    const c = (cells[i] || "").trim();
    const left = c.startsWith(":");
    const right = c.endsWith(":");
    if (left && right) aligns.push("center");
    else if (right) aligns.push("right");
    else aligns.push("left");
  }
  return aligns;
}

const alignClass: Record<Align, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
};

/**
 * Small markdown subset for AI answers / area summaries:
 * # headings, **bold**, `code`, -/* bullets, 1. numbered lists,
 * GFM tables, --- horizontal rules, paragraphs.
 */
export function renderSimpleMarkdown(text: string): ReactNode[] {
  const lines = (text || "").replace(/\r\n/g, "\n").split("\n");
  const nodes: ReactNode[] = [];
  let listItems: ReactNode[] = [];
  let listOrdered = false;
  let listKey = 0;
  let nodeKey = 0;

  const flushList = () => {
    if (!listItems.length) return;
    const Tag = listOrdered ? "ol" : "ul";
    const cls = listOrdered
      ? "list-decimal pl-5 my-2 space-y-1"
      : "list-disc pl-5 my-2 space-y-1";
    nodes.push(
      <Tag key={`list-${listKey++}`} className={cls}>
        {listItems}
      </Tag>
    );
    listItems = [];
    listOrdered = false;
  };

  /** Inline: `code`, then **bold** (code segments skipped for bold). */
  const inline = (line: string, keyBase: string): ReactNode[] => {
    const codeSplit = line.split(/(`[^`]+`)/g).filter((p) => p !== "");
    const out: ReactNode[] = [];
    codeSplit.forEach((seg, si) => {
      if (seg.startsWith("`") && seg.endsWith("`") && seg.length > 2) {
        out.push(
          <code
            key={`${keyBase}-c-${si}`}
            className="rounded bg-surface-container px-1 py-0.5 font-mono text-[0.85em] text-primary"
          >
            {seg.slice(1, -1)}
          </code>
        );
        return;
      }
      const parts = seg.split(/(\*\*[^*]+\*\*)/g).filter((p) => p !== "");
      parts.forEach((part, i) => {
        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
          out.push(
            <strong key={`${keyBase}-b-${si}-${i}`} className="font-semibold text-on-surface">
              {part.slice(2, -2)}
            </strong>
          );
        } else {
          out.push(
            <span key={`${keyBase}-t-${si}-${i}`}>{part}</span>
          );
        }
      });
    });
    return out;
  };

  let i = 0;
  while (i < lines.length) {
    const raw = lines[i];
    const line = raw.trimEnd();
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      i += 1;
      continue;
    }

    // Horizontal rule
    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushList();
      nodes.push(
        <hr
          key={`hr-${nodeKey++}`}
          className="my-3 border-0 border-t border-outline-variant/50"
        />
      );
      i += 1;
      continue;
    }

    // ATX headings # .. ######
    const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      flushList();
      const level = heading[1].length;
      const content = heading[2];
      const cls =
        level <= 1
          ? "text-lg font-bold text-on-surface mt-3 mb-1.5"
          : level === 2
            ? "text-base font-bold text-on-surface mt-3 mb-1.5"
            : "text-sm font-semibold text-on-surface mt-2.5 mb-1";
      nodes.push(
        <p key={`h-${nodeKey++}`} className={cls} role="heading" aria-level={Math.min(level + 1, 6)}>
          {inline(content, `h-${i}`)}
        </p>
      );
      i += 1;
      continue;
    }

    // GFM table: header row + separator, then body rows
    if (looksLikeTableRow(trimmed) && isTableSeparator(lines[i + 1]?.trim())) {
      flushList();
      const headerCells = splitTableRow(trimmed);
      const aligns = parseAlignments(lines[i + 1]!.trim(), headerCells.length);
      const body: string[][] = [];
      let j = i + 2;
      while (j < lines.length) {
        const rowLine = lines[j].trim();
        if (!rowLine) break;
        if (!looksLikeTableRow(rowLine) || isTableSeparator(rowLine)) break;
        const cells = splitTableRow(rowLine);
        // Pad / trim to header width
        const padded = headerCells.map((_, ci) => cells[ci] ?? "");
        body.push(padded);
        j += 1;
      }
      nodes.push(
        <div key={`tbl-wrap-${nodeKey++}`} className="my-3 w-full overflow-x-auto rounded-lg border border-outline-variant/40">
          <table className="w-full min-w-[28rem] border-collapse text-left text-xs md:text-sm">
            <thead>
              <tr className="bg-surface-container-low border-b border-outline-variant/50">
                {headerCells.map((cell, ci) => (
                  <th
                    key={ci}
                    className={`px-2.5 py-2 font-semibold text-on-surface whitespace-nowrap ${alignClass[aligns[ci] || "left"]}`}
                  >
                    {inline(cell, `th-${i}-${ci}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, ri) => (
                <tr
                  key={ri}
                  className="border-b border-outline-variant/30 last:border-0 odd:bg-surface-container-lowest even:bg-surface-container-low/40"
                >
                  {row.map((cell, ci) => (
                    <td
                      key={ci}
                      className={`px-2.5 py-2 align-top text-on-surface-variant ${alignClass[aligns[ci] || "left"]} ${ci === 0 ? "font-medium text-on-surface whitespace-nowrap" : ""}`}
                    >
                      {inline(cell, `td-${i}-${ri}-${ci}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      i = j;
      continue;
    }

    // Unordered list
    const bullet = trimmed.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      if (listItems.length && listOrdered) flushList();
      listOrdered = false;
      listItems.push(
        <li key={`li-${i}`} className="leading-relaxed">
          {inline(bullet[1], `li-${i}`)}
        </li>
      );
      i += 1;
      continue;
    }

    // Ordered list
    const numbered = trimmed.match(/^\d+[.)]\s+(.*)$/);
    if (numbered) {
      if (listItems.length && !listOrdered) flushList();
      listOrdered = true;
      listItems.push(
        <li key={`oli-${i}`} className="leading-relaxed">
          {inline(numbered[1], `oli-${i}`)}
        </li>
      );
      i += 1;
      continue;
    }

    flushList();

    // Heading-ish: lone **Title** line (legacy / non-ATX)
    if (/^\*\*[^*]+\*\*$/.test(trimmed)) {
      nodes.push(
        <p key={`hs-${nodeKey++}`} className="font-semibold text-on-surface mt-1 mb-1">
          {trimmed.slice(2, -2)}
        </p>
      );
      i += 1;
      continue;
    }

    nodes.push(
      <p key={`p-${nodeKey++}`} className="my-1.5 leading-relaxed">
        {inline(trimmed, `p-${i}`)}
      </p>
    );
    i += 1;
  }

  flushList();
  return nodes;
}
