"use client";
import { DollarSign, TrendingUp, Trophy } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Ranking({ onSelectStock }: { onSelectStock: (symbol: string) => void }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchRanking = async () => {
        setLoading(true);
        try {
            // Hardcode parameters for: Undervalued Growth (ROE >= 10, EPS >= 1, PE <= 15)
            const response = await fetch('http://127.0.0.1:8000/api/screener/?min_roe=10&min_eps=1&max_pe=15&limit=10');
            const result = await response.json();
            // Since the API already sorts by Investment Value Score, top 3 are the absolute best
            setData(result.results || []);
        } catch (error) {
            console.error("Failed to fetch ranking", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRanking();
    }, []);

    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex items-center gap-3 mb-6 border-b border-gray-700 pb-4">
                <Trophy className="w-6 h-6 text-yellow-500" />
                <div>
                    <h2 className="text-xl font-bold text-white">低估成長潛力榜單 (Top 10)</h2>
                    <p className="text-sm text-gray-400">嚴選 ROE &gt; 10%、持續獲利且目前本益比低於 15 倍的優質企業</p>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center p-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                </div>
            ) : (
                <div className="space-y-4">
                    {data.map((stock: any, index: number) => (
                        <div
                            key={stock.symbol}
                            className={`flex flex-col md:flex-row items-center justify-between p-4 rounded-lg border ${index === 0 ? 'bg-yellow-900/20 border-yellow-700/50' :
                                index === 1 ? 'bg-gray-400/10 border-gray-500/50' :
                                    index === 2 ? 'bg-orange-900/20 border-orange-700/50' :
                                        'bg-gray-900/50 border-gray-800'
                                } hover:bg-gray-700 transition duration-200`}
                        >
                            <div className="flex items-center gap-4 w-full md:w-1/3 mb-4 md:mb-0">
                                <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold text-lg ${index === 0 ? 'bg-yellow-500 text-black shadow-[0_0_15px_rgba(234,179,8,0.5)]' :
                                    index === 1 ? 'bg-gray-300 text-black' :
                                        index === 2 ? 'bg-orange-400 text-black' :
                                            'bg-gray-800 text-gray-400 border border-gray-600'
                                    }`}>
                                    {index + 1}
                                </div>
                                <div>
                                    <div className="text-lg font-bold text-white flex items-center gap-2">
                                        {stock.name}
                                        <span className="text-xs text-blue-400 font-mono bg-blue-900/30 px-2 py-0.5 rounded">
                                            {stock.symbol}
                                        </span>
                                    </div>
                                    <div className="text-sm text-gray-400">{stock.industry}</div>
                                </div>
                            </div>

                            <div className="flex items-center justify-around w-full md:w-1/2 gap-2 text-center mb-4 md:mb-0">
                                <div>
                                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1"><DollarSign className="w-3 h-3" /> 當前股價</div>
                                    <div className="font-bold text-yellow-400">${stock.price}</div>
                                </div>
                                <div className="border-l border-gray-700 h-8"></div>
                                <div>
                                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1"><TrendingUp className="w-3 h-3" /> EPS</div>
                                    <div className="font-bold text-green-400">{stock.eps}</div>
                                </div>
                                <div className="border-l border-gray-700 h-8"></div>
                                <div>
                                    <div className="text-xs text-gray-400">ROE</div>
                                    <div className="font-bold text-green-400">{stock.roe}%</div>
                                </div>
                                <div className="border-l border-gray-700 h-8"></div>
                                <div>
                                    <div className="text-xs text-gray-400">本益比 (PE)</div>
                                    <div className="font-bold font-mono text-purple-400">{stock.pe}</div>
                                </div>
                            </div>

                            <div className="w-full md:w-auto flex justify-end">
                                <button
                                    onClick={() => onSelectStock(stock.symbol)}
                                    className={`px-6 py-2 rounded-lg font-medium transition ${index < 3
                                        ? 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white shadow-lg'
                                        : 'bg-gray-700 hover:bg-gray-600 text-white'
                                        }`}
                                >
                                    進入分析
                                </button>
                            </div>
                        </div>
                    ))}

                    {data.length === 0 && (
                        <div className="text-center p-8 text-gray-500">
                            目前市場中沒有符合嚴格低估成長條件的股票。
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
