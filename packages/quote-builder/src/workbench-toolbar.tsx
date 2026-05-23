"use client";

export function WorkbenchToolbar({
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  onSave,
  saving,
  readOnly,
  itemCount,
  bomCount,
}: {
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onSave?: () => void;
  saving?: boolean;
  readOnly?: boolean;
  itemCount: number;
  bomCount: number;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-zinc-200 bg-zinc-50/80 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900/80">
      <div className="flex items-center gap-1 border-r pr-2 dark:border-zinc-700">
        <ToolbarBtn label="撤销" shortcut="Ctrl+Z" disabled={!canUndo || readOnly} onClick={onUndo} />
        <ToolbarBtn label="重做" shortcut="Ctrl+Y" disabled={!canRedo || readOnly} onClick={onRedo} />
      </div>
      <span className="text-xs text-zinc-500">
        {itemCount} 行 · BOM {bomCount} 项
      </span>
      <div className="ml-auto flex gap-2">
        {!readOnly && onSave ? (
          <button
            type="button"
            className="rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50"
            disabled={saving}
            onClick={onSave}
          >
            {saving ? "保存中…" : "保存版本"}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function ToolbarBtn({
  label,
  shortcut,
  disabled,
  onClick,
}: {
  label: string;
  shortcut: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      title={`${label} (${shortcut})`}
      disabled={disabled}
      onClick={onClick}
      className="rounded border border-zinc-300 bg-white px-2.5 py-1 text-xs font-medium hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
    >
      {label}
    </button>
  );
}
