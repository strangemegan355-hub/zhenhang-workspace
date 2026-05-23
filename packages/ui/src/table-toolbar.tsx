import * as React from "react";

type Props = {
  keyword: string;
  onKeywordChange: (v: string) => void;
  onExport?: () => void;
};

export function TableToolbar({ keyword, onKeywordChange, onExport }: Props) {
  return (
    <div className="flex items-center gap-2">
      <input
        value={keyword}
        onChange={(e) => onKeywordChange(e.target.value)}
        placeholder="Search..."
        className="h-9 rounded-md border px-3 text-sm"
      />
      {onExport ? (
        <button className="h-9 rounded-md border px-3 text-sm" onClick={onExport}>
          Export
        </button>
      ) : null}
    </div>
  );
}
