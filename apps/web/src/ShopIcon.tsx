export type ShopIconName = 'today' | 'sell' | 'stock' | 'reports' | 'profile' | 'mic' | 'spark' | 'receipt' | 'wifi'

/** Small, consistent shop icons; decorative alongside their visible labels. */
export function ShopIcon({ name, className = '' }: { name: ShopIconName; className?: string }) {
  const paths: Record<ShopIconName, React.ReactNode> = {
    today: <><path d="m3 10 9-7 9 7v11h-6v-7H9v7H3z" /></>,
    sell: <path d="M12 4v16M4 12h16" />,
    stock: <><path d="m3 7 9-4 9 4v10l-9 4-9-4zM3 7l9 4 9-4M12 11v10M7 5l10 4" /></>,
    reports: <><path d="M4 20V11h4v9M10 20V4h4v16M16 20V8h4v12" /></>,
    profile: <><circle cx="12" cy="7" r="4" /><path d="M4 21v-2a8 8 0 0 1 16 0v2z" /></>,
    mic: <><rect x="8" y="2" width="8" height="13" rx="4" /><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8" /></>,
    spark: <path d="m12 2 2.8 7.2L22 12l-7.2 2.8L12 22l-2.8-7.2L2 12l7.2-2.8z" />,
    receipt: <><path d="M6 3h12v19l-3-2-3 2-3-2-3 2zM9 7h6M9 11h6M9 15h4" /></>,
    wifi: <><path d="M3 8a14 14 0 0 1 18 0M6 12a9 9 0 0 1 12 0M9 16a4.5 4.5 0 0 1 6 0" /><circle cx="12" cy="20" r=".7" /></>,
  }
  return <svg className={`shop-icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}
