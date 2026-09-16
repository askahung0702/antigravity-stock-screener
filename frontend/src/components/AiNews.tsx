"use client";
import React, { useState } from 'react';
import { Info, TrendingUp, AlertTriangle } from 'lucide-react';

interface NewsItem {
  id: number;
  date: string | null;
  title: string;
  original_content: string;
  ai_sentiment: 'Positive' | 'Neutral' | 'Negative' | string;
  ai_summary: string[];
}

interface NewsResponse {
  symbol: string;
  news: NewsItem[];
}

export default function AiNews({ symbol }: { symbol: string }) {
  const [data, setData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchNews = async () => {
    if (!symbol) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`http://localhost:8000/api/news/${symbol}`);
      if (!res.ok) throw new Error('News data not found');
      const json = await res.json();
      setData(json);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'News request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Info className="text-blue-400" /> AI 消息面總結
        </h2>
        <button 
          onClick={fetchNews}
          disabled={loading || !symbol}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-medium disabled:opacity-50"
        >
          {loading ? '分析中...' : '載入並分析新聞'}
        </button>
      </div>

      {!symbol && <p className="text-gray-400 text-center py-8">請先選擇或輸入股票代號</p>}
      
      {error && <p className="text-red-400">{error}</p>}

      {data && data.news && data.news.length === 0 && (
        <p className="text-gray-400">目前沒有關於此股票的即時新聞。</p>
      )}

      <div className="space-y-4">
        {data?.news?.map((item) => (
          <div key={item.id} className="bg-gray-900 p-4 rounded-lg border border-gray-700">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-lg">{item.title}</h3>
              <span className={`px-2 py-1 text-xs rounded font-bold ${
                item.ai_sentiment === 'Positive' ? 'bg-green-900 text-green-300' :
                item.ai_sentiment === 'Negative' ? 'bg-red-900 text-red-300' :
                'bg-gray-700 text-gray-300'
              }`}>
                {item.ai_sentiment === 'Positive' && <TrendingUp className="inline w-3 h-3 mr-1"/>}
                {item.ai_sentiment === 'Negative' && <AlertTriangle className="inline w-3 h-3 mr-1"/>}
                {item.ai_sentiment}
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">{item.date}</p>
            
            <div className="bg-gray-800 p-3 rounded text-sm text-gray-300 mb-3">
              <p className="font-medium text-white mb-2">🤖 AI 重點摘要：</p>
              <ul className="list-disc pl-5 space-y-1">
                {item.ai_summary.map((sum: string, idx: number) => (
                  <li key={idx}>{sum}</li>
                ))}
              </ul>
            </div>
            
            <details className="text-xs text-gray-400">
              <summary className="cursor-pointer hover:text-gray-300">檢視原始內文 (Grounding Source)</summary>
              <p className="mt-2 p-2 bg-black rounded whitespace-pre-wrap">{item.original_content}</p>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
