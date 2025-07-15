'use client'
import React, { useState, useEffect } from 'react'

interface PullRequest {
  id: number
  title: string
  state: string
  repository: {
    name: string
    full_name: string
    owner: string
  }
  created_at: string
  updated_at: string
  html_url: string
  user: {
    login: string
    avatar_url: string
  }
  comments: number
}

export default function Veda() {
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPullRequests()
  }, [])

  const fetchPullRequests = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/pullrequests?state=all&repo_owner=ryanmello&repo_name=toodeloo')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      setPullRequests(data.items || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('Error fetching pull requests:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Veda - Pull Requests</h1>
        <div>Loading pull requests...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Veda - Pull Requests</h1>
        <div className="text-red-600">Error: {error}</div>
        <button 
          onClick={fetchPullRequests}
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Veda - Pull Requests</h1>
      
      <div className="mb-4">
        <p className="text-gray-600">Found {pullRequests.length} pull requests</p>
      </div>

      {pullRequests.length === 0 ? (
        <div className="text-gray-500">No pull requests found.</div>
      ) : (
        <div className="space-y-4">
          {pullRequests.map((pr) => (
            <div key={pr.id} className="border rounded-lg p-4 bg-white shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-blue-600">
                    <a href={pr.html_url} target="_blank" rel="noopener noreferrer">
                      {pr.title}
                    </a>
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {pr.repository.full_name} • #{pr.id}
                  </p>
                  <div className="flex items-center mt-2 space-x-4">
                    <span className={`px-2 py-1 text-xs rounded ${
                      pr.state === 'open' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {pr.state}
                    </span>
                    <span className="text-sm text-gray-500">
                      {pr.comments} comments
                    </span>
                    <span className="text-sm text-gray-500">
                      Updated: {new Date(pr.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <div className="ml-4">
                  <img 
                    src={pr.user.avatar_url} 
                    alt={pr.user.login}
                    className="w-8 h-8 rounded-full"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
