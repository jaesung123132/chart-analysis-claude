import React, { useState, useEffect } from 'react'
import axios from 'axios'
import FavoriteCard from './FavoriteCard'

function FavoriteGrid({ favorites, onStockClick }) {
  const [stocksData, setStocksData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchBatchPrices = async () => {
    if (favorites.length === 0) {
      setStocksData([])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('/api/v1/stocks/batch-prices', {
        tickers: favorites,
        period: '5d'
      })

      if (response.data.success) {
        setStocksData(response.data.data.stocks)
      }
    } catch (err) {
      console.error('즐겨찾기 가격 조회 실패:', err)
      setError('가격 정보를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 초기 로드 및 즐겨찾기 변경 시
  useEffect(() => {
    fetchBatchPrices()
  }, [favorites])

  // 60초마다 자동 갱신
  useEffect(() => {
    if (favorites.length === 0) return

    const interval = setInterval(() => {
      fetchBatchPrices()
    }, 60000) // 60초

    return () => clearInterval(interval)
  }, [favorites])

  if (favorites.length === 0) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <svg
          className="w-12 h-12 text-blue-400 mx-auto mb-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
          />
        </svg>
        <p className="text-blue-800 font-medium mb-1">즐겨찾기가 비어있습니다</p>
        <p className="text-blue-600 text-sm">
          종목을 검색하고 별 아이콘을 눌러 즐겨찾기에 추가하세요
        </p>
      </div>
    )
  }

  if (loading && stocksData.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {favorites.map((ticker) => (
          <div
            key={ticker}
            className="bg-white rounded-lg shadow p-4 animate-pulse"
          >
            <div className="h-6 bg-gray-200 rounded w-20 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-32 mb-1"></div>
            <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="h-12 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p className="text-red-800">{error}</p>
        <button
          onClick={fetchBatchPrices}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          다시 시도
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">즐겨찾기</h2>
        <span className="text-sm text-gray-500">
          {stocksData.length}개 종목 | 60초마다 자동 갱신
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stocksData.map((stock) => (
          <FavoriteCard
            key={stock.ticker}
            stock={stock}
            onClick={onStockClick}
          />
        ))}
      </div>
    </div>
  )
}

export default FavoriteGrid
