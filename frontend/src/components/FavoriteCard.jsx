import React from 'react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

function FavoriteCard({ stock, onClick }) {
  const { ticker, currentPrice, changePercent, changeAmount, prices } = stock
  const isPositive = changePercent >= 0

  // 미니 차트 데이터
  const chartData = prices.map(p => ({ value: p.close }))

  return (
    <div
      onClick={() => onClick(ticker)}
      className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
    >
      {/* 티커 */}
      <div className="font-bold text-lg text-gray-900 mb-2">{ticker}</div>

      {/* 현재가 */}
      <div className="text-2xl font-bold text-gray-900 mb-1">
        ${currentPrice.toFixed(2)}
      </div>

      {/* 등락률 */}
      <div className={`text-sm font-medium mb-3 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? '+' : ''}{changeAmount.toFixed(2)} ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
      </div>

      {/* 미니 차트 */}
      <div className="h-12">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <Line
              type="monotone"
              dataKey="value"
              stroke={isPositive ? '#10b981' : '#ef4444'}
              strokeWidth={1.5}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default FavoriteCard
