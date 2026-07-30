import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

const STEPS = [
  "Finding relevant documents",
  "Searching vector index",
  "Ranking evidence",
  "Generating answer",
  "Scoring confidence",
  "Finalizing",
];

export function AnalyzeStepper({ active }: { active: boolean }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!active) {
      setStep(0);
      return;
    }
    setStep(0);
    const id = window.setInterval(() => {
      setStep((s) => (s < STEPS.length - 1 ? s + 1 : s));
    }, 900);
    return () => window.clearInterval(id);
  }, [active]);

  return (
    <AnimatePresence>
      {active ? (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.16 }}
          className="panel mt-4 p-4"
          role="status"
          aria-live="polite"
          aria-busy="true"
        >
          <div className="flex items-center gap-2">
            <Loader2
              className="h-3.5 w-3.5 animate-spin text-foreground"
              aria-hidden
            />
            <p className="text-[13px] font-medium text-foreground">
              Analyzing question
            </p>
            <span className="ml-auto text-[11px] tabular text-muted-foreground">
              {step + 1}/{STEPS.length}
            </span>
          </div>
          <div className="mt-3 h-1 overflow-hidden rounded-[2px] bg-muted">
            <div
              className="h-full bg-foreground transition-[width] duration-500 ease-product"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
          <ol className="mt-3 space-y-1.5">
            {STEPS.map((label, i) => {
              const done = i < step;
              const current = i === step;
              return (
                <li
                  key={label}
                  className={cn(
                    "flex items-center gap-2 text-[12px] transition-colors",
                    current
                      ? "font-medium text-foreground"
                      : done
                        ? "text-muted-foreground"
                        : "text-muted-foreground/45",
                  )}
                >
                  <span
                    className={cn(
                      "flex h-4 w-4 items-center justify-center rounded-[3px] border text-[9px]",
                      current &&
                        "border-foreground bg-foreground text-background",
                      done && "border-success/40 bg-success/10 text-success",
                      !done && !current && "border-border",
                    )}
                  >
                    {done ? "✓" : i + 1}
                  </span>
                  {label}
                </li>
              );
            })}
          </ol>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
