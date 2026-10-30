import { API_URL } from '@/core/constants/api-url'

// FastAPI 오류 응답({ detail: "..." })에서 화면에 보여줄 문구를 꺼낸다
export async function requestError(res: Response): Promise<Error> {
  const err = await res.json().catch(() => ({}))
  return new Error(typeof err.detail === 'string' ? err.detail : '요청에 실패했어요.')
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`)
  if (!res.ok) throw await requestError(res)
  return res.json()
}
