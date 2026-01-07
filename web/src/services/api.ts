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

export interface briefingRow {
    ts: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

export interface briefingRespones {
    code: string;
    rows: briefingRow[];
    error?: string;
}

export interface MarketSummary {
    symbol: string;
    trend:{
        short: 'up' | 'down' | 'range';
        medium: 'up' | 'down' | 'range';
    };
}

export const api = {
    getKline: (symbol: string) => {
        return http.get<any, KlineData[]>(`/api/kline/${symbol}`);
    },
    getAiBriefing: (code: string) => {
        return http.get<any, briefingRespones[]>(`/api/ai-briefing/${code}`);
    },

};