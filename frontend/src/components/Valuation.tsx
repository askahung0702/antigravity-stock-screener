"use client";
import { useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function Valuation({ symbol }: { symbol: string }) {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const fetchValuation = async () => {
        if (!symbol) return;
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`http://localhost:8000/api/valuation/${symbol}`);
            if (!res.ok) throw new Error('Valuation data not found or insufficient');
            const json = await res.json();
            setData(json);
        } catch (err: any) {
            setError(err.message);
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
                        </div>
                        <div className="bg-gray-700 p-4 rounded text-center">
                            <p className="text-gray-400 text-sm">目前 EPS / 淨值</p>
                            <p className="text-xl font-bold">{data.eps} / {data.bvps}</p>
                        </div>
                        <div className="bg-gray-700 p-4 rounded text-center">
                            <p className="text-gray-400 text-sm">葛拉漢數字 (防禦價值)</p>
                            <p className="text-2xl font-bold text-blue-400">{data.graham_number}</p>
                        </div>
                        <div className={`p-4 rounded text-center ${data.valuation_status.includes('低估') ? 'bg-green-900/50 border border-green-500' : data.valuation_status.includes('高估') ? 'bg-red-900/50 border border-red-500' : 'bg-yellow-900/50 border border-yellow-500'}`}>
                            <p className="text-gray-300 text-sm">當前估值判定</p>
                            <p className="text-2xl font-bold">{data.valuation_status}</p>
                        </div>
                    </div>

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
                                <Line type="monotone" dataKey="pe_band_10" stroke="#10B981" strokeWidth={1} strokeDasharray="5 5" name="10x PE" dot={false} />
                                <Line type="monotone" dataKey="pe_band_15" stroke="#3B82F6" strokeWidth={1} strokeDasharray="5 5" name="15x PE" dot={false} />
                                <Line type="monotone" dataKey="pe_band_20" stroke="#F59E0B" strokeWidth={1} strokeDasharray="5 5" name="20x PE" dot={false} />
                                <Line type="monotone" dataKey="pe_band_25" stroke="#EF4444" strokeWidth={1} strokeDasharray="5 5" name="25x PE" dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
}
