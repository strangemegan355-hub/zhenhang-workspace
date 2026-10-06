/**
 * The page envelope the API returns, in one place.
 *
 * Nineteen modules under `domains/` each declared their own copy of this, all of them typing `items` as
 * `Record<string, unknown>[]`; two of them carried `page` and `page_size` as well. The backend's page model is
 * `PageResponse`, so the fields here mirror it. The type parameter defaults to `Record<string, unknown>` so existing
 * call sites keep compiling, and a hook that knows its row type can say `PageData<SomeRead>`.
 */
export type PageData<T = Record<string, unknown>> = {
  items?: T[];
  total?: number;
  page?: number;
  page_size?: number;
};
