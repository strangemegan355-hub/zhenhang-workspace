import { redirect } from "next/navigation";

/** 产品分类已合并至产品库左侧分类树 */
export default function ProductCategoriesPage() {
  redirect("/products");
}
