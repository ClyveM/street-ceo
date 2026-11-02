export const HANDS_FREE_PREFERENCE = 'street-ceo-hands-free-v1'
export function readHandsFreePreference(storage: Pick<Storage, 'getItem'> | undefined, nativeAndroid: boolean): boolean {
  try { const saved = storage?.getItem(HANDS_FREE_PREFERENCE); return saved === 'on' ? true : saved === 'off' ? false : nativeAndroid } catch { return nativeAndroid }
}
export function storeHandsFreePreference(storage: Pick<Storage, 'setItem'>, enabled: boolean): boolean {
  try { storage.setItem(HANDS_FREE_PREFERENCE, enabled ? 'on' : 'off'); return true } catch { return false }
}
export type CounterWakeState = { phase: string; open: boolean; enabled: boolean; hasReceipt: boolean; busy: boolean; blocked: boolean; uncertain: boolean }
/** Wake advances only a verified, completed sale; every pending state stays intact. */
export function counterWakeTransition<T extends CounterWakeState>(state: T): T {
  if (state.phase !== 'success' || !state.hasReceipt || !state.enabled || state.busy || state.blocked || state.uncertain) return state
  return { ...state, phase: 'idle', open: false }
}
