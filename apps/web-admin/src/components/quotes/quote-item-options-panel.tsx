"use client";

import { apiClient } from "@zhenhang/http-client";
import { useEffect, useState } from "react";

type OptionItem = { id: string; name: string; price_adjustment: number; group_name: string };
type QuoteItem = { id: string; item_name: string; unit_price: number; selected_options: string[] | null; machine_id?: string };

export default function QuoteItemOptionsPanel({
  quoteId,
  items,
  onOptionsUpdated,
}: {
  quoteId: string;
  items: QuoteItem[];
  onOptionsUpdated: () => void;
}) {
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [machineOptions, setMachineOptions] = useState<OptionItem[]>([]);
  const [selectedOptionIds, setSelectedOptionIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const selectedItem = items.find((i) => i.id === selectedItemId) ?? null;

  useEffect(() => {
    let ignore = false;
    if (!selectedItem?.machine_id) {
      // ponytail: sync reset on item switch is required UX; no stale options shown
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMachineOptions([]);
      setSelectedOptionIds(selectedItem?.selected_options ?? []);
      return;
    }
    setLoading(true);
    apiClient
      .get<{ data: Array<{ id: string; name: string; items: Array<{ id: string; name: string; price_adjustment: number }> }> }>(
        `/api/v1/machines/${selectedItem.machine_id}/options`
      )
      .then(({ data }) => {
        if (ignore) return;
        const flat: OptionItem[] = [];
        for (const g of data.data ?? []) {
          for (const i of g.items ?? []) {
            flat.push({ id: i.id, name: i.name, price_adjustment: i.price_adjustment, group_name: g.name });
          }
        }
        setMachineOptions(flat);
        setSelectedOptionIds(selectedItem?.selected_options ?? []);
      })
      .catch(() => { if (!ignore) setMachineOptions([]); })
      .finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [selectedItemId, selectedItem?.machine_id]);

  async function saveOptions() {
    if (!selectedItemId) return;
    setSaving(true);
    try {
      await apiClient.put(
        `/api/v1/quotes/${quoteId}/items/${selectedItemId}/options`,
        { option_item_ids: selectedOptionIds }
      );
      onOptionsUpdated();
    } catch (e) {
      console.error("Failed to save options", e);
    } finally {
      setSaving(false);
    }
  }

  function toggleOption(id: string) {
    setSelectedOptionIds((prev) =>
      prev.includes(id) ? prev.filter((oid) => oid !== id) : [...prev, id]
    );
  }

  if (!items.length) return null;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-700 dark:bg-zinc-900">
      <h4 className="mb-2 text-xs font-semibold">选配项</h4>

      <select
        className="mb-2 w-full rounded border px-2 py-1 text-xs dark:border-zinc-600 dark:bg-zinc-800"
        value={selectedItemId ?? ""}
        onChange={(e) => setSelectedItemId(e.target.value || null)}
      >
        <option value="">选择报价行...</option>
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.item_name} (¥{Number(item.unit_price).toFixed(0)})
          </option>
        ))}
      </select>

      {selectedItem && loading && <p className="text-xs text-zinc-400">加载选项...</p>}

      {selectedItem && !loading && machineOptions.length === 0 && (
        <p className="text-xs text-zinc-400">该机型暂未配置选配项</p>
      )}

      {selectedItem && !loading && machineOptions.length > 0 && (
        <>
          <div className="max-h-60 space-y-1 overflow-auto">
            {machineOptions.map((opt) => (
              <label key={opt.id} className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={selectedOptionIds.includes(opt.id)}
                  onChange={() => toggleOption(opt.id)}
                  className="h-3 w-3"
                />
                <span className="flex-1">{opt.name}</span>
                <span className="text-zinc-400">{opt.group_name}</span>
                <span className="tabular-nums text-emerald-600">+{opt.price_adjustment}</span>
              </label>
            ))}
          </div>
          <button
            type="button"
            disabled={saving}
            onClick={saveOptions}
            className="mt-2 w-full rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "保存中..." : "保存选配"}
          </button>
        </>
      )}
    </div>
  );
}
