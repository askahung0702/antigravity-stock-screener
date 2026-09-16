"use client";
import { useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

interface PeBand {
    key: string;
    label: string;
    multiple: number;
}

interface ValuationData {
    latest_price: number;
    price_date: string | null;
    financial_as_of: string | null;
    financial_period_type: string | null;
    eps: number | null;
    bvps: number | null;
    graham_number: number | null;
    valuation_status: string;
    data_quality_warnings: string[];
    pe_bands: PeBand[];
    river_data: Array<Record<string, string | number | null>>;
}

export default function Valuation({ symbol }: { symbol: string }) {
    const [data, setData] = useState<ValuationData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const bandColors = ['#10B981', '#22C55E', '#3B82F6', '#F59E0B', '#EF4444'];

    const fetchValuation = async () => {
        if (!symbol) return;
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`http://localhost:8000/api/valuation/${symbol}`);
            if (!res.ok) throw new Error('Valuation data not found or insufficient');
            const json = await res.json();
            setData(json);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Valuation request failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold">基本面估值分析</h2>
                <button
                    onClick={fetchValuation}
                    disabled={loading || !symbol}
                    className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded font-medium disabled:opacity-50"
                >
                    {loading ? '計算中...' : '載入估值模型'}
                </button>
            </div>

            {!symbol && <p className="text-gray-400 text-center py-8">請先選擇或輸入股票代號</p>}
            {error && <p className="text-red-400">{error}</p>}

            {data && (
                <div className="space-y-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-700 p-4 rounded text-center">
                            <p className="text-gray-400 text-sm">最新收盤價</p>
                            <p className="text-2xl font-bold">{data.latest_price}</p>
                            <p className="text-xs text-gray-400 mt-1">{data.price_date || '日期未知'}</p>
                        </div>
                        <div className="bg-gray-700 p-4 rounded text-center">
                            <p className="text-gray-400 text-sm">目前 EPS / 淨值</p>
                            <p className="text-xl font-bold">{data.eps ?? '-'} / {data.bvps ?? '-'}</p>
                            <p className="text-xs text-gray-400 mt-1">{data.financial_as_of || data.financial_period_type || '期別未知'}</p>
                        </div>
                        <div className="bg-gray-700 p-4 rounded text-center">
                            <p className="text-gray-400 text-sm">葛拉漢數字 (防禦價值)</p>
                            <p className="text-2xl font-bold text-blue-400">{data.graham_number ?? '-'}</p>
                        </div>
                        <div className={`p-4 rounded text-center ${data.valuation_status.includes('偏低') ? 'bg-green-900/50 border border-green-500' : data.valuation_status.includes('偏高') ? 'bg-red-900/50 border border-red-500' : 'bg-yellow-900/50 border border-yellow-500'}`}>
                            <p className="text-gray-300 text-sm">當前估值判定</p>
                            <p className="text-2xl font-bold">{data.valuation_status}</p>
                        </div>
                    </div>

                    {data.data_quality_warnings?.length > 0 && (
                        <div className="rounded-lg border border-amber-500/40 bg-amber-950/30 p-4 text-sm text-amber-100">
                            <p className="font-semibold mb-2">資料品質提醒</p>
                            <ul className="list-disc pl-5 space-y-1">
                                {data.data_quality_warnings.map((warning: string) => <li key={warning}>{warning}</li>)}
                            </ul>
                        </div>
                    )}

                    <div className="bg-gray-900 p-4 rounded-xl border border-gray-700 h-[400px]">
                        <h3 className="text-sm text-gray-400 mb-2">本益比河流圖 (PE River)</h3>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data.river_data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="date" stroke="#9CA3AF" tick={{ fontSize: 12 }} />
                                <YAxis stroke="#9CA3AF" domain={['auto', 'auto']} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                                    itemStyle={{ color: '#E5E7EB' }}
                                />
                                <Legend />
                                <Line type="monotone" dataKey="price" stroke="#fff" strokeWidth={3} name="股價" dot={false} />
                                {data.pe_bands?.map((band, index: number) => (
                                    <Line
                                        key={band.key}
                                        type="monotone"
                                        dataKey={band.key}
                                        stroke={bandColors[index % bandColors.length]}
                                        strokeWidth={1}
                                        strokeDasharray="5 5"
                                        name={band.label}
                                        dot={false}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
}
