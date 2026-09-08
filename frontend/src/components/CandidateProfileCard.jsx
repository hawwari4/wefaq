const PROFILE_FIELDS = [
  ['العمر', 'age', ' سنة'],
  ['الجنسية', 'nationality', ''],
  ['بلد الإقامة', 'country', ''],
  ['المهنة', 'profession', ''],
  ['الحالة الاجتماعية', 'marital_status', ''],
  ['موعد الزواج المفضل', 'marriage_timeline', ''],
]

export default function CandidateProfileCard({ candidate, compatibility, position, children }) {
  return (
    <article className="overflow-hidden rounded-3xl border border-teal-100 bg-white shadow-sm">
      <div className="relative bg-teal-700 px-5 py-5 text-linen sm:px-6">
        <div className="absolute inset-0 opacity-10 mashrabiya-bg" />
        <div className="relative flex items-center gap-4">
          <div aria-label="صورة المرشح مخفية" className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-linen/40 bg-linen/10 text-center text-xs leading-tight">الصورة<br />مخفية</div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-linen/75">مرشح مناسب</p>
            <div className="mt-1 flex items-end gap-2">
              <strong className="font-display text-4xl leading-none">{compatibility == null ? '—' : `${compatibility}%`}</strong>
              <span className="pb-1 text-xs text-linen/75">نسبة توافق إرشادية</span>
            </div>
          </div>
          {position && <span className="rounded-full bg-linen/10 px-3 py-1 text-xs">{position}</span>}
        </div>
      </div>

      <div className="p-5 sm:p-6">
        <dl className="grid grid-cols-2 gap-x-5 gap-y-4">
          {PROFILE_FIELDS.map(([label, key, suffix]) => candidate?.[key] != null && candidate[key] !== '' ? (
            <div key={key} className="border-b border-teal-50 pb-3">
              <dt className="text-xs text-muted">{label}</dt>
              <dd className="mt-1 font-medium text-ink">{candidate[key]}{suffix}</dd>
            </div>
          ) : null)}
        </dl>

        {candidate?.profile_description && (
          <section className="mt-5 border-r-2 border-gold-500 pr-4">
            <h2 className="font-display text-xl text-teal-700">نبذة عن المرشح</h2>
            <p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-ink">{candidate.profile_description}</p>
          </section>
        )}

        {children}
      </div>
    </article>
  )
}
