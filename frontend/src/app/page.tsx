"use client";
import AiNews from '@/components/AiNews';
import Ranking from '@/components/Ranking';
import Screener from '@/components/Screener';
import Valuation from '@/components/Valuation';
import { Activity, LayoutList, Trophy } from 'lucide-react';
import { useState } from 'react';

export default function Home() {
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'screener' | 'ranking'>('screener');

  return (
    <main className="min-h-screen bg-gray-950 text-white p-6 pb-20 font-sans">
      <header className="mb-8 border-b border-gray-800 pb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Antigravity Stock</h1>
            <p className="text-sm text-gray-400 mt-1">台股價值投資與動能分析系統</p>
          </div>
        </div>

        {selectedStock && (
          <div className="bg-blue-900/40 border border-blue-500/30 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-300 mr-2">目前分析標的:</span>
            <span className="text-xl font-bold font-mono text-blue-400">{selectedStock}</span>
            <button
              onClick={() => setSelectedStock('')}
              className="ml-4 text-sm text-gray-400 hover:text-white underline"
            >
              清除
            </button>
          </div>
        )}
      </header>

      <div className="max-w-7xl mx-auto space-y-8">

        {/* 如果沒有選擇特定股票，顯示選單與對應組件 */}
        {!selectedStock ? (
          <section className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setActiveTab('screener')}
                className={`flex items-center gap-2 px-6 py-3 rounded-t-lg font-bold transition-colors ${activeTab === 'screener'
                    ? 'bg-gray-800 text-white border-t-2 border-blue-500'
                    : 'bg-gray-900 text-gray-500 hover:text-gray-300'
                  }`}
              >
                <LayoutList className="w-5 h-5" /> 全市場掃描
              </button>
              <button
                onClick={() => setActiveTab('ranking')}
                className={`flex items-center gap-2 px-6 py-3 rounded-t-lg font-bold transition-colors ${activeTab === 'ranking'
                    ? 'bg-gray-800 text-yellow-400 border-t-2 border-yellow-500'
                    : 'bg-gray-900 text-gray-500 hover:text-gray-300'
                  }`}
              >
                <Trophy className="w-5 h-5" /> 價值成長潛力榜
              </button>
            </div>

            <div className="bg-gray-950">
              {activeTab === 'screener' ? (
                <Screener onSelectStock={(symbol) => setSelectedStock(symbol)} />
              ) : (
                <Ranking onSelectStock={(symbol) => setSelectedStock(symbol)} />
              )}
            </div>
          </section>
        ) : (
          /* 如果有選擇股票，顯示個股詳細儀表板 */
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="xl:col-span-2 space-y-8">
              <Valuation symbol={selectedStock} />
            </div>
            <div className="xl:col-span-1 space-y-8">
              <AiNews symbol={selectedStock} />
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
