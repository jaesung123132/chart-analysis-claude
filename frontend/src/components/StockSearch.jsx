import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import useDebounce from '../hooks/useDebounce'

function StockSearch({ onSelect, initialValue = '' }) {
  const [inputValue, setInputValue] = useState(initialValue)
  const [results, setResults] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [activeIndex, setActiveIndex] = useState(-1)

  const debouncedQuery = useDebounce(inputValue, 300)
  const containerRef = useRef(null)

  // 검색 API 호출
  useEffect(() => {
    if (!debouncedQuery || debouncedQuery.trim().length < 1) {
      setResults([])
      setIsOpen(false)
      return
    }

    const fetchResults = async () => {
      setLoading(true)
      try {
        const res = await axios.get(`/api/v1/search?q=${encodeURIComponent(debouncedQuery)}&limit=10`)
        if (res.data.success) {
          setResults(res.data.data.results)
          setIsOpen(res.data.data.results.length > 0)
          setActiveIndex(-1)
        }
      } catch (err) {
        console.error('검색 실패:', err)
        setResults([])
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [debouncedQuery])

  // 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (stock) => {
    setInputValue(stock.ticker)
    setIsOpen(false)
    setResults([])
    onSelect(stock.ticker)
  }

  const handleKeyDown = (e) => {
    if (!isOpen) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex(prev => Math.min(prev + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (activeIndex >= 0 && results[activeIndex]) {
        handleSelect(results[activeIndex])
      } else if (results.length > 0) {
        handleSelect(results[0])
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative flex-1">
      <label className="block text-sm font-medium text-gray-700 mb-2">
        종목 검색
      </label>
      <div className="relative">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="한글 또는 영문 입력 (예: 테슬라, TSLA, Apple)"
        />
        {/* 로딩 스피너 */}
        {loading && (
          <div className="absolute right-3 top-2.5">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>

      {/* 드롭다운 */}
      {isOpen && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {results.map((stock, index) => (
            <div
              key={stock.ticker}
              onClick={() => handleSelect(stock)}
              className={`px-4 py-3 cursor-pointer flex items-center justify-between hover:bg-blue-50 ${
                index === activeIndex ? 'bg-blue-50' : ''
              } ${index > 0 ? 'border-t border-gray-100' : ''}`}
            >
              <div className="flex items-center gap-3">
                {/* 티커 배지 */}
                <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-bold rounded">
                  {stock.ticker}
                </span>
                {/* 한글명 */}
                <div>
                  <div className="text-sm font-medium text-gray-900">{stock.nameKr}</div>
                  <div className="text-xs text-gray-500">{stock.nameEn}</div>
                </div>
              </div>
              {/* 시장 */}
              <span className="text-xs text-gray-400 shrink-0">{stock.market}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default StockSearch
