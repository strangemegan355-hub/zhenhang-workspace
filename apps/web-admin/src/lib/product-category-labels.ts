/** 电机分类下规格栏展示为「功率」，其余分类为「规格」。 */
export function isMotorCategory(categoryName?: string | null): boolean {
  if (!categoryName) return false;
  return categoryName.includes("电机");
}

export function productSpecLabel(categoryName?: string | null): string {
  return isMotorCategory(categoryName) ? "功率" : "规格";
}

export function productSpecPlaceholder(categoryName?: string | null): string {
  return isMotorCategory(categoryName) ? "如 55kW、75kW" : "如 型号、尺寸、材质等";
}
