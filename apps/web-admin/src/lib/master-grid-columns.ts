import type { GridColumn } from "@zhenhang/data-grid";

/** Shared master-data grid columns for product management pages */

export const masterCodeCol = <T extends Record<string, unknown>>(): GridColumn<T> => ({
  key: "code" as GridColumn<T>["key"],
  title: "编码",
  canView: true,
  fixed: "left",
  width: 120,
});

export const masterNameCol = <T extends Record<string, unknown>>(): GridColumn<T> => ({
  key: "name" as GridColumn<T>["key"],
  title: "名称",
  canView: true,
  width: 200,
});

export const masterStatusCol = <T extends Record<string, unknown>>(): GridColumn<T> => ({
  key: "status" as GridColumn<T>["key"],
  title: "状态",
  canView: true,
  width: 88,
});

export const masterRemarkCol = <T extends Record<string, unknown>>(): GridColumn<T> => ({
  key: "remark" as GridColumn<T>["key"],
  title: "备注",
  canView: true,
  width: 200,
});
