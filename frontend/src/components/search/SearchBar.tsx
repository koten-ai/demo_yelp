type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
  large?: boolean;
};

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder = "Find coffee, dinner, parks…",
  large,
}: Props) {
  return (
    <form
      className={`relative w-full ${large ? "max-w-3xl" : "max-w-2xl"}`}
      onSubmit={(e) => {
        e.preventDefault();
        if (!loading) onSubmit();
      }}
    >
      <label className="sr-only" htmlFor="localai-search">
        Search
      </label>
      <input
        id="localai-search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={loading}
        className={`w-full rounded-2xl bg-surface-container-lowest border border-outline-variant/40 card-shadow
          pl-5 pr-16 text-on-surface placeholder:text-on-surface-variant/70
          focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
          ${large ? "h-14 text-base" : "h-12 text-sm"}`}
        autoComplete="off"
      />
      <button
        type="submit"
        disabled={loading || !value.trim()}
        aria-label="Search"
        className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-xl ai-gradient text-white
          flex items-center justify-center disabled:opacity-50 shadow-md"
      >
        {loading ? (
          <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
        ) : (
          <span className="material-symbols-outlined text-[20px]">search</span>
        )}
      </button>
    </form>
  );
}
