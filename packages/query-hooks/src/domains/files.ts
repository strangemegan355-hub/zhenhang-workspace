import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@zhenhang/http-client";
import { qk } from "@zhenhang/query-policy-registry";

type ApiWrap<T> = { code: string; message: string; data: T };

export type FileItem = {
  id: string;
  file_name: string;
  file_ext: string | null;
  mime_type: string | null;
  size_bytes: number;
  category: string;
  created_at: string;
};

const FILES = qk("platform", "files");

export function useFilesQuery(pageSize = 100) {
  return useQuery({
    queryKey: [...FILES, pageSize],
    queryFn: async () => {
      const { data } = await apiClient.get<ApiWrap<{ items?: FileItem[]; total?: number }>>(
        "/api/v1/files",
        { params: { page: 1, page_size: pageSize } },
      );
      return data.data?.items ?? [];
    },
    staleTime: 30_000,
  });
}

export function useUploadFileMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, category }: { file: File; category: string }) => {
      const form = new FormData();
      form.append("category", category);
      form.append("upload", file);
      const { data } = await apiClient.post<ApiWrap<FileItem>>("/api/v1/files/upload", form);
      return data.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: FILES });
    },
  });
}

/**
 * Downloading returns bytes rather than JSON, so the caller decides what to do with them. The
 * filename comes from the file record, not from the response headers.
 */
export function useDownloadFileMutation() {
  return useMutation({
    mutationFn: async (fileId: string) => {
      const { data } = await apiClient.get<Blob>(`/api/v1/files/${fileId}/download`, {
        responseType: "blob",
      });
      return data;
    },
  });
}
