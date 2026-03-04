interface TocEntry {
  id: string;
  label: string;
}

interface TocNavProps {
  entries: TocEntry[];
}

export function TocNav({ entries }: TocNavProps) {
  if (entries.length === 0) return null;

  const handleClick = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <nav className="fixed right-4 top-1/2 -translate-y-1/2 z-10 hidden lg:flex">
      <div className="relative">
        {/* Single continuous vertical line */}
        <div className="absolute left-[3px] top-1 bottom-1 w-px bg-neutral-300" />
        {/* Dot + label rows */}
        <div className="flex flex-col gap-5">
          {entries.map((entry) => (
            <button
              key={entry.id}
              type="button"
              onClick={() => handleClick(entry.id)}
              className="flex items-center gap-2.5 group cursor-pointer"
            >
              <div className="relative z-[1] h-[7px] w-[7px] rounded-full bg-neutral-400 group-hover:bg-brand-600 transition-colors shrink-0" />
              <span className="text-[10px] leading-none text-muted-foreground group-hover:text-foreground transition-colors whitespace-nowrap">
                {entry.label}
              </span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
