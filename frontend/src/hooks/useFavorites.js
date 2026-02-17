import { useState, useEffect } from 'react'

const STORAGE_KEY = 'ispas_favorites'
const MAX_FAVORITES = 20

function useFavorites() {
  const [favorites, setFavorites] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : []
    } catch (error) {
      console.error('즐겨찾기 로드 실패:', error)
      return []
    }
  })

  // localStorage 동기화
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites))
    } catch (error) {
      console.error('즐겨찾기 저장 실패:', error)
    }
  }, [favorites])

  const addFavorite = (ticker) => {
    if (favorites.length >= MAX_FAVORITES) {
      alert(`즐겨찾기는 최대 ${MAX_FAVORITES}개까지 추가할 수 있습니다.`)
      return false
    }
    if (!favorites.includes(ticker)) {
      setFavorites([...favorites, ticker])
      return true
    }
    return false
  }

  const removeFavorite = (ticker) => {
    setFavorites(favorites.filter(t => t !== ticker))
  }

  const toggleFavorite = (ticker) => {
    if (favorites.includes(ticker)) {
      removeFavorite(ticker)
      return false
    } else {
      return addFavorite(ticker)
    }
  }

  const isFavorite = (ticker) => {
    return favorites.includes(ticker)
  }

  return {
    favorites,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isFavorite
  }
}

export default useFavorites
