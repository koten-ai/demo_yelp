import type { ReactNode } from "react";

/** Very small markdown subset for AI summaries: **bold**, - lists, paragraphs. */
export function renderSimpleMarkdown(text: string): ReactNode[] {
  const lines = (text || "").replace(/\r\n/g, "\n").split("\n");
  const nodes: ReactNode[] = [];
  let listItems: ReactNode[] = [];
  let listKey = 0;

  const flushList = () => {
    if (!listItems.length) return;
    nodes.push(
      <ul key={`ul-${listKey++}`} className="list-disc pl-5 my-2 space-y-1">
        {listItems}
      </ul>
    );
    listItems = [];
  };

  const inline = (line: string, keyBase: string): ReactNode[] => {
    // Split on **bold** segments
    const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
        return (
          <strong key={`${keyBase}-b-${i}`} className="font-semibold text-on-surface">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return <span key={`${keyBase}-t-${i}`}>{part}</span>;
    });
  };

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd();
    const trimmed = line.trim();
    if (!trimmed) {
      flushList();
      return;
    }
    const bullet = trimmed.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      listItems.push(
        <li key={`li-${idx}`} className="leading-relaxed">
          {inline(bullet[1], `li-${idx}`)}
        </li>
      );
      return;
    }
    flushList();
    // Heading-ish: lone **Title** line
    if (/^\*\*[^*]+\*\*$/.test(trimmed)) {
      nodes.push(
        <p key={`h-${idx}`} className="font-semibold text-on-surface mt-1 mb-1">
          {trimmed.slice(2, -2)}
        </p>
      );
      return;
    }
    nodes.push(
      <p key={`p-${idx}`} className="my-1.5 leading-relaxed">
        {inline(trimmed, `p-${idx}`)}
      </p>
    );
  });
  flushList();
  return nodes;
}
