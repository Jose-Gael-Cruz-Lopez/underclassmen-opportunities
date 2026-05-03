import { loadOpportunities } from "@/lib/parse-readme";
import { Browser } from "@/components/browser";

export default function Home() {
  const opportunities = loadOpportunities();

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <header className="border-b border-zinc-200 dark:border-zinc-900">
        <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 text-sm font-medium text-emerald-700 dark:text-emerald-400">
              <span className="text-lg">🌱</span>
              <span>Underclassmen Opportunities</span>
            </div>
            <h1 className="max-w-3xl text-balance text-3xl font-semibold leading-tight tracking-tight text-zinc-950 dark:text-zinc-50 sm:text-4xl lg:text-5xl">
              The only opportunity board built for college freshmen and sophomores.
            </h1>
            <p className="max-w-2xl text-base leading-relaxed text-zinc-600 dark:text-zinc-400">
              Internships, fellowships, research, and scholarships — designed for
              first and second-year students. No experience required. No
              junior-year gatekeeping. Updated daily.
            </p>
            <div className="mt-2 flex flex-wrap gap-3 text-sm">
              <a
                href="https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full bg-zinc-900 px-4 py-1.5 font-medium text-zinc-50 hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                Star on GitHub →
              </a>
              <a
                href="https://github.com/Jose-Gael-Cruz-Lopez/underclassmen-opportunities/issues/new/choose"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full border border-zinc-300 px-4 py-1.5 font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-900"
              >
                Submit an opportunity
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Browser opportunities={opportunities} />
      </main>

      <footer className="mt-16 border-t border-zinc-200 dark:border-zinc-900">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-2 px-4 py-8 text-sm text-zinc-500 sm:flex-row sm:items-center sm:px-6 lg:px-8 dark:text-zinc-400">
          <div>
            Built by{" "}
            <a
              href="https://www.linkedin.com/in/josegaelcruz"
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-zinc-900 hover:underline dark:text-zinc-100"
            >
              Jose Cruz
            </a>
          </div>
          <div>Open source · Community-driven</div>
        </div>
      </footer>
    </div>
  );
}
