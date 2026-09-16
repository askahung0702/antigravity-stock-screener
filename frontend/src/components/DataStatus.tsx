"use client";

import { AlertTriangle, Database, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';

interface PipelineRun {
    job_name: string;
    status: string;
    finished_at: string | null;
    error_message: string | null;
}

interface PipelineStatus {
    active_stock_count: number;
    latest_price_date: string | null;
    latest_financial_as_of: string | null;
    latest_institutional_date: string | null;
    latest_news_date: string | null;
    latest_runs: PipelineRun[];
}

export default function DataStatus() {
    const [status, setStatus] = useState<PipelineStatus | null>(null);
    const [error, setError] = useState('');

    useEffect(() => {
        const loadStatus = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/system/pipeline-status');
                if (!response.ok) throw new Error('無法取得資料管線狀態');
                setStatus(await response.json());
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : '資料狀態讀取失敗');
            }
        };
        void loadStatus();
    }, []);

    if (error) {
        return (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-950/30 px-4 py-3 text-sm text-red-200">
                <AlertTriangle className="h-4 w-4" /> {error}
            </div>
        );
    }
    if (!status) {
        return (
            <div className="flex items-center gap-2 text-sm text-gray-500">
                <RefreshCw className="h-4 w-4 animate-spin" /> 讀取資料狀態…
            </div>
        );
    }

    const failedJobs = status.latest_runs.filter((run) => run.status === 'failed');
    return (
        <div className={`rounded-lg border px-4 py-3 text-sm ${failedJobs.length ? 'border-amber-500/40 bg-amber-950/30' : 'border-gray-700 bg-gray-900/60'}`}>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
                <span className="flex items-center gap-2 font-medium text-gray-200">
                    <Database className="h-4 w-4 text-blue-400" /> 資料狀態
                </span>
                <span className="text-gray-400">觀察池 {status.active_stock_count} 檔</span>
                <span className="text-gray-400">股價 {status.latest_price_date || '尚無有效日期'}</span>
                <span className="text-gray-400">財務 {status.latest_financial_as_of || '尚無有效日期'}</span>
                <span className="text-gray-400">法人 {status.latest_institutional_date || '尚無正式資料'}</span>
                <span className="text-gray-400">新聞 {status.latest_news_date || '尚無有效日期'}</span>
                {failedJobs.length > 0 && (
                    <span className="flex items-center gap-1 text-amber-300">
                        <AlertTriangle className="h-4 w-4" /> {failedJobs.length} 個工作最近執行失敗
                    </span>
                )}
            </div>
        </div>
    );
}
