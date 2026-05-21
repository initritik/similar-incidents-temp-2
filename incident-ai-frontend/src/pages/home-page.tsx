export function HomePage() {
  return (
    <section className="mx-auto flex min-h-[calc(100vh-9rem)] max-w-3xl items-center justify-center">
      <div className="w-full rounded-lg border border-border bg-card p-8 text-card-foreground shadow-sm">
        <p className="text-sm font-medium text-muted-foreground">
          Frontend foundation is ready.
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-normal">
          Incident AI Assistant
        </h2>
        <p className="mt-4 text-sm leading-6 text-muted-foreground">
          This shell provides the application layout, styling system, and
          enterprise-ready project structure for future incident workflows.
        </p>
      </div>
    </section>
  );
}
