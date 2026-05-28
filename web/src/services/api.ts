import http from '@/services/http';

export interface KlineData {
  ts: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  RSI?: number;
  MA5?: number;
  MA20?: number;
}

export interface BriefingRow {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface BriefingResponse {
  code: string;
  rows: BriefingRow[];
  error?: string;
}

export interface MarketSummary {
  symbol: string;
  trend: {
    short: 'up' | 'down' | 'range';
    medium: 'up' | 'down' | 'range';
  };
}

export interface AiReportResponse {
  code: string;
  report?: string;
  error?: string;
  saved?: boolean;
  report_id?: number;
  daily_price_saved?: number;
  technical_snapshot_saved?: number;
  source?: string;
  data_source?: 'database' | 'shioaji' | 'mixed' | 'none';
  start_date?: string;
  end_date?: string;
  timeframe?: string;
  db_rows_used?: number;
  shioaji_rows_fetched?: number;
  data_quality_warning?: boolean;
  message?: string;
}

export interface SyncResponse {
  success: boolean;
  symbol: string;
  start_date?: string;
  end_date?: string;
  fetched_rows?: number;
  saved_1m_rows?: number;
  saved_1d_rows?: number;
  saved_1w_rows?: number;
  technical_snapshot_1d_saved?: number;
  technical_snapshot_1w_saved?: number;
  elapsed_seconds?: number;
  error?: string;
  message?: string;
}

export interface SyncCoverageRow {
  date: string;
  is_trading_day: boolean;
  db_count: number;
  fetched_count: number;
  kbar_count: number;
  source: string;
  status: string;
  fetch_attempted: boolean;
}

export interface SyncStatusResponse {
  success: boolean;
  symbol: string;
  start_date?: string;
  end_date?: string;
  timeframe?: string;
  needs_sync?: boolean;
  can_sync_once?: boolean;
  max_sync_days?: number;
  range_days?: number;
  missing_dates?: string[];
  coverage?: SyncCoverageRow[];
  error?: string;
  message?: string;
}

export interface StockPosition {
  id: number;
  code: string;
  name?: string | null;
  direction?: string | null;
  quantity: number;
  yd_quantity: number;
  price: number;
  last_price: number;
  pnl: number;
  pnl_rate: number;
  market_value: number;
  cond?: string | null;
}

export interface StockPositionsResponse {
  success: boolean;
  source: 'shioaji';
  count?: number;
  symbols?: string[];
  positions?: StockPosition[];
  error?: string;
}

export const api = {
  getKline: (symbol: string) => {
    return http.get<any, KlineData[]>(`/api/kline/${symbol}`);
  },
  getAiBriefing: (code: string) => {
    return http.get<any, BriefingResponse>(`/api/ai-briefing/${code}`);
  },
  getAiReport: (code: string, startDate?: string, endDate?: string) => {
    return http.get<any, AiReportResponse>(`/api/ai-report/${code}`, {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
  },
  syncStockData: (symbol: string, startDate?: string, endDate?: string) => {
    return http.post<any, SyncResponse>(`/api/sync/${symbol}`, null, {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
  },
  getSyncStatus: (symbol: string, startDate?: string, endDate?: string) => {
    return http.get<any, SyncStatusResponse>(`/api/sync-status/${symbol}`, {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
  },
  getStockPositions: () => {
    return http.get<any, StockPositionsResponse>('/api/account/stock-positions');
  },
};
