import { NavLink } from 'react-router-dom'

const ITEMS = [
  ['/matches', 'المرشحون', '◇'],
  ['/compatibility-requests', 'الطلبات', '⇄'],
  ['/saved-candidates', 'المحفوظات', '♡'],
  ['/account', 'الحساب', '○'],
]

export default function ApprovedUserNav() {
  return (
    <nav aria-label="التنقل الرئيسي" dir="rtl" className="fixed inset-x-3 bottom-3 z-40 mx-auto max-w-xl rounded-2xl border border-teal-100 bg-white/95 p-1.5 shadow-lg backdrop-blur">
      <div className="grid grid-cols-4 gap-1">
        {ITEMS.map(([to, label, icon]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `flex min-h-14 flex-col items-center justify-center rounded-xl px-1 text-xs transition-colors ${isActive ? 'bg-teal-50 font-bold text-teal-700' : 'text-muted hover:bg-teal-50'}`}>
            <span aria-hidden="true" className="text-lg leading-none">{icon}</span>
            <span className="mt-1">{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
