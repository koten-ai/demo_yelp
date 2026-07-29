import { renderSimpleMarkdown } from "../../lib/simpleMarkdown";

type Props = { text: string; title?: string };

export default function AreaSummary({ text, title = "AI Area Summary" }: Props) {
  if (!text) return null;
  const display = text.length > 1200 ? text.slice(0, 1197) + "…" : text;
  return (
    <div className="glass rounded-2xl p-4 md:p-5 border border-primary/10">
      <div className="flex items-center gap-2 mb-2">
        <span className="material-symbols-outlined text-primary text-[20px]">
          auto_awesome
        </span>
        <h2 className="font-semibold text-primary">{title}</h2>
      </div>
      <div className="text-sm md:text-base text-on-surface max-w-prose">
        {renderSimpleMarkdown(display)}
      </div>
    </div>
  );
}
