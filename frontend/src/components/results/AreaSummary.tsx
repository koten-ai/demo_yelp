type Props = { text: string; title?: string };

export default function AreaSummary({ text, title = "AI Area Summary" }: Props) {
  if (!text) return null;
  return (
    <div className="glass rounded-2xl p-4 md:p-5 border border-primary/10">
      <div className="flex items-center gap-2 mb-2">
        <span className="material-symbols-outlined text-primary text-[20px]">
          auto_awesome
        </span>
        <h2 className="font-semibold text-primary">{title}</h2>
      </div>
      <p className="text-sm md:text-base text-on-surface whitespace-pre-wrap leading-relaxed max-w-prose">
        {text.length > 600 ? text.slice(0, 597) + "…" : text}
      </p>
    </div>
  );
}
