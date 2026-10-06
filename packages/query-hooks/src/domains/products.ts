import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";
import { queryKeys } from "../keys";
import type { PageData } from "../types";

type ApiWrap<T> = { code: string; message: string; data: T };

export function useProductCategoriesQuery(page = 1, q?: string) {
  return useQuery({
    queryKey: queryKeys.master.productCategories(page, q),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/product-categories", {
        params: { page, page_size: 100, q },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateProductCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/product-categories", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-categories") });
    },
  });
}

export function useDeleteProductCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/product-categories/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-categories") });
    },
  });
}

export function useProductsQuery(page = 1, q?: string, categoryId?: string) {
  return useQuery({
    queryKey: queryKeys.master.products(page, q, categoryId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/products", {
        params: { page, page_size: 100, q, category_id: categoryId || undefined },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateProductMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/products", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "products") });
    },
  });
}

export function useDeleteProductMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/products/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "products") });
    },
  });
}

export function useProductQuotePayloadQuery(
  productId: string | null,
  costTemplateId?: string,
  priceTemplateId?: string,
  enabled = true,
) {
  return useQuery({
    queryKey: queryKeys.master.productQuotePayload(productId ?? "", costTemplateId, priceTemplateId),
    // `enabled: false` lets a caller hold the query dormant and `refetch()` it on demand.
    enabled: Boolean(productId) && enabled,
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<Record<string, unknown>>>(
        `/api/v1/products/${productId}/quote-payload`,
        {
          params: {
            cost_template_id: costTemplateId || undefined,
            price_template_id: priceTemplateId || undefined,
          },
        },
      );
      return data.data;
    },
    staleTime: 30_000,
  });
}

export function useProductCostTemplatesQuery(page = 1, q?: string, productId?: string) {
  return useQuery({
    queryKey: queryKeys.master.productCostTemplates(page, q, productId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/product-cost-templates", {
        params: { page, page_size: 100, q, product_id: productId || undefined },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateProductCostTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/product-cost-templates", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-cost-templates") });
    },
  });
}

export function useDeleteProductCostTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/product-cost-templates/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-cost-templates") });
    },
  });
}

export function useProductPriceTemplatesQuery(page = 1, q?: string, productId?: string) {
  return useQuery({
    queryKey: queryKeys.master.productPriceTemplates(page, q, productId),
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<PageData>>("/api/v1/product-price-templates", {
        params: { page, page_size: 100, q, product_id: productId || undefined },
      });
      return data.data;
    },
    staleTime: 60_000,
  });
}

export function useCreateProductPriceTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      const { data } = await apiClient.post<ApiWrap<Record<string, unknown>>>("/api/v1/product-price-templates", body);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-price-templates") });
    },
  });
}

export function useDeleteProductPriceTemplateMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.delete<ApiWrap<Record<string, unknown>>>(`/api/v1/product-price-templates/${id}`);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk("master", "product-price-templates") });
    },
  });
}
