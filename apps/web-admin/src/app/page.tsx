import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <div className="rounded-lg border bg-white p-8 dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-lg font-semibold">Zhenhang ERP Admin Platform</h1>
        <p className="mt-2 text-sm text-zinc-500">Frontend skeleton initialized.</p>
        <div className="mt-4 flex gap-2">
          <Link className="rounded-md border px-3 py-2 text-sm" href="/login">
            Login
          </Link>
          <Link className="rounded-md border px-3 py-2 text-sm" href="/dashboard">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
