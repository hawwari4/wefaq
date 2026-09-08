import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import ApprovedUserNav from '../components/ApprovedUserNav'
import Button from '../components/Button'
import { getSavedCandidates, removeSavedCandidate } from '../services/matchInteractionService'

export default function SavedCandidatesPage() {
  const navigate = useNavigate()
  const [items, setItems] = useState(null)
  const [busyRef, setBusyRef] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const session = JSON.parse(localStorage.getItem('wefaq_user') || 'null')
    if (!session) return navigate('/login', { replace: true })
    if (session.status !== 'approved') return navigate('/dashboard', { replace: true })
    getSavedCandidates().then((data) => setItems(data.saved || [])).catch((err) => setError(err.message))
  }, [navigate])

  async function remove(candidateRef) {
    setBusyRef(candidateRef)
    setError('')
    try {
      await removeSavedCandidate(candidateRef)
      setItems((current) => current.filter((item) => item.candidate_ref !== candidateRef))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyRef(null)
    }
  }

  return (
    <main dir="rtl" className="mx-auto max-w-2xl px-4 pb-28 pt-7 sm:px-6">
      <header><p className="text-sm text-muted">قائمتك الخاصة للعودة لاحقاً</p><h1 className="mt-1 font-display text-3xl text-teal-700">المرشحون المحفوظون</h1></header>
      {error && <p className="mt-4 rounded-xl bg-brick-100 px-4 py-3 text-sm text-brick-500">{error}</p>}
      {!items ? <p className="py-16 text-center text-muted">جاري تحميل المحفوظات...</p> : items.length === 0 ? (
        <div className="py-16 text-center"><p className="font-display text-xl text-teal-700">لم تحفظ أي مرشح بعد.</p><p className="mt-2 text-sm text-muted">يمكنك حفظ المرشحين من صفحة المرشحين المناسبين.</p><Button className="mt-5" onClick={() => navigate('/matches')}>استعراض المرشحين</Button></div>
      ) : <div className="mt-6 space-y-3">{items.map((item) => item.available ? (
        <article key={item.id} className="rounded-2xl border border-teal-100 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3"><div><h2 className="font-display text-xl text-teal-700">مرشح محفوظ</h2><p className="mt-2 text-sm text-ink">{item.candidate.age} سنة · {item.candidate.country || 'بلد الإقامة غير محدد'} · {item.candidate.profession || 'المهنة غير محددة'}</p></div>{item.compatibility_percentage != null && <span className="shrink-0 rounded-full bg-gold-100 px-3 py-1 text-sm text-gold-700">{item.compatibility_percentage}%</span>}</div>
          {item.candidate.profile_description && <p className="mt-3 line-clamp-2 text-sm leading-6 text-muted">{item.candidate.profile_description}</p>}
          <div className="mt-4 flex gap-2"><Button className="px-4 py-2 text-sm" onClick={() => navigate(`/matches?candidate=${item.candidate.candidate_ref}`)}>عرض الملف</Button><Button variant="secondary" className="px-4 py-2 text-sm" disabled={busyRef === item.candidate.candidate_ref} onClick={() => remove(item.candidate.candidate_ref)}>إزالة</Button></div>
        </article>
      ) : <article key={item.id} className="rounded-2xl border border-teal-100 bg-white p-5"><h2 className="font-display text-lg text-teal-700">مرشح غير متاح</h2><p className="mt-2 text-sm text-muted">لم يعد هذا الملف متاحاً للعرض.</p><Button variant="secondary" className="mt-4 px-4 py-2 text-sm" disabled={busyRef === item.candidate_ref} onClick={() => remove(item.candidate_ref)}>إزالة</Button></article>)}</div>}
      <ApprovedUserNav />
    </main>
  )
}
