const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ApiError = {
    status: number;
    message: string;
    detail?: unknown;
};

export type RequestOptions = {
    method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    query?: Record<string, string | number | boolean | undefined | null>;
    body?: unknown;
    headers?: Record<string, string>;
    signal?: AbortSignal;
};

function buildUrl(path: string, query?: RequestOptions["query"]) {
    const url = new URL(`${BASE_URL}${path}`);
    if(query){
        for(const [key, value] of Object.entries(query)){
            if(value === undefined || value === null) continue;
            url.searchParams.append(key, String(value));
        }
    }
    return url.toString();
}

async function parseJsonSafe(res: Response) {
    const text = await res.text().catch(() => "");
    if(!text) return null;
    try {
        return JSON.parse(text);
    }catch{
        return text;
    }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(path, options.query);

  const res = await fetch(url, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    signal: options.signal,
  });

  
  if (!res.ok) {
    const detail = await parseJsonSafe(res);
    const err: ApiError = {
      status: res.status,
      message: `HTTP ${res.status} ${res.statusText}`,
      detail,
    };
    throw err;
  }

 
  const data = (await parseJsonSafe(res)) as T;
  return data;
}

// 常用快捷
export const http = {
  get: <T>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { ...options, method: "POST", body }),
};