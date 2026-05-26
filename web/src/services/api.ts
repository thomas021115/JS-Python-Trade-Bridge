import http from '@/services/http';

//K 線資料介面 (對應 /api/kline/{symbol})
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

//AI 摘要介面 (對應 /api/ai-briefing/{code})

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
    trend:{
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

// 獲取python裡的輸出
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
    getStockPositions: () => {
        return http.get<any, StockPositionsResponse>('/api/account/stock-positions');
    }

};
