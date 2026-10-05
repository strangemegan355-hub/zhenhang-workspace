/** Auto-generate master-data code when user skips manual entry */

export function autoMasterCode(name: string, prefix = "AUTO"): string {
  const slug =
    name
      .trim()
      .replace(/\s+/g, "")
      .replace(/[^\w\u4e00-\u9fff-]/g, "")
      .slice(0, 24) || prefix;
  const tail = Date.now().toString(36).slice(-5).toUpperCase();
  return `${slug}-${tail}`.slice(0, 64);
}
