import { redirect } from "next/navigation";

/** 新建报价已并入报价中心单页，保留路由仅做重定向 */
export default function NewQuoteRedirectPage() {
  redirect("/quotes?create=1");
}
