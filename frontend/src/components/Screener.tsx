"use client";
import { Filter } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

interface ScreenerParams {
    min_eps: string;
    min_roe: string;
    max_pe: string;
    industry: string;
}

interface ScreenerStock {
    symbol: string;
    name: string;
    industry: string;
    price: number | null;
    eps: number | null;
    roe: number | null;
    pe: number | null;
    pb: number | null;
    momentum_60d: number | null;
    score: number;
    rating_explanation: string;
    data_completeness: number;
    price_date: string | null;
    financial_as_of: string | null;
    financial_period_type: string | null;
}

const EMPTY_PARAMS: ScreenerParams = {
    min_eps: '',
    min_roe: '',
    max_pe: '',
    industry: ''
};

const momentumColor = (value: number | null) => {
    if (value === null) return 'text-gray-400';
    if (value > 0) return 'text-green-400';
    if (value < 0) return 'text-red-400';
    return 'text-gray-400';
};

export default function Screener({ onSelectStock }: { onSelectStock: (symbol: string) => void }) {
    const [data, setData] = useState<ScreenerStock[]>([]);
    const [loading, setLoading] = useState(false);
    const [params, setParams] = useState<ScreenerParams>(EMPTY_PARAMS);

    const fetchScreen = useCallback(async (screenParams: ScreenerParams, template?: string) => {
        setLoading(true);
        try {
            let url = 'http://localhost:8000/api/screener/?';
            if (template) {
                url = `http://localhost:8000/api/screener/templates/${template}`;
            } else {
                const queryParams = new URLSearchParams();
                if (screenParams.min_eps) queryParams.append('min_eps', screenParams.min_eps);
                if (screenParams.min_roe) queryParams.append('min_roe', screenParams.min_roe);
                if (screenParams.max_pe) queryParams.append('max_pe', screenParams.max_pe);
                if (screenParams.industry) queryParams.append('industry', screenParams.industry);
                url += queryParams.toString();
            }

            const res = await fetch(url);
            const json = await res.json();
            setData(json.results || []);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleScreen = (template?: string) => fetchScreen(params, template);

    useEffect(() => {
        void fetchScreen(EMPTY_PARAMS);
    }, [fetchScreen]);

    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Filter className="text-green-400" /> 多因子選股器
                </h2>
            </div>

            <div className="mb-5 rounded-lg border border-blue-500/30 bg-blue-950/30 px-4 py-3 text-sm text-blue-100">
                目前為大型優質股觀察池，不代表完整上市櫃市場；評分依品質、成長、相對估值、動能與風險流動性計算。
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                <div>
                    <label className="block text-sm text-gray-400 mb-1">最低 EPS</label>
                    <input
                        type="number"
                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
                        placeholder="e.g. 2"
                        value={params.min_eps}
                        onChange={(e) => setParams({ ...params, min_eps: e.target.value })}
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400 mb-1">最低 ROE (%)</label>
                    <input
                        type="number"
                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
                        placeholder="e.g. 15"
                        value={params.min_roe}
                        onChange={(e) => setParams({ ...params, min_roe: e.target.value })}
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400 mb-1">本益比 (PE) 低於</label>
                    <input
                        type="number"
                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
                        placeholder="e.g. 15"
                        value={params.max_pe}
                        onChange={(e) => setParams({ ...params, max_pe: e.target.value })}
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400 mb-1">產業類別</label>
                    <select
                        className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white"
                        value={params.industry}
                        onChange={(e) => setParams({ ...params, industry: e.target.value })}
                    >
                        <option value="">全部產業</option>
                        <option value="半導體業">半導體業</option>
                        <option value="電腦及週邊設備業">電腦及週邊設備業</option>
                        <option value="電子零組件業">電子零組件業</option>
                        <option value="通信網路業">通信網路業</option>
                        <option value="航運業">航運業</option>
                    </select>
                </div>
                <div className="flex items-end gap-2">
                    <button
                        onClick={() => handleScreen()}
                        className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-medium flex-1 h-10"
                    >
                        {loading ? '...' : '篩選'}
                    </button>
                </div>
            </div>

            <div className="flex gap-2 mb-6">
                <button onClick={() => handleScreen('high_roe_undervalued')} className="text-sm bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded-full text-gray-300">
                    🔥 模板: 高ROE低估值組合
                </button>
                <button onClick={() => handleScreen('turnaround')} className="text-sm bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded-full text-gray-300">
                    🚀 模板: 轉機潛力股
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead>
                        <tr className="border-b border-gray-700 text-gray-400">
                            <th className="p-2">代號</th>
                            <th className="p-2">名稱</th>
                            <th className="p-2">產業</th>
                            <th className="p-2">當前股價</th>
                            <th className="p-2">EPS</th>
                            <th className="p-2">ROE</th>
                            <th className="p-2">PE / PB</th>
                            <th className="p-2">60日動能</th>
                            <th className="p-2">多因子評分</th>
                            <th className="p-2">資料日期</th>
                            <th className="p-2 text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((stock) => (
                            <tr key={stock.symbol} className="border-b border-gray-700/50 hover:bg-gray-750">
                                <td className="p-2 font-mono text-blue-400">{stock.symbol}</td>
                                <td className="p-2 font-bold">{stock.name}</td>
                                <td className="p-2 text-sm text-gray-400">{stock.industry}</td>
                                <td className="p-2 font-bold text-yellow-400">{stock.price != null ? `$${stock.price}` : '-'}</td>
                                <td className="p-2 text-green-400">{stock.eps ?? '-'}</td>
                                <td className="p-2 text-green-400">{stock.roe != null ? `${stock.roe}%` : '-'}</td>
                                <td className="p-2 font-mono text-purple-400">{stock.pe ?? '-'} / {stock.pb ?? '-'}</td>
                                <td className={`p-2 font-mono ${momentumColor(stock.momentum_60d)}`}>
                                    {stock.momentum_60d != null ? `${stock.momentum_60d}%` : '-'}
                                </td>
                                <td className="p-2">
                                    <div className="flex items-center gap-2">
                                        <div className="w-10 h-10 rounded-full bg-blue-900/50 border border-blue-500 flex items-center justify-center font-bold text-cyan-300">
                                            {stock.score}
                                        </div>
                                        <span className="text-xs text-gray-400 max-w-40 leading-tight">
                                            {stock.rating_explanation}<br />
                                            完整度 {Math.round((stock.data_completeness || 0) * 100)}%
                                        </span>
                                    </div>
                                </td>
                                <td className="p-2 text-xs text-gray-400">
                                    股價 {stock.price_date || '-'}<br />
                                    財務 {stock.financial_as_of || stock.financial_period_type || '-'}
                                </td>
                                <td className="p-2 text-right">
                                    <button
                                        onClick={() => onSelectStock(stock.symbol)}
                                        className="text-white bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded font-medium text-sm transition"
                                    >
                                        進入儀表板
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {data.length === 0 && !loading && (
                            <tr>
                                <td colSpan={11} className="p-4 text-center text-gray-500">沒有符合條件的股票，或尚未執行篩選。</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
