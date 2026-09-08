import { apiDelete, apiGet, apiPost, apiPut } from './api'

export const getCompatibilityRequests = () => apiGet('/matching/requests')
export const sendCompatibilityRequest = (candidateId) => apiPost('/matching/requests', { candidate_id: candidateId })
export const respondToCompatibilityRequest = (requestId, status) => apiPut(`/matching/requests/${requestId}`, { status })

export const getSavedCandidates = () => apiGet('/matching/saved')
export const saveCandidate = (candidateId) => apiPost('/matching/saved', { candidate_id: candidateId })
export const removeSavedCandidate = (candidateId) => apiDelete(`/matching/saved/${candidateId}`)
