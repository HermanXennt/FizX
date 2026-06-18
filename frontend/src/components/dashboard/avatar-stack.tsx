import { cn } from "@/lib/utils";
import { stableColor } from "@/lib/avatar";

export interface AvatarPerson {
  id: string;
  initials: string;
  color?: string;
}

export function AvatarStack({
  people,
  size = 28,
  max = 4,
  className,
}: {
  people: AvatarPerson[];
  size?: number;
  max?: number;
  className?: string;
}) {
  const shown = people.slice(0, max);
  const remaining = people.length - shown.length;

  return (
    <div className={cn("flex items-center", className)}>
      {shown.map((p, i) => (
        <div
          key={p.id}
          className="flex items-center justify-center rounded-full border-2 border-white font-medium text-white"
          style={{
            backgroundColor: p.color ?? stableColor(p.id),
            width: size,
            height: size,
            fontSize: size * 0.36,
            marginLeft: i === 0 ? 0 : -size * 0.28,
            zIndex: shown.length - i,
          }}
        >
          {p.initials}
        </div>
      ))}
      {remaining > 0 && (
        <div
          className="flex items-center justify-center rounded-full border-2 border-white bg-secondary font-medium text-secondary-foreground"
          style={{
            width: size,
            height: size,
            fontSize: size * 0.32,
            marginLeft: -size * 0.28,
          }}
        >
          +{remaining}
        </div>
      )}
    </div>
  );
}
