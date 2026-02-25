"use client";
import { Filter } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Screener({ onSelectStock }: { onSelectStock: (symbol: string) => void }) {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [params, setParams] = useState({
        min_eps: '',
        min_roe: '',
        max_pe: '',
        industry: ''
    });

    const handleScreen = async (template?: string) => {
        setLoading(true);
        try {
            let url = 'http://localhost:8000/api/screener/?';
            if (template) {
                url = `http://localhost:8000/api/screener/templates/${template}`;
            } else {
                const queryParams = new URLSearchParams();
                if (params.min_eps) queryParams.append('min_eps', params.min_eps);
                if (params.min_roe) queryParams.append('min_roe', params.min_roe);
                if (params.max_pe) queryParams.append('max_pe', params.max_pe);
                if (params.industry) queryParams.append('industry', params.industry);
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
    };

    useEffect(() => {
        handleScreen();
    }, []);

    return (
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Filter className="text-green-400" /> 高效選股器
                </h2>
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
                            <th className="p-2">PE</th>
                            <th className="p-2">投資價值評分</th>
                            <th className="p-2 text-right">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((stock: any) => (
                            <tr key={stock.symbol} className="border-b border-gray-700/50 hover:bg-gray-750">
                                <td className="p-2 font-mono text-blue-400">{stock.symbol}</td>
                                <td className="p-2 font-bold">{stock.name}</td>
                                <td className="p-2 text-sm text-gray-400">{stock.industry}</td>
                                <td className="p-2 font-bold text-yellow-400">${stock.price}</td>
                                <td className="p-2 text-green-400">{stock.eps}</td>
                                <td className="p-2 text-green-400">{stock.roe}%</td>
                                <td className="p-2 font-mono text-purple-400">{stock.pe}</td>
                                <td className="p-2">
                                    <div className="flex items-center gap-2">
                                        <div className="w-10 h-10 rounded-full bg-blue-900/50 border border-blue-500 flex items-center justify-center font-bold text-cyan-300">
                                            {stock.score}
                                        </div>
                                        <span className="text-xs text-gray-400 max-w-40 leading-tight">
                                            {stock.rating_explanation}
                                        </span>
                                    </div>
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
                                <td colSpan={9} className="p-4 text-center text-gray-500">沒有符合條件的股票，或尚未執行篩選。</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
